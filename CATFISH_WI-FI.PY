
import subprocess
import os
import sqlite3
import time
import re
import select
import curses

DB_PATH = "DATABASES/catfish.db"
GPS_PATH = "/dev/ttyACM0"
REFRESH_SECONDS = 0.5


# ========================================================
# DATABASE
# ========================================================

def init_database():
    os.makedirs("DATABASES", exist_ok=True)
    connection = sqlite3.connect(DB_PATH)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS networks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ssid TEXT,
            bssid TEXT,
            channel INTEGER,
            signal INTEGER,
            security TEXT,
            latitude REAL,
            longitude REAL,
            altitude REAL,
            timestamp TEXT
        )
    """)

    connection.commit()
    return connection


def store_data(connection, networks, latitude=None,
               longitude=None, altitude=None):

    altitude_value = None

    if altitude not in ("", None):
        try:
            altitude_value = float(altitude)
        except (ValueError, TypeError):
            pass

    cursor = connection.cursor()

    for network in networks:
        if len(network) != 9:
            continue

        try:
            channel = int(network[4])
            signal = int(network[6])
        except (ValueError, TypeError):
            continue

        cursor.execute("""
            INSERT INTO networks (
                ssid, bssid, channel, signal, security,
                latitude, longitude, altitude, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            network[2],
            network[1],
            channel,
            signal,
            network[8],
            latitude,
            longitude,
            altitude_value
        ))

    connection.commit()


# ========================================================
# WI-FI SCANNING
# ========================================================

def scan_wifi():
    command = [
        "nmcli", "-t",
        "-f",
        "IN-USE,BSSID,SSID,MODE,CHAN,RATE,SIGNAL,BARS,SECURITY",
        "device", "wifi", "list"
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=15
        )
    except (OSError, subprocess.TimeoutExpired):
        return []

    if result.returncode != 0:
        return []

    networks = []

    for line in result.stdout.splitlines():
        if not line:
            continue

        fields = re.split(r'(?<!\\):', line)
        fields = [
            field.replace(r"\:", ":").replace(r"\\", "\\")
            for field in fields
        ]

        if len(fields) != 9:
            continue

        try:
            channel = int(fields[4])
            signal = int(fields[6])
        except (ValueError, TypeError):
            continue

        if not 0 <= signal <= 100 or channel < 0:
            continue

        networks.append(fields)

    return networks


# ========================================================
# GPS
# ========================================================

def empty_gps_data():
    return ("", "", "", "", "0", "0", "")


def scan_gps(timeout_seconds=0.2):
    if not os.path.exists(GPS_PATH):
        return empty_gps_data()

    deadline = time.monotonic() + timeout_seconds
    buffer = ""
    latest_data = empty_gps_data()

    try:
        fd = os.open(GPS_PATH, os.O_RDONLY | os.O_NONBLOCK)

        try:
            while time.monotonic() < deadline:
                remaining = deadline - time.monotonic()

                readable, _, _ = select.select(
                    [fd], [], [], max(0, remaining)
                )

                if not readable:
                    break

                try:
                    chunk = os.read(fd, 4096).decode(
                        "ascii", errors="ignore"
                    )
                except OSError:
                    break

                if not chunk:
                    continue

                buffer += chunk

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()

                    if not (
                        line.startswith("$GPGGA,")
                        or line.startswith("$GNGGA,")
                    ):
                        continue

                    fields = line.split(",")

                    if len(fields) < 10:
                        continue

                    latest_data = (
                        fields[2],
                        fields[3],
                        fields[4],
                        fields[5],
                        fields[6] or "0",
                        fields[7] or "0",
                        fields[9]
                    )

                    if (
                        latest_data[4] == "1"
                        and latest_data[0]
                        and latest_data[2]
                    ):
                        return latest_data

        finally:
            os.close(fd)

    except OSError:
        return empty_gps_data()

    return latest_data


def convert_coordinates(latitude, longitude):
    lat_degrees = int(latitude[:2])
    lat_minutes = float(latitude[2:])

    lon_degrees = int(longitude[:3])
    lon_minutes = float(longitude[3:])

    return (
        lat_degrees + lat_minutes / 60,
        lon_degrees + lon_minutes / 60
    )


def get_decimal_coordinates(gps_data):
    latitude, lat_dir, longitude, lon_dir, fix, _, _ = gps_data

    if fix != "1" or not latitude or not longitude:
        return None, None

    try:
        lat, lon = convert_coordinates(latitude, longitude)
    except (ValueError, IndexError):
        return None, None

    if lat_dir == "S":
        lat = -lat

    if lon_dir == "W":
        lon = -lon

    return lat, lon


