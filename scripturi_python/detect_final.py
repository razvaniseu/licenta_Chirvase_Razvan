import os                # Pentru lucrul cu fisiere si directoare
import sys               # Pentru terminarea programului in caz de eroare
import argparse          # Pentru parsarea argumentelor din linia de comanda
import glob              # Pentru a cauta fisiere dupa pattern
import time              # Pentru masurarea timpului de procesare

import cv2               # Biblioteca pentru procesarea imaginilor (OpenCV)
import numpy as np       # Biblioteca pentru calcule numerice si matrici
from ultralytics import YOLO  # Modelul YOLO pentru detectie obiecte
import serial            # Pentru comunicarea cu porturi seriale (ex. GPS, GSM)
import pynmea2           # Pentru parsarea mesajelor GPS in format NMEA

# ------------------- PARSARE ARGUMENTE -------------------
parser = argparse.ArgumentParser()
parser.add_argument('--model', help='Calea catre modelul YOLO', required=True)
parser.add_argument('--source', help='Sursa imaginilor sau video', required=True)
parser.add_argument('--thresh', help='Prag minim de incredere', default=0.8)
parser.add_argument('--resolution', help='Rezolutia WxH de afisare', default=None)
parser.add_argument('--record', help='Inregistreaza rezultatele ca demo1.avi', action='store_true')
args = parser.parse_args()

model_path = args.model
img_source = args.source
min_thresh = float(args.thresh)
user_res = args.resolution
record = args.record

# ------------------- INITIALIZARE YOLO -------------------
if not os.path.exists(model_path):
    print('ERROR: Model path is invalid sau modelul nu exista.')
    sys.exit(0)
model = YOLO(model_path, task='detect')
labels = model.names

# ------------------- INITIALIZARE GPS & GSM -------------------
# Schimba porturile daca folosesti altele!
gps_ser = serial.Serial('/dev/ttyAMA3', 9600, timeout=1)     # Port GPS (ex. SIM808)
gsm_ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=2)     # Port GSM (ex. SIM800L)

# Seteaza numarul de telefon destinatar (format international, ex: +407...)
numar_telefon = "+40712345678"

# Functie pentru trimiterea SMS-ului prin SIM800L
def trimite_sms(text):
    gsm_ser.write(b'AT\r')
    time.sleep(1)
    gsm_ser.write(b'AT+CMGF=1\r')
    time.sleep(1)
    gsm_ser.write(f'AT+CMGS="{numar_telefon}"\r'.encode())
    time.sleep(1)
    gsm_ser.write(text.encode() + b"\x1A")  # Ctrl+Z pentru terminarea mesajului
    print("SMS trimis:", text)
    time.sleep(3)

# Variabila pentru a evita trimiterea de SMS-uri duplicate (pastreaza ultima locatie trimisa)
ultima_locatie_sms = None

# ------------------- DETECTARE TIP SURSA (IMAGINE/VIDEO/CAMERA) -------------------
img_ext_list = ['.jpg','.JPG','.jpeg','.JPEG','.png','.PNG','.bmp','.BMP']
vid_ext_list = ['.avi','.mov','.mp4','.mkv','.wmv']

if os.path.isdir(img_source):
    source_type = 'folder'
elif os.path.isfile(img_source):
    _, ext = os.path.splitext(img_source)
    if ext in img_ext_list:
        source_type = 'image'
    elif ext in vid_ext_list:
        source_type = 'video'
    else:
        print(f'Extensia fisierului {ext} nu este suportata.')
        sys.exit(0)
elif 'usb' in img_source:
    source_type = 'usb'
    usb_idx = int(img_source[3:])
elif 'picamera' in img_source:
    source_type = 'picamera'
    picam_idx = int(img_source[8:])
else:
    print(f'Inputul {img_source} este invalid. Incearca din nou.')
    sys.exit(0)

# ------------------- REZOLUTIE & INREGISTRARE -------------------
resize = False
if user_res:
    resize = True
    resW, resH = int(user_res.split('x')[0]), int(user_res.split('x')[1])

if record:
    if source_type not in ['video','usb']:
        print('Inregistrarea functioneaza doar pentru surse video sau camera.')
        sys.exit(0)
    if not user_res:
        print('Trebuie sa specifici rezolutia pentru inregistrare video.')
        sys.exit(0)
    record_name = 'demo1.avi'
    record_fps = 30
    recorder = cv2.VideoWriter(record_name, cv2.VideoWriter_fourcc(*'MJPG'), record_fps, (resW,resH))

# ------------------- INCARCARE SURSA -------------------
if source_type == 'image':
    imgs_list = [img_source]
elif source_type == 'folder':
    imgs_list = []
    filelist = glob.glob(img_source + '/*')
    for file in filelist:
        _, file_ext = os.path.splitext(file)
        if file_ext in img_ext_list:
            imgs_list.append(file)
elif source_type == 'video' or source_type == 'usb':
    if source_type == 'video': cap_arg = img_source
    elif source_type == 'usb': cap_arg = usb_idx
    cap = cv2.VideoCapture(cap_arg)
    if user_res:
        ret = cap.set(3, resW)
        ret = cap.set(4, resH)
