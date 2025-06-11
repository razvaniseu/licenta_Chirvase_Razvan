import serial             # Biblioteca pentru comunicare seriala cu GPS si GSM
import pynmea2            # Biblioteca pentru parsarea mesajelor NMEA de la GPS
import time               # Biblioteca pentru delay-uri (asteptare)

# Portul serial pentru GPS (modifica daca nu este acesta)
gps_ser = serial.Serial('/dev/ttyAMA3', 9600, timeout=1)

# Portul serial pentru GSM (modifica daca nu este acesta)
gsm_ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=2)

# Numarul de telefon la care va fi trimis SMS-ul (modifica dupa nevoie)
numar_telefon = "+40732607209"  # Inlocuieste cu numarul tau

def trimite_sms(text):
    # Trimite un SMS cu textul primit ca argument
    gsm_ser.write(b'AT\r')                           # Test comunicare cu modulul GSM
    time.sleep(1)
    gsm_ser.write(b'AT+CMGF=1\r')                    # Pune modulul in modul Text
    time.sleep(1)
    gsm_ser.write(f'AT+CMGS="{numar_telefon}"\r'.encode())  # Seteaza destinatarul
    time.sleep(1)
    gsm_ser.write(text.encode() + b"\x1A")           # Trimite textul si Ctrl+Z pentru terminare SMS
    print("SMS trimis:", text)
    time.sleep(3)                                    # Asteapta pentru procesare

ultimele_coord = None    # Retine ultimele coordonate pentru a evita trimiterea de SMS-uri duplicate

while True:
    line = gps_ser.readline().decode(errors='ignore').strip()   # Citeste o linie de la GPS si decodeaza
    if line.startswith('$GPGGA') or line.startswith('$GPRMC'):  # Daca este linie cu informatii de pozitie
        try:
            msg = pynmea2.parse(line)             # Parseeaza mesajul NMEA
            lat = msg.latitude                    # Extrage latitudinea
            lon = msg.longitude                   # Extrage longitudinea
            # Daca lat si lon sunt valide (nu sunt 0)
            if lat != 0.0 and lon != 0.0:
                coord = f"{lat:.6f},{lon:.6f}"    # Formateaza coordonatele ca text
                print(f"Coordonate curente: {coord}")
                # Trimite SMS doar daca s-au schimbat coordonatele fata de ultima transmisa
                if coord != ultimele_coord:
                    mesaj = f"Locatia curenta este: {coord}"
                    trimite_sms(mesaj)            # Trimite SMS cu locatia noua
                    ultimele_coord = coord
                    # Daca vrei sa trimiti un singur SMS, poti decomenta break-ul de mai jos
                    # break
                time.sleep(10)  # Asteapta 10 secunde inainte de urmatorul SMS
        except pynmea2.ParseError:
            continue           # Daca nu poate parsa linia, trece peste