# ========================================================
# NETWORK ANALYSIS
# ========================================================

def strongest_networks(networks):
    valid = []

    for network in networks:
        try:
            int(network[6])
            valid.append(network)
        except (ValueError, IndexError):
            continue

    return sorted(
        valid,
        key=lambda network: int(network[6]),
        reverse=True
    )[:5]


# ========================================================
# TERMINAL INTERFACE
# ========================================================

def safe_addstr(screen, y, x, text, max_width, attr=0):
    height, width = screen.getmaxyx()

    if y < 0 or y >= height or x < 0 or x >= width:
        return

    available = min(max_width, width - x - 1)

    if available <= 0:
        return

    try:
        screen.addnstr(y, x, str(text), available, attr)
    except curses.error:
        pass


def draw_interface(screen, networks, gps_data, saved_count,
                   latitude, longitude):

    screen.erase()
    height, width = screen.getmaxyx()

    safe_addstr(
        screen, 0, 0,
        "CATFISH WI-FI | NETWORK MONITOR".center(width - 1),
        width - 1, curses.A_BOLD
    )

    safe_addstr(
        screen, 1, 0,
        "DARK SENTINEL".center(width - 1),
        width - 1, curses.A_BOLD
    )

    fix = gps_data[4]
    satellites = gps_data[5]
    altitude = gps_data[6]

    # STATISTICS ABOVE TOP 5
    row = 3

    safe_addstr(
        screen, row, 0, "STATISTICS",
        width - 1, curses.A_BOLD
    )
    row += 1

    stats = [
        f"Saved observations: {saved_count}",
        f"GPS fix: {'VALID' if fix == '1' and latitude is not None else 'NO FIX'}",
        f"Satellites: {satellites or '0'}",
        f"Latitude: {latitude if latitude is not None else 'N/A'}",
        f"Longitude: {longitude if longitude is not None else 'N/A'}",
        f"Altitude: {altitude + ' m' if altitude else 'N/A'}"
    ]

    for stat in stats:
        safe_addstr(screen, row, 0, stat, width - 1)
        row += 1

    row += 1

    safe_addstr(
        screen, row, 0, "TOP 5 STRONGEST NETWORKS",
        width - 1, curses.A_BOLD
    )
    row += 1

    headers = (
        f"{'SSID':<24}"
        f"{'BSSID':<19}"
        f"{'CH':<5}"
        f"{'RATE':<15}"
        f"{'SIGNAL':<8}"
        f"SECURITY"
    )

    safe_addstr(
        screen, row, 0, headers,
        width - 1, curses.A_UNDERLINE
    )
    row += 1

    for network in networks:
        if row >= height - 2:
            break

        ssid = network[2] or "<hidden>"

        line = (
            f"{ssid[:23]:<24}"
            f"{network[1]:<19}"
            f"{network[4]:<5}"
            f"{network[5]:<15}"
            f"{network[6]:<8}"
            f"{network[8]}"
        )

        safe_addstr(screen, row, 0, line, width - 1)
        row += 1

    if not networks and row < height - 2:
        safe_addstr(screen, row, 0, "No networks detected.", width - 1)

    safe_addstr(
        screen, height - 1, 0,
        "Refresh: 0.5 seconds | Press Ctrl+C to exit",
        width - 1, curses.A_DIM
    )

    screen.noutrefresh()
    curses.doupdate()


# ========================================================
# MAIN LOOP
# ========================================================

def main(screen):
    curses.curs_set(0)
    screen.timeout(0)

    connection = init_database()

    try:
        while True:
            cycle_start = time.monotonic()

            networks = scan_wifi()
            gps_data = scan_gps()

            latitude, longitude = get_decimal_coordinates(gps_data)
            altitude = gps_data[6] or None

            store_data(
                connection,
                networks,
                latitude,
                longitude,
                altitude
            )

            saved_count = connection.execute(
                "SELECT COUNT(*) FROM networks"
            ).fetchone()[0]

            top_networks = strongest_networks(networks)

            draw_interface(
                screen,
                top_networks,
                gps_data,
                saved_count,
                latitude,
                longitude
            )

            elapsed = time.monotonic() - cycle_start
            time.sleep(max(0, REFRESH_SECONDS - elapsed))

    finally:
        connection.close()


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
