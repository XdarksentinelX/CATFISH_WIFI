import subprocess
import os
import sqlite3
import time

width = os.get_terminal_size().columns
 def scan_gps():
     

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


def display_networks(all_intercepted_networks):

    print(" CATFISH WI-FI ".center(width, "="))
    print(" CREATED BY DARK SENTINEL ".center(width, "="))

    print(f"{'SSID':<25}{'BSSID':<20}{'CH':<4}{'RATE':<12}{'SIGNAL':<8}{'SECURITY'}")
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


while True:
    os.system("clear")

    all_intercepted_networks = scan_wifi()

    display_networks(all_intercepted_networks)

    time.sleep(0.5)


# ========== DEBUG ==========
# print("NETWORK".center(width, "="))
# print(fields[1].center(width))