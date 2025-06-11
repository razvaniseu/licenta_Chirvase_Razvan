import serial             # Biblioteca pentru comunicare pe port serial
import pynmea2            # Biblioteca pentru parsarea mesajelor GPS in format NMEA

# Deschide portul serial la adresa specificata, viteza 9600 bps, timeout 1 secunda
ser = serial.Serial('/dev/ttyAMA3', 9600, timeout=1)

while True:   # Bucla infinita pentru citirea continua a datelor de la GPS
    line = ser.readline().decode(errors='ignore').strip()   # Citeste o linie de la portul serial si decodeaza
    if line.startswith('$GPGGA') or line.startswith('$GPRMC'):  # Daca linia contine date de localizare
        try:
            msg = pynmea2.parse(line)   # Parseeaza linia NMEA cu pynmea2
            print(f"Latitudine: {msg.latitude}, Longitudine: {msg.longitude}")  # Afiseaza coordonatele
        except pynmea2.ParseError:
            continue  # Daca mesajul nu poate fi parsat, trece mai departe
