from sys import platform
import sys
import os
import io
import re
import json
import urllib.request
import subprocess

try:
    import winreg
except ImportError:
    pass

try:
    import psutil
except ImportError:
    print("Installing missing psutil module")
    os.system("python -m pip install psutil")
    import psutil

# Defines

resManifest = "https://github.com/colin969/SimpleDiscordCrypt/raw/master/app_files/manifest.json"
resBackground = "https://raw.githubusercontent.com/colin969/SimpleDiscordCrypt/master/app_files/background.html"
resLoader = "https://github.com/colin969/SimpleDiscordCrypt/raw/master/app_files/SimpleDiscordCryptLoader.js"

linuxDiscordProcName = "Discord"
linuxDiscordPath = "/opt/discord"
linuxDiscordDataPath = "/.config/discord"
linuxPluginPath = "/.config/SimpleDiscordCrypt"

win32DiscordProcName = r"Discord.exe"
win32DiscordPath = r"\Discord"
win32PluginPath = r"\SimpleDiscordCrypt"
win32ExtensionPath = '../../SimpleDiscordCrypt'
win32RegistryKey = r"Software\Microsoft\Windows\CurrentVersion\Run"
win32RegistryValue = r"\Microsoft\Windows\Start Menu\Programs\Discord Inc\Discord.lnk"

# Util Funcs

# Kill any running processes with given name
def stop_process(name):
    print("Stopping " + name)
    for proc in psutil.process_iter():
        if(proc.name() == name):
            proc.kill()

# Make sure path exists and exit if failure
def check_path(name, path):
    if(os.path.exists(path)):
        print(name + " located at - " + path)
    else:
        print(name + " not found")
        sys.exit(0)

# Create path if empty
def create_path(name, path):
    if(os.path.exists(path)):
        print(name + " located at - " + path);
    else:
        os.mkdir(path);
        print(name + " created at - " + path)


def root_electron(path):
    print("Rooting " + path)

    # Read file into mem
    file = io.open(path, 'r', encoding='iso-8859-1')
    lines = file.read()
    file.close()

    # Find Chrome context injection, append 'context.chrome={require};'
    regex = re.compile(r"^(?:\s*\/\/.*\r?\n\s*|\s*)?(exports\.injectTo)\s*?(=)\s*?((?:function)\s*\(.*context.*\)|\(.*context.*\)\s*=>)\s*({)(?=\r?\n)",
                        re.MULTILINE)

    for x in regex.finditer(lines):
        # Remove 'comment' above
        edited = lines[x.start():x.end()]
        edited = edited[edited.rfind('|')+1:]

        # Complete file again
        temp = lines[:x.start()] + edited + "context.chrome={require};" + lines[x.end():]
        lines = temp
        print("Appended Instruction")

    # Save file
    file = io.open(path, 'w', encoding='iso-8859-1')
    file.write(lines)
    file.close()

def add_extension(path, extPath):
    extListPath = path + "/DevTools Extensions"

    if(os.path.exists(extListPath)):
        # Load extensions list
        file = io.open(extListPath, 'r')
        lines = file.read()
        file.close()

        if len(lines) != 0:
            # Add extension path if not present
            js = json.loads(lines)
            if extPath not in js:
                js.append(extPath)
            else:
                print("Extension already present")
                return
            print(js)

            # Save file back
            file = io.open(extListPath, 'w')
            file.write(json.dumps(js))
            file.close()
            print("Added Extension")
            pass
    # No extension list present, make a new one
    else:
        file = io.open(extListPath, 'w')
        file.write('["' + extPath + '"]')
        file.close()
        print("Added Extension")

# Change startup from Discord.exe to Discord.lnk - Windows Only
def replace_startup(key, value):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, win32RegistryKey, 0, winreg.KEY_ALL_ACCESS)
    except:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, win32RegistryKey)
    winreg.SetValueEx(key, "Discord", 0, winreg.REG_SZ, value)
    winreg.CloseKey(key)
    print("Updated Startup Registry")

