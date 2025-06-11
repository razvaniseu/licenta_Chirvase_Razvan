import os                 # Pentru operatii cu sistemul de fisiere
import sys                # Pentru terminarea programului in caz de eroare
import argparse           # Pentru a prelua argumente din linia de comanda
import glob               # Pentru a gasi fisiere dupa pattern
import time               # Pentru masurarea timpului de procesare

import cv2                # Biblioteca OpenCV pentru procesarea imaginilor
import numpy as np        # Pentru calcule numerice si procesarea de array-uri
from ultralytics import YOLO  # Importa modelul YOLO pentru detectie

# Defineste si parseaza argumentele introduse de utilizator

parser = argparse.ArgumentParser()
parser.add_argument('--model', help='Calea catre fisierul model YOLO (exemplu: "runs/detect/train/weights/best.pt")',
                    required=True)
parser.add_argument('--source', help='Sursa de imagini: poate fi fisier imagine ("test.jpg"), \
                    folder cu imagini ("test_dir"), fisier video ("testvid.mp4"), index de camera USB ("usb0"), \
                    sau index de Picamera ("picamera0")', 
                    required=True)
parser.add_argument('--thresh', help='Pragul minim de incredere pentru afisarea obiectelor detectate (exemplu: "0.4")',
                    default=0.5)
parser.add_argument('--resolution', help='Rezolutia WxH la care sa se afiseze rezultatele (exemplu: "640x480"). \
                    Daca nu se specifica, va folosi rezolutia sursei.',
                    default=None)
parser.add_argument('--record', help='Inregistreaza rezultatele din video sau camera si le salveaza ca "demo1.avi". \
                    Trebuie sa specifici si argumentul --resolution.',
                    action='store_true')

args = parser.parse_args()

# Preia argumentele introduse de utilizator
model_path = args.model
img_source = args.source
min_thresh = args.thresh
user_res = args.resolution
record = args.record

# Verifica daca fisierul modelului exista si este valid
if (not os.path.exists(model_path)):
    print('EROARE: Calea catre model este invalida sau modelul nu a fost gasit. Verifica numele fisierului modelului.')
    sys.exit(0)

# Incarca modelul YOLO in memorie si preia labelmap-ul (numele claselor)
model = YOLO(model_path, task='detect')
labels = model.names

# Identifica tipul sursei: imagine, folder, video, camera USB, picamera
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

# Preia rezolutia specificata de utilizator, daca exista
resize = False
if user_res:
    resize = True
    resW, resH = int(user_res.split('x')[0]), int(user_res.split('x')[1])

# Daca se doreste inregistrarea video, verifica daca sursa e valida si seteaza parametrii
if record:
    if source_type not in ['video','usb']:
        print('Inregistrarea functioneaza doar pentru surse video sau camera. Incearca din nou.')
        sys.exit(0)
    if not user_res:
        print('Trebuie sa specifici rezolutia pentru inregistrare video.')
        sys.exit(0)
    
    # Seteaza parametrii pentru inregistrare
    record_name = 'demo1.avi'
    record_fps = 30
    recorder = cv2.VideoWriter(record_name, cv2.VideoWriter_fourcc(*'MJPG'), record_fps, (resW,resH))

# Incarca sau initializeaza sursa de imagini
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

    # Seteaza rezolutia camerei sau a fisierului video, daca este specificata de utilizator
    if user_res:
        ret = cap.set(3, resW)
        ret = cap.set(4, resH)

elif source_type == 'picamera':
    from picamera2 import Picamera2
    cap = Picamera2()
    cap.configure(cap.create_video_configuration(main={"format": 'RGB888', "size": (resW, resH)}))
    cap.start()

# Stabileste culorile pentru bounding box-uri (paleta Tableu 10)
bbox_colors = [(164,120,87), (68,148,228), (93,97,209), (178,182,133), (88,159,106), 
              (96,202,231), (159,124,168), (169,162,241), (98,118,150), (172,176,184)]

# Initializeaza variabile de control si status
avg_frame_rate = 0
frame_rate_buffer = []
fps_avg_len = 200
img_count = 0

