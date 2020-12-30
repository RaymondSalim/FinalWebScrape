import os
import subprocess

allFiles = [file for file in os.listdir(os.path.normpath('./Output/')) if '_errors.json' in file]

for f in allFiles:
    subprocess.call(f'python main.py retry -r csv -f "{f}"', shell=True)
    os.remove(os.path.normpath(f'./Output/{f}'))
