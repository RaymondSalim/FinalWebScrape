import subprocess
import platform
import os
import zipfile
import shutil

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


if str(operating_system) == 'Windows':
    proc1 = subprocess.run(['start', 'chrome', '--version'])
    new_path = driver_path + '\\Files\\'

    if not os.path.exists(os.path.normpath(new_path)):
        os.mkdir(os.path.normpath(new_path))

    print(f"Failed to get chrome version, please download chromedriver "
          f"from\nhttps://chromedriver.storage.googleapis.com/\nPlace it inside Files folder with the name of "
          f"chromedriver.exe")
else:
    try:
        proc1 = subprocess.run(['google-chrome-stable', '--version'], stdout=subprocess.PIPE)
        proc2 = subprocess.run(["grep", "-Eo", "[0-9.]+"], input=proc1.stdout, stdout=subprocess.PIPE)
        version = proc2.stdout.decode('utf-8')
        dl_url = get_url(version) + 'chromedriver_linux64.zip'

        subprocess.run(['curl', dl_url, '--output', 'cd.zip'])

        new_path = driver_path + '/Files/'

        if not os.path.exists(os.path.normpath(new_path)):
            os.mkdir(os.path.normpath(new_path))

        extract_zip()

        shutil.move(os.path.normpath(driver_path + '/chromedriver'), os.path.normpath(new_path + 'chromedriver'))

        print("Changing permission to executable requires sudo:")
        subprocess.run(['sudo', 'chmod', '+x', new_path + 'chromedriver'])

        print("success")

    except Exception as err:
        print(err)
        print("Failed")
        exit(-1)





