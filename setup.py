import subprocess
import platform
import os
import sys
import zipfile
import shutil
import webbrowser
import re

operating_system = platform.system()
driver_path = str(os.path.dirname(os.path.realpath(__file__)))


def get_url(version):
    version = version[0:2:]
    if "85" == version:
        return 'https://chromedriver.storage.googleapis.com/85.0.4183.87/'
    elif "86" == version:
        return 'https://chromedriver.storage.googleapis.com/86.0.4240.22/'
    elif "86" == version:
        return 'https://chromedriver.storage.googleapis.com/87.0.4280.20/'


def extract_zip():
    with zipfile.ZipFile('cd.zip', 'r') as zf:
        zf.extractall()

    if os.path.exists('cd.zip'):
        os.remove('cd.zip')

# TODO! Fix Windows
if str(operating_system) == 'Windows':
    proc1 = subprocess.run(['wmic', 'datafile', 'where', 'name="C:\\\\Program Files (x86)\\\\Google\\\\Chrome\\\\Application\\\\chrome.exe"', 'get', 'Version', '/value'],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    version = proc1.stdout.decode('utf-8') + proc1.stderr.decode('utf-8')

    if "No" in version:
        proc1 = subprocess.run(['wmic', 'datafile', 'where', 'name="C:\\\\Program Files\\\\Google\\\\Chrome\\\\Application\\\\chrome.exe"', 'get', 'Version', '/value'],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        version = proc1.stdout.decode('utf-8') + proc1.stderr.decode('utf-8')

    pattern = "[0-9.]+"
    version = (re.findall(pattern, version))[0]
    
    if "No" in version or len(version) == 0:
        print(f"Failed to get chrome version, please ensure you have google chrome installed and download chromedriver "
          f"from\nhttps://chromedriver.storage.googleapis.com/\nPlace it inside Files folder with the name of "
          f"chromedriver.exe")
        webbrowser.open('https://chromedriver.storage.googleapis.com/')
        sys.exit(-1)
        
    
    dl_url = get_url(version) + 'chromedriver_win32.zip'

    subprocess.run(['curl', dl_url, '--output', 'cd.zip'])

    new_path = driver_path + '\\Files\\'

    if not os.path.exists(os.path.normpath(new_path)):
        os.mkdir(os.path.normpath(new_path))
        os.mkdir(os.path.normpath(new_path.replace('Files', 'Output')))

    extract_zip()

    shutil.move(os.path.normpath(driver_path + '/chromedriver.exe'), os.path.normpath(new_path + 'chromedriver.exe'))
    print("\n\n\nSuccessful")


else:
    try:
        proc1 = subprocess.run(['google-chrome-stable', '--version'], stdout=subprocess.PIPE)
        if "command not found" in proc1.stdout.decode('utf-8'):
            print("Google chrome not found, please ensure you have google chrome installed")
            sys.exit(-1)

        proc2 = subprocess.run(["grep", "-Eo", "[0-9.]+"], input=proc1.stdout, stdout=subprocess.PIPE)
        version = proc2.stdout.decode('utf-8')
        dl_url = get_url(version) + 'chromedriver_linux64.zip'

        subprocess.run(['curl', dl_url, '--output', 'cd.zip'])

        new_path = driver_path + '/Files/'

        if not os.path.exists(os.path.normpath(new_path)):
            os.mkdir(os.path.normpath(new_path))
            os.mkdir(os.path.normpath(new_path.replace('Files', 'Output')))

        extract_zip()


        shutil.move(os.path.normpath(driver_path + '/chromedriver'), os.path.normpath(new_path + 'chromedriver'))

        print("Changing permission to executable requires sudo:")
        # subprocess.run(['sudo', 'chmod', '+x', new_path + 'chromedriver'])
        print("Please mark chromedriver as executable with the following:\n    sudo chmod +x " + new_path + "chromedriver")

        print("\n\n\nSuccessful")

    except Exception as err:
        print(err)
        print("Failed")
        sys.exit(-1)





