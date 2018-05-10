# msm: source - http://www.instructables.com/id/Raspberry-Pi-Laser-Security-System/?ALLSTEPS

#!/usr/bin/python3
# Author: EliBuilds
# This script will introduce you to the basics of accessing and reading the pins on the pi
# hint: ctrl-c will exit script


laser_1_input = 25 # this variable stores the name of the pin on which you have connected the laser
import RPi.GPIO as GPIO  #we need this so we can access the pins
import time # to allow for sleep function
import os
import subprocess

def send_mail():
 global sm_pid
 global sending_mail
 # we need these vars to be global so that they will persist through function calls
 if sending_mail:
  output = os.waitpid(sm_pid,os.WNOHANG)
  #check what this does
  print(output)
 process_running = os.path.exists("/proc/" + str(sm_pid))
 print(process_running)		
 if not process_running:
  print("Alert -> Sending")
  sm_pid = os.spawnlp(os.P_NOWAIT, "/usr/bin/python3","python3","/home/pi/Desktop/security/send_mail.py")
  sending_mail = True
 else:
  print("Currently sending mail!")
 return

def laser_a_rising_event(channel):
 # this will be the function called when the laser is tripped going from high to low
 print("Function Called")
 time.sleep(.2)   # wait to check for ligitimate interupt, increase this value to decrease the sensitivity of the system
 if GPIO.input(laser_1_input):	
  #if the pin is still triggered after the sleep interval it must be a legitimate triggering
  hr  = time.strftime("%H",time.localtime()) #get the hour
  min = time.strftime("%M",time.localtime()) #get the minutes
  sec = time.strftime("%S",time.localtime()) #get the seconds
  print(("Tripped @ ",hr,":",min,":",sec))
  send_mail()
 else:
  print("False positive")
 return

###
# End of funcitons begin of program
###

print ("Setting Up Pins")
GPIO.setmode(GPIO.BCM) # use this to set the pin naming mode 
#see for info on this command http://raspberrypi.stackexchange.com/questions/12966/what-is-the-difference-between-board-and-bcm-for-gpio-pin-numbering
GPIO.setup(laser_1_input,GPIO.IN) # set up pin 25 as the input
GPIO.remove_event_detect(laser_1_input)   #set defaults for event detection		
GPIO.add_event_detect(laser_1_input,GPIO.RISING,callback=laser_a_rising_event) # register a new interrupt and its callback function
sm_pid = 0
sending_mail = False
print("Waiting For Event")

while True:
	time.sleep(.1)
 #wait so we don't lock up proccessor
try:
	time.sleep(1)
except KeyboardInterrupt:
 GPIO.cleanup() #cleanup
 exit()
