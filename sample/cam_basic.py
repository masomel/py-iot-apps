import time
from subprocess import call
from datetime import datetime

dt = datetime.now()
now = dt.strftime('%Y%m%d-%H%M%S')
name = now + '.jpg'
print(name)

cmd = 'raspistill -t 500 -o /tmp/' + name

call([cmd], shell=True)
