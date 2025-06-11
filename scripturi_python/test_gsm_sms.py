import serial            # Biblioteca pentru comunicare pe port serial
import time              # Biblioteca pentru operatii de temporizare (delay)

# Deschide portul serial la adresa specificata, cu baudrate 9600 si timeout 2 secunde
ser = serial.Serial('/dev/ttyAMA0', baudrate=9600, timeout=2)

def send_at(command, delay=1):
    # Trimite o comanda AT si returneaza raspunsul de la modulul GSM
    ser.write((command + '\r').encode())              # Trimite comanda AT cu sfarsit de linie
    time.sleep(delay)                                 # Asteapta un timp scurt pentru ca modulul sa raspunda
    response = ser.read_all().decode(errors='ignore') # Citeste toate datele din buffer si decodeaza
    print(f">>> {command}\n{response}")               # Afiseaza comanda si raspunsul in consola
    return response

# Test comunicare - verifica daca modulul GSM raspunde la comanda AT
send_at('AT', 1)

# Pune modulul GSM in modul Text pentru SMS (nu PDU)
send_at('AT+CMGF=1', 1)

# Trimite comanda pentru a pregati trimiterea SMS-ului catre numarul specificat
send_at('AT+CMGS="+40768671235"', 2)

# Trimite textul SMS-ului urmat de CTRL+Z (hex 1A) pentru a marca sfarsitul mesajului
ser.write(b'coordonate: 44.4331071 26.0584579\x1A')
time.sleep(5)  # Asteapta cateva secunde pentru ca SMS-ul sa fie transmis

# Citeste si afiseaza raspunsul de confirmare dupa trimiterea SMS-ului
print(ser.read_all().decode(errors='ignore'))

# Inchide portul serial pentru a elibera resursa hardware
ser.close()
