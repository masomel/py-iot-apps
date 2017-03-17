# msm: source - https://www.hackster.io/Hoefnix/monitoring-the-doorbell-6a2000
#!/usr/bin/python.

import RPi.GPIO as GPIO 
import time
import subprocess
import os

GPIO.setmode(GPIO.BCM)  
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def erWordtGebeld(channel):
        returncode = subprocess.Popen("/usr/bin/fswebcam -c /opt/develop/deurmonitor.cfg", shell=True)
        print('Doorbell rang at ' + time.strftime("%a om %H:%M:%S"))

GPIO.add_event_detect(24, GPIO.FALLING, callback=erWordtGebeld, bouncetime=500)
print( "Deurbelmonitor is started at " + time.strftime("%A om %H:%M:%S") )
print( "Druk op Ctrl-C om te stoppen")

try:
        while True:
                time.sleep(3600)

except KeyboardInterrupt:
        print "Cleaning up..."
        GPIO.remove_event_detect(24)
        GPIO.cleanup()
        print "Done"