elif source_type == 'picamera':
    from picamera2 import Picamera2
    cap = Picamera2()
    cap.configure(cap.create_video_configuration(main={"format": 'RGB888', "size": (resW, resH)}))
    cap.start()

# Culori pentru bounding box-uri (maxim 10 clase diferite)
bbox_colors = [
    (164,120,87), (68,148,228), (93,97,209), (178,182,133), (88,159,106),
    (96,202,231), (159,124,168), (169,162,241), (98,118,150), (172,176,184)
]

avg_frame_rate = 0
frame_rate_buffer = []
fps_avg_len = 200
img_count = 0

# ------------------- BUCLE PRINCIPALA -------------------
while True:
    t_start = time.perf_counter()

    # Incarca un frame in functie de sursa
    if source_type == 'image' or source_type == 'folder':
        if img_count >= len(imgs_list):
            print('Toate imaginile au fost procesate. Programul se va inchide.')
            sys.exit(0)
        img_filename = imgs_list[img_count]
        frame = cv2.imread(img_filename)
        img_count += 1
    elif source_type == 'video':
        ret, frame = cap.read()
        if not ret:
            print('S-a ajuns la finalul fisierului video. Programul se va inchide.')
            break
    elif source_type == 'usb':
        ret, frame = cap.read()
        if (frame is None) or (not ret):
            print('Nu se pot citi frame-uri din camera.')
            break
    elif source_type == 'picamera':
        frame = cap.capture_array()
        if (frame is None):
            print('Nu se pot citi frame-uri din Picamera.')
            break

    # Redimensioneaza imaginea daca e cazul
    if resize:
        frame = cv2.resize(frame, (resW, resH))

    # Ruleaza YOLO pe frame
    results = model(frame, verbose=False)
    detections = results[0].boxes
    object_count = 0

    # Verifica fiecare obiect detectat
    for i in range(len(detections)):
        xyxy_tensor = detections[i].xyxy.cpu()
        xyxy = xyxy_tensor.numpy().squeeze()
        xmin, ymin, xmax, ymax = xyxy.astype(int)
        classidx = int(detections[i].cls.item())
        classname = labels[classidx]
        conf = detections[i].conf.item()

        # Daca a detectat un urs cu scor peste prag, trimite SMS cu coordonatele GPS
        if classname.lower() == "urs" and conf > min_thresh:
            # Citeste datele GPS
            while True:
                line = gps_ser.readline().decode(errors='ignore').strip()
                if line.startswith('$GPGGA') or line.startswith('$GPRMC'):
                    try:
                        msg = pynmea2.parse(line)
                        lat = msg.latitude
                        lon = msg.longitude
                        # Daca primeste coordonate valide (nu 0)
                        if lat != 0.0 and lon != 0.0:
                            locatie = f"{lat:.6f},{lon:.6f}"
                            # Trimite SMS doar daca nu ai trimis deja pentru acea locatie
                            if locatie != ultima_locatie_sms:
                                mesaj = f"Atentie! Urs detectat la coordonatele: {locatie}"
                                trimite_sms(mesaj)
                                ultima_locatie_sms = locatie
                            break
                    except pynmea2.ParseError:
                        continue

        # Deseneaza bounding box-ul daca scorul este peste prag
        if conf > min_thresh:
            color = bbox_colors[classidx % 10]
            cv2.rectangle(frame, (xmin,ymin), (xmax,ymax), color, 2)
            label = f'{classname}: {int(conf*100)}%'
            labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            label_ymin = max(ymin, labelSize[1] + 10)
            cv2.rectangle(frame, (xmin, label_ymin-labelSize[1]-10), (xmin+labelSize[0], label_ymin+baseLine-10), color, cv2.FILLED)
            cv2.putText(frame, label, (xmin, label_ymin-7), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            object_count += 1

    # Afiseaza FPS daca sursa este video/camera
    if source_type in ['video', 'usb', 'picamera']:
        cv2.putText(frame, f'FPS: {avg_frame_rate:0.2f}', (10,20), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,255,255), 2)

    # Afiseaza numarul de obiecte detectate
    cv2.putText(frame, f'Number of objects: {object_count}', (10,40), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,255,255), 2)
    cv2.imshow('YOLO detection results', frame)
    if record: recorder.write(frame)

    # Comenzi tastatura: q = iesire, s = pauza, p = salveaza poza
    if source_type in ['image', 'folder']:
        key = cv2.waitKey()
    else:
        key = cv2.waitKey(5)

    if key == ord('q') or key == ord('Q'):
        break
    elif key == ord('s') or key == ord('S'):
        cv2.waitKey()
    elif key == ord('p') or key == ord('P'):
        cv2.imwrite('capture.png', frame)

    # Calculeaza FPS-ul pentru frame-ul curent
    t_stop = time.perf_counter()
    frame_rate_calc = float(1/(t_stop - t_start))

    if len(frame_rate_buffer) >= fps_avg_len:
        frame_rate_buffer.pop(0)
    frame_rate_buffer.append(frame_rate_calc)
    avg_frame_rate = np.mean(frame_rate_buffer)

# Curata resursele la final
print(f'Average pipeline FPS: {avg_frame_rate:.2f}')
if source_type in ['video', 'usb']:
    cap.release()
elif source_type == 'picamera':
    cap.stop()
if record: recorder.release()
cv2.destroyAllWindows()
