#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    humidity_monitor.py
#    Part of "Raspberry Pi IoT: Temperature and Humidity monitor"
#    Copyright 2015 Pavlos Iliopoulos, techprolet.com
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
# 
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
# 
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import math
from time import sleep, strftime

import Adafruit_DHT
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from ubidots import ApiClient

import Image
import ImageDraw
import ImageFont

exec(compile(open('settings_screen.py').read(), 'settings_screen.py', 'exec'))
exec(compile(open('settings_sensor.py').read(), 'settings_sensor.py', 'exec'))

api = 0
tempVar = 0
humidVar = 0

#upload to ubidots every 6 measurements (free plan compatible)
uploadEvery =6
iterationCounter = 0

# Load default font.
graphFont = ImageFont.truetype('/usr/share/fonts/truetype/droid/DroidSans.ttf', 10)
timeFont = ImageFont.truetype('/usr/share/fonts/truetype/droid/DroidSans.ttf', 14)
humidityFont = ImageFont.truetype('/usr/share/fonts/truetype/droid/DroidSans.ttf', 22)

lastVals = []
graphVals = []
lastValIndex = 0
lastValDiff = 0

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)


def loadApi():
	global api, tempVar, humidVar
	try:
		#Create an "API" object
		api = ApiClient("xxxxxxxxxxxxxxxxxxxxxxxxxx")
	
		#Create a "Variable" object
		tempVar = api.get_variable("xxxxxxxxxxxxxxxxxxxxxxx")
		humidVar = api.get_variable("xxxxxxxxxxxxxxxxxxxxxxx")
	except:
		e = sys.exc_info()[0]
		print("Loading ubidots api failed with exception",e,"... will retry later")
		api=0


while True:
	humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
	
	# Draw a black filled box to clear the image.
	draw.rectangle((0,0,width,height), outline=0, fill=0)
	
	#show date and time
	draw.text((x, top),  strftime("%Y-%m-%d %H:%M"),  font=timeFont, fill=255)
	
	if humidity is not None and temperature is not None:
		print(strftime("%Y-%m-%d %H:%M:%S"),'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))
		draw.text((x, top+20),    '{0:0.1f}C  {1:0.1f}%'.format(temperature, humidity),  font=humidityFont, fill=255)
		
		#initialize chart
		if len(lastVals) == 0:
			for i in range(0,width):
				lastVals.append(humidity)
				graphVals.append(0)
			
		lastVals[lastValIndex] = humidity
		lastValIndex = (lastValIndex +1) % width
		if (iterationCounter % uploadEvery == 0):
			iterationCounter = 1
			if (api == 0):
				loadApi()
			if (api != 0):
				try:
					print("uploading to Ubidots...")
					tempVar.save_value({'value':temperature})
					humidVar.save_value({'value':humidity})
					print("...done")
				except:
					e = sys.exc_info()[0]
					print("Exception while connecting to Ubidots:", e)
		else:
			iterationCounter += 1
		
	else:
		print('Sensor reading failed. Will try again in the next cycle')
		draw.text((x, top+20),    'Error',  font=humidityFont, fill=255)
	
	# Display image.
	disp.image(image)
	disp.display()
	
	# sleep for ten seconds
	sleep(10)
	
	# ...and now show the humidity graph
	
	# resize humidity value range to screen height
	minVal = 100
	maxVal = 0
	for i in range (0, width):
		if lastVals[i] < minVal:
			minVal = lastVals[i]
		elif lastVals[i] > maxVal:
			maxVal = lastVals[i]
	minVal = int((math.floor(minVal / 10.0)) * 10)
	maxVal = int((math.ceil(maxVal / 10.0)) * 10)
	valDiff = maxVal - minVal
	
	if valDiff != lastValDiff:
		for i in range (0, width):
			graphVals[i] =  int (round((maxVal - lastVals[i]) * height / valDiff))
		lastValDiff = valDiff
	else:
		graphVals[lastValIndex - 1] = int (round((maxVal - lastVals[lastValIndex - 1]) * height / valDiff))
	
	# Draw a black filled box to clear the image.
	draw.rectangle((0,0,width,height), outline=0, fill=0)
	
	for i in range (0,width-1):
		draw.line((i, graphVals[(i + lastValIndex) % width], i+1, graphVals[(i+lastValIndex+1) % width]), fill=255)
			
	draw.text((0,0),  '{0:0.1f}%'.format(maxVal),  font=graphFont, fill=255)
	draw.text((0, height-10),  '{0:0.1f}%'.format(minVal),  font=graphFont, fill=255)
	
	
	# Display image.
	disp.image(image)
	disp.display()
	
	# sleep for another ten seconds
	sleep(10)
	

