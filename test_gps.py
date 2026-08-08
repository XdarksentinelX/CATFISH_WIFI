def scan_gps():
    gps_file = open("/dev/ttyACM0")

    while True:
        gps_line = gps_file.readline()
        if gps_line.startswith("$GPGGA") == True:
            gps_fields = gps_line.split(",")  
            latitude = gps_fields[2]
            latitude_direction = gps_fields[3]
            
            longitude = gps_fields[4]
            longitude_direction = gps_fields[5]
            
            fix = gps_fields[6]
            satellites = gps_fields[7]
            altitude = gps_fields[9]
            return latitude, latitude_direction, longitude, longitude_direction, fix, satellites, altitude

def display_gps(gps_data):
    latitude, latitude_direction, longitude, longitude_direction, fix, satellites, altitude = gps_data


    print("===== GPS =====")
    if fix == "1":
        print(f"Latitude:   {latitude} {latitude_direction}")
        print(f"Longitude:  {longitude} {longitude_direction}")
        print(f"Fix:        {fix}")
        print(f"Satellites: {satellites}")
        print(f"Altitude:   {altitude} m")
    
    else:
        print("NO SIGNAL WAITING FOR GPS FIX")
def convert_coordinates(latitude, longitude):
    #konwersja latitude
    lat_degrees = int(latitude[0:2])
    lat_minutes = float(latitude[2:])
    #konwersja longitude
    longi_degrees =int(longitude[0:3])
    longi_minutes = float(longitude[3:])
    #wzór
    lat_decimal = lat_degrees + (lat_minutes / 60)
    logi_decimal = longi_degrees + (longi_minutes / 60)
    return lat_decimal, longi_decimal
gps_data = scan_gps()

latitude, latitude_direction, longitude, longitude_direction, fix, satellites, altitude = gps_data

lat_decimal, longi_decimal = convert_coordinates(latitude, longitude)

display_gps(gps_data)