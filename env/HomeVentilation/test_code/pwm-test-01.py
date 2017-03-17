import RPi.GPIO as gpio
from time import sleep

gpio.setmode(gpio.BOARD)
gpio.setup(12,gpio.OUT)
p = gpio.PWM(12,2300)      #2kHz
p.start(50)                #%duty cycle
#print input("Press <return>")
sleep (3)
p.stop()
gpio.cleanup()

