from shutil import copy2, rmtree
from subprocess import Popen
from sys import exit
import urllib.request

# maybie you could do this automatic:
urllib.request.urlretrieve('https://raw.githubusercontent.com/RoadJDK/Yuumi-Bot-Extension/main/main.py', 'WTF.py')
urllib.request.urlretrieve('https://raw.githubusercontent.com/RoadJDK/Yuumi-Bot-Extension/main/main.py', 'WTF.py')

rmtree('bot') # will delete the folder itself

#Popen("app/main.py", shell=True) # go back to your program

exit("exit to restart the true program")
