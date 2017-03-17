# msm: source - http://www.instructables.com/id/Smart-JPEG-Camera-for-Home-Security/?ALLSTEPS

import RPi.GPIO as GPIO
import time
import picamera
import datetime

timeFormat = 0  

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN) 
GPIO.setup(18, GPIO.IN)
camera = picamera.PiCamera()
 
while True:
        input17 = GPIO.input(17)  #Pin number 17 activates
        input18 = GPIO.input(18)  #Pin number 18 activates
	now = datetime.datetime.now()
	timeFormat = now.strftime("%Y%m%d_%H%M_%S.%s") #To put date and time in images 
	
        if input17 == True or input18 == True:  #If PIR Sensor detects something, the Picamera will take. 
                print('Motion_Detected_%s' %timeFormat)  
		camera.capture('image_%s.jpg' %timeFormat) #To take a picture
		
                time.sleep(1) #sleeping time 1 second
