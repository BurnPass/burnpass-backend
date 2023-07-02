import os 
from os import listdir

for file_name in listdir():
    if file_name.endswith('.pem') or file_name.endswith('.key'):
        os.remove(file_name)
