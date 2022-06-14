from os import mkdir
from shutil import rmtree
from subprocess import Popen
from sys import exit
import urllib.request

rmtree('bot')
mkdir('bot')
mkdir('bot/common')

# maybie you could do this automatic:
urllib.request.urlretrieve('https://raw.githubusercontent.com/RoadJDK/Yuumi-Bot-Extension/main/bot/main.py', 'bot/main.py')
urllib.request.urlretrieve('https://raw.githubusercontent.com/RoadJDK/Yuumi-Bot-Extension/main/bot/requirements.txt', 'bot/requirements.txt')
urllib.request.urlretrieve('https://raw.githubusercontent.com/RoadJDK/Yuumi-Bot-Extension/main/bot/config.json', 'bot/config.json')
urllib.request.urlretrieve('https://raw.githubusercontent.com/RoadJDK/Yuumi-Bot-Extension/main/bot/common/champions.json', 'bot/common/champions.json')
urllib.request.urlretrieve('https://raw.githubusercontent.com/RoadJDK/Yuumi-Bot-Extension/main/bot/common/gamemodes.json', 'bot/common/gamemodes.json')

Popen("python bot/main.py", shell=True)
print()
exit("exit to restart the true program")
