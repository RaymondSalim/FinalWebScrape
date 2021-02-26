import os
import subprocess

allFiles = [file for file in os.listdir(os.path.normpath('./Output/')) if '_errors.json' in file]

for f in allFiles:
    process = subprocess.Popen(f'python3.8 main.py retry -r csv -f "{f}"', shell=True)
    stdout, stderr = process.communicate()
    exit_code = process.wait()
    if exit_code == 0:
        os.remove(os.path.normpath(f'./Output/{f}'))
