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
driver_success = False
pip_success = False
os_is_windows = False


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


def install_requirements():
    global pip_success
    try:
        import selenium
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", 'selenium'])
        except Exception:
            pip_success = False
        else:
            pip_success = True
    else:
        pip_success = True


def check_status():
    global driver_success, pip_success, operating_system, err
    if driver_success and pip_success:
        print("*********************")
        print("* Setup Successful! *")
        print("*********************")

        if str(operating_system) != 'Windows':
            print("\nPlease mark chromedriver as executable with the following:\n\n\n    sudo chmod +x " + new_path + "chromedriver\n\n\n")

        sys.exit(0)

    else:
        if not driver_success:
            if str(operating_system) == 'Windows':
                print(f"Failed to get chrome version, please ensure you have google chrome installed and download chromedriver "
                      f"from\nhttps://chromedriver.storage.googleapis.com/\nPlace it inside Files folder with the name of "
                      f"chromedriver.exe")
                webbrowser.open('https://chromedriver.storage.googleapis.com/')
                sys.exit(-1)
            else:
                if "command not found".casefold() in str(err).casefold() or "No such file".casefold() in str(err).casefold():
                    print("Google chrome not found, please ensure you have google chrome installed")
                else:
                    print(err)
                sys.exit(-1)

        elif not pip_success:
            print("Failed to install selenium pip library, please install manually by typing\n\n\n    pip install selenium")




if str(operating_system) == 'Windows':
    os_is_windows = True
    proc1 = subprocess.run(['wmic', 'datafile', 'where', 'name="C:\\\\Program Files (x86)\\\\Google\\\\Chrome\\\\Application\\\\chrome.exe"', 'get', 'Version', '/value'],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    version = proc1.stdout.decode('utf-8') + proc1.stderr.decode('utf-8')

    if "No" in version:
        proc1 = subprocess.run(['wmic', 'datafile', 'where', 'name="C:\\\\Program Files\\\\Google\\\\Chrome\\\\Application\\\\chrome.exe"', 'get', 'Version', '/value'],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        version = proc1.stdout.decode('utf-8') + proc1.stderr.decode('utf-8')

    pattern = "[0-9.]+"
    version = (re.findall(pattern, version))[0]
    
    if "No" not in version and len(version) != 0:
        dl_url = get_url(version) + 'chromedriver_win32.zip'

        subprocess.run(['curl', dl_url, '--output', 'cd.zip'])

        new_path = driver_path + '\\Files\\'

        if not os.path.exists(os.path.normpath(new_path)):
            os.mkdir(os.path.normpath(new_path))
            try:
                os.mkdir(os.path.normpath(new_path.replace('Files', 'Output')))
            except FileExistsError:
                pass

        extract_zip()

        shutil.move(os.path.normpath(driver_path + '/chromedriver.exe'), os.path.normpath(new_path + 'chromedriver.exe'))
        driver_success = True

    install_requirements()

    check_status()


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
            try:
                os.mkdir(os.path.normpath(new_path.replace('Files', 'Output')))
            except FileExistsError:
                pass

        extract_zip()

        shutil.move(os.path.normpath(driver_path + '/chromedriver'), os.path.normpath(new_path + 'chromedriver'))

        # subprocess.run(['sudo', 'chmod', '+x', new_path + 'chromedriver'])
        driver_success = True

    except Exception as err:
        pass
    finally:
        install_requirements()

        check_status()







