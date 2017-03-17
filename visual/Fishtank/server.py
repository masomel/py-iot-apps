from thread import start_new_thread
import time
import os
os.chdir("/var/www/fishtank/server/")

import FishTank
import Log
from FlaskServer import app

print "Ready"

def tick():
	while True:
		time.sleep(1)
		FishTank.tick()

start_new_thread(tick, ())