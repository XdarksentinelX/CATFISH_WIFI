import subprocess
import os
import sqlite3
import time


width = os.get_terminal_size().columns

##########################################################
# FUNKCJE
##########################################################


def init_database():
    connection = sqlite3.connect("DATABASES/catfish.db")
    cursor = connection.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS networks (
    id,
    ssid,
    bssid,
    channel,
    signal,
    security,
    latitude,
    longitude,
    altitude,
    timestamp
)""")

    connection.commit()
    return connection


def store_data(
    connection_database,
    all_intercepted_networks,
    lat_decimal,
    longi_decimal
):
    for network in all_intercepted_networks:

        ssid = network[1]
        bssid = network[0]
        channel = network[3]
        signal = network[6]
        security = network[8:]

        cursor = connection_database.cursor()

        cursor.execute(
            """INSERT INTO networks
            (ssid, bssid, channel, signal, security)
            VALUES (?, ?, ?, ?, ?)""",
            (
                ssid,
                bssid,
                channel,
                signal,
                ' '.join(security)
            )
        )


def scan_wifi():

    results_wifi = subprocess.run(
        ["nmcli", "device", "wifi", "list"],
        capture_output=True,
        text=True
    )

    wifi_list = results_wifi.stdout.splitlines()
    all_intercepted_networks = []

    for line in wifi_list[1:]:

        fields = line.split()
        all_intercepted_networks.append(fields)

    return all_intercepted_networks


def scan_gps():

    gps_file = open("/dev/ttyACM0")

    while True:

        gps_line = gps_file.readline()

        if gps_line.startswith("$GPGGA"):

            gps_fields = gps_line.split(",")

            latitude = gps_fields[2]
            latitude_direction = gps_fields[3]

            longitude = gps_fields[4]
            longitude_direction = gps_fields[5]

            fix = gps_fields[6]
            satellites = gps_fields[7]
            altitude = gps_fields[9]

            return (
                latitude,
                latitude_direction,
                longitude,
                longitude_direction,
                fix,
                satellites,
                altitude
            )


def convert_coordinates(latitude, longitude):

    # Konwersja latitude
    lat_degrees = int(latitude[0:2])
    lat_minutes = float(latitude[2:])

    # Konwersja longitude
    longi_degrees = int(longitude[0:3])
    longi_minutes = float(longitude[3:])

    # Wzór
    lat_decimal = lat_degrees + (lat_minutes / 60)
    longi_decimal = longi_degrees + (longi_minutes / 60)

    return lat_decimal, longi_decimal


def display_gps(
    gps_data,
    lat_decimal=None,
    longi_decimal=None
):

    (
        latitude,
        latitude_direction,
        longitude,
        longitude_direction,
        fix,
        satellites,
        altitude
    ) = gps_data

    print("===== GPS =====")

    if fix == "1":

        print(
            f"Latitude:   {lat_decimal:.6f} "
            f"{latitude_direction}"
        )

        print(
            f"Longitude:  {longi_decimal:.6f} "
            f"{longitude_direction}"
        )

        print(f"Fix:        {fix}")
        print(f"Satellites: {satellites}")
        print(f"Altitude:   {altitude} m")

    else:

        print("NO SIGNAL WAITING FOR GPS FIX")


##########################################################
# TOP 5 NAJSILNIEJSZYCH SIECI
##########################################################


def strongest_networks(all_intercepted_networks):

    strongest = sorted(
        all_intercepted_networks,
        key=lambda network: int(network[6]),
        reverse=True
    )

    return strongest[:5]


##########################################################
# STATYSTYKI
##########################################################


def display_statistics(connection_database, gps_data):

    cursor = connection_database.cursor()

    cursor.execute("SELECT COUNT(*) FROM networks")

    captured = cursor.fetchone()[0]

    fix = gps_data[4]
    satellites = gps_data[5]
    altitude = gps_data[6]

    print()
    print("===== STATISTICS =====")
    print(f"Captured records: {captured}")
    print(f"GPS FIX:          {fix}")
    print(f"Satellites:       {satellites}")
    print(f"Altitude:         {altitude} m")


##########################################################
# WYŚWIETLANIE SIECI
##########################################################


def display_networks(all_intercepted_networks):

    print()
    print(" CATFISH WI-FI ".center(width, "="))
    print(" CREATED BY DARK SENTINEL ".center(width, "="))

    print(
        f"{'SSID':<25}"
        f"{'BSSID':<20}"
        f"{'CH':<4}"
        f"{'RATE':<12}"
        f"{'SIGNAL':<8}"
        f"{'SECURITY'}"
    )

    print("-".center(width, "-"))

    for every_network in all_intercepted_networks:

        if every_network[0] == "*":
            continue

        print(
            f"{every_network[1]:<25}"
            f"{every_network[0]:<20}"
            f"{every_network[3]:<4}"
            f"{every_network[4] + ' ' + every_network[5]:<12}"
            f"{every_network[6]:<8}"
            f"{' '.join(every_network[8:])}"
        )


##########################################################
# BAZA DANYCH
##########################################################


connection_database = init_database()


##########################################################
# PĘTLA
##########################################################


while True:

    os.system("clear")

    # ==========================================
    # SKAN WI-FI
    # ==========================================

    all_intercepted_networks = scan_wifi()

    # ==========================================
    # SKAN GPS
    # ==========================================

    gps_data = scan_gps()

    (
        latitude,
        latitude_direction,
        longitude,
        longitude_direction,
        fix,
        satellites,
        altitude
    ) = gps_data

    # ==========================================
    # GPS FIX
    # ==========================================

    if fix == "1":

        lat_decimal, longi_decimal = convert_coordinates(
            latitude,
            longitude
        )

        display_gps(
            gps_data,
            lat_decimal,
            longi_decimal
        )

        # Zapis danych do SQLite
        store_data(
            connection_database,
            all_intercepted_networks,
            lat_decimal,
            longi_decimal
        )

    else:

        display_gps(gps_data)

    # ==========================================
    # TOP 5 NAJSILNIEJSZYCH SIECI
    # ==========================================

    strongest = strongest_networks(
        all_intercepted_networks
    )

    # ==========================================
    # WYŚWIETLENIE TOP 5
    # ==========================================

    display_networks(strongest)

    # ==========================================
    # STATYSTYKI
    # ==========================================

    display_statistics(
        connection_database,
        gps_data
    )

    time.sleep(0.5)