# Incepe bucla principala de inferenta
while True:

    t_start = time.perf_counter()  # Porneste cronometru pentru calcularea FPS

    # Incarca un frame din sursa
    if source_type == 'image' or source_type == 'folder': # Daca sursa e imagine sau folder, incarca imaginea dupa nume
        if img_count >= len(imgs_list):
            print('Toate imaginile au fost procesate. Programul se va inchide.')
            sys.exit(0)
        img_filename = imgs_list[img_count]
        frame = cv2.imread(img_filename)
        img_count = img_count + 1
    
    elif source_type == 'video': # Daca sursa este video, incarca urmatorul frame din fisier
        ret, frame = cap.read()
        if not ret:
            print('S-a ajuns la finalul fisierului video. Programul se va inchide.')
            break
    
    elif source_type == 'usb': # Daca sursa e camera USB, citeste frame din camera
        ret, frame = cap.read()
        if (frame is None) or (not ret):
            print('Nu se pot citi frame-uri din camera. Camera nu este conectata sau nu functioneaza. Programul se va inchide.')
            break

    elif source_type == 'picamera': # Daca sursa e Picamera, citeste frame folosind Picamera
        frame = cap.capture_array()
        if (frame is None):
            print('Nu se pot citi frame-uri din Picamera. Camera nu este conectata sau nu functioneaza. Programul se va inchide.')
            break

    # Redimensioneaza frame-ul la rezolutia dorita
    if resize == True:
        frame = cv2.resize(frame,(resW,resH))

    # Ruleaza inferenta YOLO pe frame
    results = model(frame, verbose=False)

    # Extrage rezultatele detectiei
    detections = results[0].boxes

    # Initializeaza o variabila pentru a numara obiectele detectate
    object_count = 0

    # Parcurge fiecare detectie si extrage coordonatele, increderea si clasa
    for i in range(len(detections)):

        # Extrage coordonatele bounding box-ului
        # Ultralytics intoarce rezultatele in format Tensor, trebuie convertit in array normal
        xyxy_tensor = detections[i].xyxy.cpu() # Bounding box-uri in format Tensor pe CPU
        xyxy = xyxy_tensor.numpy().squeeze()   # Converteste Tensorul in array Numpy
        xmin, ymin, xmax, ymax = xyxy.astype(int) # Extrage coordonatele individuale si le converteste in intregi

        # Extrage ID-ul clasei si numele clasei
        classidx = int(detections[i].cls.item())
        classname = labels[classidx]

        # Extrage increderea pentru bounding box
        conf = detections[i].conf.item()

        # Deseneaza bounding box-ul doar daca scorul este peste pragul minim
        if conf > 0.5:

            color = bbox_colors[classidx % 10]
            cv2.rectangle(frame, (xmin,ymin), (xmax,ymax), color, 2)

            label = f'{classname}: {int(conf*100)}%'
            labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1) # Calculeaza dimensiunea fontului
            label_ymin = max(ymin, labelSize[1] + 10) # Evita ca labelul sa fie prea aproape de marginea de sus
            cv2.rectangle(frame, (xmin, label_ymin-labelSize[1]-10), (xmin+labelSize[0], label_ymin+baseLine-10), color, cv2.FILLED) # Deseneaza o casuta pentru textul labelului
            cv2.putText(frame, label, (xmin, label_ymin-7), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1) # Scrie textul labelului

            # Exemplu simplu: incrementeaza numarul de obiecte detectate
            object_count = object_count + 1

    # Calculeaza si afiseaza FPS-ul (daca sursa este video sau camera)
    if source_type == 'video' or source_type == 'usb' or source_type == 'picamera':
        cv2.putText(frame, f'FPS: {avg_frame_rate:0.2f}', (10,20), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,255,255), 2) # Afiseaza framerate-ul
    
    # Afiseaza rezultatele detectiei
    cv2.putText(frame, f'Number of objects: {object_count}', (10,40), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,255,255), 2) # Afiseaza numarul total de obiecte detectate
    cv2.imshow('YOLO detection results',frame) # Afiseaza imaginea in fereastra
    if record: recorder.write(frame)

    # Daca se proceseaza imagini individuale, asteapta apasarea unei taste pentru a trece la urmatoarea imagine. Altfel, asteapta 5ms intre frame-uri.
    if source_type == 'image' or source_type == 'folder':
        key = cv2.waitKey()
    elif source_type == 'video' or source_type == 'usb' or source_type == 'picamera':
        key = cv2.waitKey(5)
    
    if key == ord('q') or key == ord('Q'): # Apasa 'q' pentru a iesi din program
        break
    elif key == ord('s') or key == ord('S'): # Apasa 's' pentru a pune pauza la inferenta
        cv2.waitKey()
    elif key == ord('p') or key == ord('P'): # Apasa 'p' pentru a salva imaginea curenta cu rezultate
        cv2.imwrite('capture.png',frame)
    
    # Calculeaza FPS-ul pentru acest frame
    t_stop = time.perf_counter()
    frame_rate_calc = float(1/(t_stop - t_start))

    # Adauga FPS-ul curent in bufferul de frame rate (pentru a calcula media pe mai multe frame-uri)
    if len(frame_rate_buffer) >= fps_avg_len:
        temp = frame_rate_buffer.pop(0)
        frame_rate_buffer.append(frame_rate_calc)
    else:
        frame_rate_buffer.append(frame_rate_calc)

    # Calculeaza media FPS pentru ultimele frame-uri
    avg_frame_rate = np.mean(frame_rate_buffer)

# Curata resursele la final
print(f'Average pipeline FPS: {avg_frame_rate:.2f}')
if source_type == 'video' or source_type == 'usb':
    cap.release()
elif source_type == 'picamera':
    cap.stop()
if record: recorder.release()
cv2.destroyAllWindows()
