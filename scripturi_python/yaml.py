# Functie Python care creeaza automat fisierul de configurare data.yaml pentru YOLO
# 1. Citeste fisierul "classes.txt" ca sa obtina lista de clase
# 2. Creeaza un dictionar cu caile catre foldere, numarul de clase si denumirile claselor
# 3. Scrie aceste date in format YAML in fisierul data.yaml

import yaml           # Importa biblioteca pentru lucru cu fisiere YAML
import os             # Pentru operatii cu sistemul de fisiere

def create_data_yaml(path_to_classes_txt, path_to_data_yaml):

  # Citeste classes.txt pentru a obtine numele claselor
  if not os.path.exists(path_to_classes_txt):
    print(f'Fisierul classes.txt nu a fost gasit! Creeaza un labelmap classes.txt si pune-l la {path_to_classes_txt}')
    return
  with open(path_to_classes_txt, 'r') as f:
    classes = []
    for line in f.readlines():
      if len(line.strip()) == 0: continue   # Ignora liniile goale
      classes.append(line.strip())          # Adauga fiecare clasa in lista
  number_of_classes = len(classes)

  # Creeaza dictionarul de date pentru YAML
  data = {
      'path': '/content/data',             # Calea de baza catre dataset
      'train': 'train/images',             # Subfolder pentru imagini de antrenare
      'val': 'validation/images',          # Subfolder pentru imagini de validare
      'nc': number_of_classes,             # Numarul de clase
      'names': classes                     # Lista cu numele claselor
  }

  # Scrie dictionarul de date in fisierul YAML
  with open(path_to_data_yaml, 'w') as f:
    yaml.dump(data, f, sort_keys=False)
  print(f'Fisierul de configurare a fost creat la {path_to_data_yaml}')

  return

# Defineste calea catre classes.txt si ruleaza functia
path_to_classes_txt = '/content/custom_data/classes.txt'
path_to_data_yaml = '/content/data.yaml'

create_data_yaml(path_to_classes_txt, path_to_data_yaml)

print('\nContinutul fisierului:\n')
# Afiseaza continutul fisierului data.yaml (linie specifica pentru Google Colab)
!cat /content/data.yaml
