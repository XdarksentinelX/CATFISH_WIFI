# CATFISH WI-FI

**A Python-based Wi-Fi network scanner with SQLite logging and optional GPS geolocation.**

CATFISH WI-FI is a learning project focused on wireless network discovery, structured data collection, and basic network monitoring. It uses NetworkManager's `nmcli` utility to retrieve nearby Wi-Fi network information and stores observations in a local SQLite database.

## Features

- Wi-Fi network discovery using `nmcli`
- SSID and BSSID collection
- Channel, advertised rate, signal strength, and security information
- Top 5 strongest networks displayed in the terminal
- SQLite storage of network observations
- Optional GPS coordinates and altitude
- Terminal interface powered by Python `curses`
- Periodic refresh and graceful shutdown with `Ctrl+C`

## Technologies

- Python 3
- NetworkManager (`nmcli`)
- SQLite
- `curses`
- GPS data in NMEA GGA format

## Requirements

- Linux
- Python 3
- NetworkManager and `nmcli`
- A Wi-Fi adapter supported by NetworkManager
- Optional GPS receiver providing NMEA data through `/dev/ttyACM0`

## Installation

Clone the repository:

```bash
git clone https://github.com/XdarksentinelX/CATFISH_WIFI.git
cd CATFISH_WIFI
```

Verify that NetworkManager and `nmcli` are available:

```bash
nmcli --version
```

Check the Python syntax:

```bash
python3 -m py_compile CATFISH_WI-FI.PY
```

Run the application:

```bash
python3 CATFISH_WI-FI.PY
```

## Database

The application stores observations in `DATABASES/catfish.db`.

Each observation can contain:

- SSID
- BSSID
- Channel
- Signal strength
- Security information
- Latitude and longitude, when GPS data is available
- Altitude, when available
- Timestamp

When a valid GPS fix is unavailable, Wi-Fi observations can still be stored without location data.

The database is excluded from Git to avoid committing local scan data.

## Limitations

- Scan results depend on the wireless adapter and NetworkManager.
- GPS location requires a compatible receiver and a valid GPS fix.
- Advertised Wi-Fi rates are not measurements of actual throughput.
- Repeated scans create repeated observations; the record count is not the number of unique networks.
- The refresh interval does not guarantee a scan every 0.5 seconds because scanning takes time.

## Project Purpose

This project is part of my practical learning in Python, networking, wireless network discovery, and data handling. It is intended for educational use and authorized environments.

## Author

**Dark Sentinel**
