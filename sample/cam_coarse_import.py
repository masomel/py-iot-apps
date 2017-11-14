import time
import subprocess
import datetime

dt = datetime.datetime.now()
now = dt.strftime('%Y%m%d-%H%M%S')
name = now + '.jpg'
print(name)

cmd = 'raspistill -t 500 -o /tmp/' + name

subprocess.call([cmd], shell=True)
