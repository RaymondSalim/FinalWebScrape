import os
from pathlib import Path
import subprocess

allFiles = [file for file in os.listdir(os.path.normpath('./Output/')) if '_continue.' in file]

for f in allFiles:
    file2 = f.replace('_continue.', '.')

    if not Path(f"Output/{file2}").is_file():
        continue

    process = subprocess.Popen(f'python3.8 main.py merge -f1 "{f}" -f2 "{file2}"', shell=True)
    stdout, stderr = process.communicate()
    exit_code = process.wait()
    if exit_code == 0:
        os.remove(os.path.normpath(f'./Output/{f}'))
        os.remove(os.path.normpath(f'./Output/{file2}'))
