# msm: source - http://www.instructables.com/id/Audio-Server-and-Recorder-With-Intel-Edison/?ALLSTEPS

#!/usr/bin/python

import mraa
import time
import os
import signal
import subprocess

record = 'arecord -f cd /home/pi/apps/sample/podcast.wav'
play = 'aplay /home/pi/apps/sample/podcast.wav'

print("record pressed")
os.system(record)
time.sleep(10)

print("play pressed")
os.system(play)
time.sleep(10)