def install_files(path):
    manifestPath = path + "/manifest.json"
    backgroundPath = path + "/background.html"
    loaderPath = path + "/SimpleDiscordCryptLoader.js"

    if(not os.path.exists(path)):
        os.mkdir(path)

    if(not os.path.exists(manifestPath)):
        print("Downloading manifest.json")
        urllib.request.urlretrieve(resManifest, manifestPath);
    else:
        print("manifest.json already present")

    if(not os.path.exists(backgroundPath)):
        print("Downloading background.html")
        urllib.request.urlretrieve(resBackground, backgroundPath);
    else:
        print("background.html already present")

    if(not os.path.exists(loaderPath)):
        print("Downloading SimpleDiscordCryptLoader.js")
        urllib.request.urlretrieve(resLoader, loaderPath);
    else:
        print("SimpleDiscordCryptLoader.js already present")

# Install Funcs

def windows_install():
    # Set up paths
    appdataPath = os.getenv('APPDATA')
    localappdataPath = os.getenv('LOCALAPPDATA')

    discordPath = localappdataPath + win32DiscordPath
    discordDataPath = appdataPath + win32DiscordPath
    pluginPath = localappdataPath + win32PluginPath
    registryValue = appdataPath + win32RegistryValue

    check_path("Discord", discordPath)
    check_path("Discord Data", discordDataPath)
    create_path("Plugin Dir", pluginPath)

    appPaths = []
    for path in os.listdir(discordPath):
        if(path.startswith("app-")):
            appPaths.append(discordPath + "\\" + path + "\\resources\\electron.asar")

    # Stop Discord
    stop_process(win32DiscordProcName)

    # Root Electron
    print("\n-- Rooting Electron --")
    for path in appPaths:
        root_electron(path)

    print("\n-- Adding Extension --")
    add_extension(discordDataPath, win32ExtensionPath)

    print("\n-- Editing Startup Registry --")
    replace_startup(win32RegistryKey, registryValue)

    print("\n-- Installing Files --")
    install_files(pluginPath)

def linux_paths():
    discordPath = None
    homePath = os.path.expanduser("~" + user)

    # Generic
    if(os.path.exists("/opt/discord")):
        print("Generic install detected.")
        return "/opt/discord", homePath +  "/.config/discord"

    # Snap
    if(os.path.exist("/snap/discord")):
        for(path in os.listdir("/snap/discord")):
            match = re.search(r'\d+$', path)
            if match is not None:
                print("Snap install detected.")
                return path + "/usr/share/discord", path + "/.config/discord"


def linux_install():
    # Set up paths
    user = os.getenv("SUDO_USER")
    if(user == None):
        print("Failure - Must run with SUDO")
        input("Enter a key...")
        sys.exit(0)

    homePath = os.path.expanduser("~" + user)

    discordPath, discordDataPath = linux_paths()
    pluginPath = homePath + linuxPluginPath

    if(discordPath is None or discordDataPath is None):
        print("Failed to find Discord install")
        return

    check_path("Discord", discordPath)
    check_path("Discord Data", discordDataPath)

    stop_process(linuxDiscordProcName)

    print("\n-- Rooting Electron --")
    root_electron(discordPath + "/resources/electron.asar")

    print("\n-- Adding Extension --")
    add_extension(discordDataPath, pluginPath)

    print("\n-- Installing Files --")
    install_files(pluginPath)

def mac_install():
    pass;

if __name__ == "__main__":
    print("-- SimpleDiscordCrypt Installer --")
    print("Installing for platform: {}".format(platform))
    print("\n-- Setup --")

    if platform == "win32":
        windows_install()
    if platform == "darwin":
        mac_install()
    if platform.startswith("linux"):
        linux_install()

    input("\nInstall Complete!\nPress any key...")
