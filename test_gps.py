def scan_gps():
    gps_file = open("/dev/ttyACM0")

    while True:
        gps_line = gps_file.readline()
        if gps_line.startswith("$GPGGA") == True:
            gps_fields = gps_line.split(",")  
            print(gps_fields)
scan_gps()