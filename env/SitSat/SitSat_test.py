import os
import RPi.GPIO as GPIO
import time
import subprocess
import datetime

current = datetime.datetime.now()

threshold = 12
Rasptrigger = 21
pulse_start = 0
pulse_end = 0
#Module specification
TRIG1 = 5
ECHO1 = 6

GPIO.setmode(GPIO.BCM)
#Sensor 1 setup
GPIO.setup(TRIG1,GPIO.OUT)
GPIO.setup(ECHO1,GPIO.IN)
GPIO.setup(Rasptrigger, GPIO.OUT)

def sonar(trigger, echo):
	global pulse_start,pulse_end
	GPIO.output(trigger, False)
	time.sleep(0.3)
	
	GPIO.output(trigger, True)
	time.sleep(0.00001)
	GPIO.output(trigger, False)
	
	while GPIO.input(echo)==0:
	  pulse_start = time.time()
	
	while GPIO.input(echo)==1:
	  pulse_end = time.time()
	
	pulse_duration = pulse_end - pulse_start
	
	distance = pulse_duration * 17150
	
	distance = round(distance, 2)
	
	return distance

try:
	while True:
		distance1 = sonar(TRIG1, ECHO1)
		print("Distance1:",distance1,"cm")
		if (distance1 < threshold):
			print("You just took a break at " + current.strftime("%Y-%m-%d %H:%M") + " good for health")
			GPIO.output(Rasptrigger, True)
			time.sleep(1)
		else:		
			GPIO.output(Rasptrigger, False)
			time.sleep(0.1)
except:	
	print("Live Strong")

finally:
	GPIO.cleanup()
