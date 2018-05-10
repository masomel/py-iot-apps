#!/usr/bin/env python
"""
For switching Elro wall plugs using Python on Raspberry Pi with wiringPi Library.
from Dirk J. 2013

Requirements:
-WiringPi-Python Library
-433 Mhz Transmitter connected
-Export of GPIO port: gpio export <pin> out (pin=Broadcom GPIO number. Pin with connection
 to 'data' of an 433Mhz Transmitter)

Example
$ gpio export 17 out		# Exports pin 17 (e.g. in /etc/rc.local)
$ ./elro_wiringpi.py 8 1  # Switch D is turned on

This file uses wiringPi to output a bit train to a 433.92 MHz transmitter, allowing you
to control light switches from the Elro brand (AB440S). You need to export the pin before starting the
script. It does not require root permission

Credits:
This file is a just slightly modified version of "elropi.py" from by Heiko H. 2012:
	http://pastebin.com/aRipYrZ6
 It is changed to run without root by using WiringPi-Python instead of the RPi.GPIO library.
C++ source code written by J. Lukas:
	http://www.jer00n.nl/433send.cpp
and Arduino source code written by Piepersnijder:
	http://gathering.tweakers.net/forum/view_message/34919677
Some parts have been rewritten and/or translated.

This code uses the Broadcom GPIO pin naming.
For more on pin naming see: http://elinux.org/RPi_Low-level_peripherals

Version 1.0
"""

import time
import wiringpi

class RemoteSwitch(object):
	repeat = 10 # Number of transmissions
	pulselength = 300 # microseconds
	
	def __init__(self, unit_code, system_code=[1,1,1,1,1], pin=17):
		'''
		devices: A = 1, B = 2, C = 4, D = 8, E = 16 
		system_code: according to dipswitches on your Elro receivers
		pin: according to Broadcom pin naming
		'''		
		self.pin = pin
		self.system_code = system_code
		self.unit_code = unit_code
		
	def switchOn(self):
		self._switch(wiringpi.HIGH)

	def switchOff(self):
		self._switch(wiringpi.LOW)

	def _switch(self, switch):
		self.bit = [142, 142, 142, 142, 142, 142, 142, 142, 142, 142, 142, 136, 128, 0, 0, 0]		

		for t in range(5):
			if self.system_code[t]:
				self.bit[t]=136	
		x=1
		for i in range(1,6):
			if self.unit_code & x > 0:
				self.bit[4+i] = 136
			x = x<<1

		if switch == wiringpi.HIGH:
			self.bit[10] = 136
			self.bit[11] = 142
				
		bangs = []
		for y in range(16):
			x = 128
			for i in range(1,9):
				b = (self.bit[y] & x > 0) and wiringpi.HIGH or wiringpi.LOW
				bangs.append(b)
				x = x>>1
				
		wiringpi.wiringPiSetupSys()
		wiringpi.pinMode(self.pin,wiringpi.OUTPUT)
		wiringpi.digitalWrite(self.pin,wiringpi.LOW)
		for z in range(self.repeat):
			for b in bangs:
				wiringpi.digitalWrite(self.pin, b)
				time.sleep(self.pulselength/1000000.)

if __name__ == '__main__':
	import sys
	
	if len(sys.argv) < 3:
		print("usage:sudo python %s int_device int_state (e.g. '%s 2 1' switches device 2 on)" % \
			(sys.argv[0], sys.argv[0]))
		sys.exit(1)

	# Change the key[] variable below according to the dipswitches on your Elro receivers.
	default_key = [0,0,0,0,0] 
	
	# change the pin accpording to your wiring
	default_pin = 17
	device = RemoteSwitch(  unit_code= int(sys.argv[1]), 
							system_code=default_key, 
							pin=default_pin)

	if int(sys.argv[2]) == 1:
		device.switchOn()
	else: 
		device.switchOff()