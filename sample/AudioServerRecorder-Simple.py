# msm: source - http://www.instructables.com/id/Audio-Server-and-Recorder-With-Intel-Edison/?ALLSTEPS

#!/usr/bin/python

import mraa
import time
import os
import signal
import subprocess

record = 'arecord -f cd /home/pi/apps/sample/podcast.wav'
play = 'aplay /home/pi/sample/podcast.wav'
stopRecord = 'killall -9 arecord'
stopPlay = 'killall -9 aplay'

print("record pressed")
os.system(record)
time.sleep(10)
os.system(stopRecord)

print("play pressed")
os.system(play)
time.sleep(10)
os.system(stopPlay)
