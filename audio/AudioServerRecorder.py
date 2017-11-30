# msm: source - http://www.instructables.com/id/Audio-Server-and-Recorder-With-Intel-Edison/?ALLSTEPS

#!/usr/bin/python

import mraa 
import time
import os
import signal
import subprocess


LED_GPIO = 5                   # The LED pin
BUTTON_GPIO = 6                # The start record button 
STOPBTN_GPIO = 7                # The stop record and play button
PLAYBTN_GPIO = 8 
led = mraa.Gpio(LED_GPIO)      # Get the LED pin object
led.dir(mraa.DIR_OUT)          # Set the direction as output
ledState = False               # LED is off to begin with
led.write(0)

btn = mraa.Gpio(BUTTON_GPIO)
stopBtn = mraa.Gpio(STOPBTN_GPIO)
playBtn = mraa.Gpio(PLAYBTN_GPIO)

btn.dir(mraa.DIR_IN)
stopBtn.dir(mraa.DIR_IN)
playBtn.dir(mraa.DIR_IN)

record = 'arecord -f cd /usr/share/apache2/htdocs/podcast/podcast.wav'
play = 'aplay /usr/share/apache2/htdocs/podcast/podcast.wav'
stopRecord = 'killall -9 arecord'
stopPlay = 'killall -9 aplay'
#initialise a previous input variable to 0 (assume button not pressed last)
prev_input = 0
while True:
  #take a reading
  strtBtn = btn.read()
  stopButton = stopBtn.read()
  playButton = playBtn.read()
  
  #if the last reading was low and this one high, print
  if ((not prev_input) and strtBtn):
    print("record pressed")
    led.write(1)
    time.sleep(0.5)
    led.write(1)
    time.sleep(0.5)
    os.system(record)

  #update previous input
  prev_input = strtBtn
  #slight pause to debounce
  time.sleep(0.05)
  
  #if the last reading was low and this one high, print
  if ((not prev_input) and stopButton):
    print("stop pressed")
    led.write(1)
    time.sleep(0.1)
    led.write(1)
    time.sleep(0.1)
    led.write(1)
    time.sleep(0.1)
    os.system(stop) 

  #update previous input
  prev_input = stopButton
  #slight pause to debounce
  time.sleep(0.05)

  if ((not prev_input) and playButton):
    print("play pressed")
    os.system(stopPlay)
    os.system(stopRecord)

  #update previous input
  prev_input = playButton
  #slight pause to debounce
  time.sleep(0.05)



