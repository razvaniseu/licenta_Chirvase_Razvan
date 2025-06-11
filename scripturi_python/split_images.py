# Imparte un set de imagini in doua foldere: train si validation

from pathlib import Path     # Importa biblioteca pentru lucrul cu cai de fisiere
import random               # Pentru selectie aleatoare a fisierelor
import os                   # Pentru operatii cu sistemul de fisiere
import sys                  # Pentru iesirea fortata din program
import shutil               # Pentru copierea fisierelor
import argparse             # Pentru parsarea argumentelor din linia de comanda

# Defineste si parseaza argumentele introduse de utilizator

parser = argparse.ArgumentParser()
parser.add_argument('--datapath', help='Cale catre folderul cu date care contine fisierele de imagini si adnotari',
                    required=True)
parser.add_argument('--train_pct', help='Procentul de imagini care merg in folderul train; \
                    restul merg in folderul de validare (exemplu: ".8")',
                    default=.8)

args = parser.parse_args()

data_path = args.datapath
train_percent = float(args.train_pct)

# Verifica daca datele introduse sunt valide
if not os.path.isdir(data_path):
   print('Directorul specificat la --datapath nu a fost gasit. Verifica daca calea este corecta si incearca din nou.')
   sys.exit(0)
if train_percent < .01 or train_percent > 0.99:
   print('Valoare invalida pentru train_pct. Introdu un numar intre .01 si .99.')
   sys.exit(0)
val_percent = 1 - train_percent

# Defineste calea catre datasetul initial 
input_image_path = os.path.join(data_path,'images')
input_label_path = os.path.join(data_path,'labels')

# Defineste caile catre folderele de imagini si adnotari pentru train si validation
cwd = os.getcwd()
train_img_path = os.path.join(cwd,'data/train/images')
train_txt_path = os.path.join(cwd,'data/train/labels')
val_img_path = os.path.join(cwd,'data/validation/images')
val_txt_path = os.path.join(cwd,'data/validation/labels')

# Creeaza folderele daca nu exista deja
for dir_path in [train_img_path, train_txt_path, val_img_path, val_txt_path]:
   if not os.path.exists(dir_path):
      os.makedirs(dir_path)
      print(f'Folder creat la {dir_path}.')

# Obtine lista tuturor imaginilor si fisierelor de adnotari
img_file_list = [path for path in Path(input_image_path).rglob('*')]
txt_file_list = [path for path in Path(input_label_path).rglob('*')]

print(f'Numar de fisiere imagine: {len(img_file_list)}')
print(f'Numar de fisiere adnotare: {len(txt_file_list)}')

# Determina numarul de fisiere care vor merge in fiecare folder
file_num = len(img_file_list)
train_num = int(file_num*train_percent)
val_num = file_num - train_num
print('Imagini mutate in train: %d' % train_num)
print('Imagini mutate in validation: %d' % val_num)

# Selecteaza fisierele aleator si le copiaza in folderele train sau validation
for i, set_num in enumerate([train_num, val_num]):
  for ii in range(set_num):
    img_path = random.choice(img_file_list)
    img_fn = img_path.name
    base_fn = img_path.stem
    txt_fn = base_fn + '.txt'
    txt_path = os.path.join(input_label_path,txt_fn)

    if i == 0: # Copiaza primul set de fisiere in folderele train
      new_img_path, new_txt_path = train_img_path, train_txt_path
    elif i == 1: # Copiaza al doilea set de fisiere in folderele de validare
      new_img_path, new_txt_path = val_img_path, val_txt_path

    shutil.copy(img_path, os.path.join(new_img_path,img_fn))
    # Daca vrem sa mutam in loc sa copiem, decomentam linia de mai jos
    #os.rename(img_path, os.path.join(new_img_path,img_fn))
    if os.path.exists(txt_path): # Daca fisierul txt nu exista, inseamna ca e imagine background, deci nu copia fisier txt
      shutil.copy(txt_path,os.path.join(new_txt_path,txt_fn))
      # Daca vrem sa mutam fisierul txt in loc sa-l copiem, decomentam linia de mai jos
      #os.rename(txt_path,os.path.join(new_txt_path,txt_fn))

    img_file_list.remove(img_path)  # Scoate imaginea din lista pentru a nu o selecta din nou
