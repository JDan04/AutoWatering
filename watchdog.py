from time import sleep
import subprocess
import sys
import os

cmd = ["ps -aef | grep python"]
process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
stderr=subprocess.PIPE)
my_pid, err = process.communicate()

if str(my_pid).find("valve.py") == -1:
    print("Script is not running. Executing command now.")

    os.system("python3 valve.py & > /dev/null 2>&1 &")

else:
    print("Script is running")

sys.exit()
