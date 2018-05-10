#!/usr/bin/python  
  
#dependancies  
from Adafruit_I2C          import Adafruit_I2C  
from Adafruit_MCP230xx     import Adafruit_MCP230XX  
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate  
from datetime              import datetime  
from subprocess            import *  
from time                  import sleep, strftime  
from queue                 import Queue  
from threading             import Thread  
from random import *
import RPi.GPIO as GPIO
import Adafruit_DHT
 
import smbus  

import sqlite3
import os
import time
import glob
  
# initialize the LCD plate  
#   use busnum = 0 for raspi version 1 (256MB)   
#   and busnum = 1 for raspi version 2 (512MB)  
LCD = Adafruit_CharLCDPlate(busnum = 1)  
  
# Define a queue to communicate with worker thread  
LCD_QUEUE = Queue()  
TEMP_QUEUE = Queue()
  
# Globals  
TEMPNEEDED = 20
TEMPNOW    = 30
CHAUFF	   = False
delaiGetTemp = 60 #seconds

# GPIO control
GPIO.setmode(GPIO.BOARD)
GPIO.setup(16,GPIO.OUT)# stop
GPIO.setup(18,GPIO.OUT)# start
GPIO.setup(22,GPIO.OUT)# led

# Buttons  
NONE           = 0x00  
SELECT         = 0x01  
RIGHT          = 0x02  
DOWN           = 0x04  
UP             = 0x08  
LEFT           = 0x10  
UP_AND_DOWN    = 0x0C  
LEFT_AND_RIGHT = 0x12  
  
  
  
# ----------------------------  
# WORKER THREAD  
# ----------------------------  
  
# Define a function to run in the worker thread  
def update_lcd(q):  
	
   	while True:
      		msg = q.get()
      		# if we're falling behind, skip some LCD updates
      		while not q.empty():
         		q.task_done()
         		msg = q.get()
      		LCD.setCursor(0,0)
      		LCD.message(msg)
      		q.task_done()
   	return

def update_temp(i):
	while True:
		sleep(delaiGetTemp)
		global TEMPNOW, CHAUFF, TEMPNEEDED
		humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302,4)
		TEMPNOW = '{0:0.1f}'.format(temperature)
		if(CHAUFF == True):
			logTemp(temperature, humidity, 1, TEMPNEEDED)
		else:
			logTemp(temperature,humidity,0,TEMPNEEDED)
		TEMPNEEDED = getTempNeeded()
	return

def logTemp(temp, humidity, chauffmarcel,tempneed):
	try:
		conn=sqlite3.connect('/home/pi/temperature/temperature.db')
		curs=conn.cursor()
		print("INSERT INTO temperature values(datetime('now'),(?),(?),(?),(?))")
		curs.execute("INSERT INTO temperature values(datetime('now','localtime'),(?),(?),(?),(?))",(temp,humidity,chauffmarcel,tempneed))
		conn.commit()
		conn.close()
	except:
		conn.close()

# ----------------------------
# MAIN LOOP
# ----------------------------

def main():
	global TEMPNEEDED, TEMPNOW, CHAUFF
	
	# Setup AdaFruit LCD Plate
	LCD.begin(16,2)
	LCD.clear()
	LCD.backlight(LCD.VIOLET)
	
	# Create the worker thread and make it a daemon
	worker = Thread(target=update_lcd, args=(LCD_QUEUE,))
	worker.setDaemon(True)
	worker.start()

	# Create the worker thread and make it a daemon
        worker1 = Thread(target=update_temp, args=(TEMP_QUEUE,))
        worker1.setDaemon(True)
        worker1.start()

	# Display startup banner
	LCD_QUEUE.put('   Thermostat   \n  fait maison!', True)
	
 	# read current temperature
	chauffMarcel('init')
	sleep(2)
	LCD.clear()
	setTempNeeded(TEMPNEEDED)	



# ----------------------------
# control temperature
# ----------------------------
	
	nbDeTour1    = 3
	attendUnPeu1 = 0
	
	nbDeTour2    = 5
	attendUnPeu2 = nbDeTour2

	# Main loop
	while True:
	#	update_temp.join()
		press = read_buttons()
		
        # DOWN button pressed
		if(press == DOWN):
			TEMPNEEDED -= 0.5
			setTempNeeded(TEMPNEEDED)	
  			attendUnPeu1 = nbDeTour1
		
		# UP button pressed
		if(press == UP):
			TEMPNEEDED += 0.5
			setTempNeeded(TEMPNEEDED)	
  			attendUnPeu1 = nbDeTour1
		
		# SELECT button pressed  
		if(press == SELECT):  
			menu_pressed() 		
		
		if(attendUnPeu1 > 0):
			attendUnPeu1 -= 1
			if(attendUnPeu1 == 0):
				if(TEMPNEEDED > float(TEMPNOW) and CHAUFF == False):
            				chauffMarcel(True)
					CHAUFF = True
					LCD_QUEUE.put('Chauff Marcel   \n' + str(TEMPNOW) + 'C       '+str(TEMPNEEDED)+'C   ', True)  
				elif(TEMPNEEDED <= float(TEMPNOW) and CHAUFF == True):
						chauffMarcel(False)
						CHAUFF = False  
						LCD_QUEUE.put('Chauffage eteint\n' + str(TEMPNOW) + 'C       '+str(TEMPNEEDED)+'C   ', True)  
 		
		if(attendUnPeu2 > 0):
			attendUnPeu2 -= 1
			if(attendUnPeu2 == 0):
				attendUnPeu2 = nbDeTour2
				if(TEMPNEEDED > float(TEMPNOW)):
					if(CHAUFF == False):
                                        	chauffMarcel(True)
                                        	CHAUFF = True
                                        	LCD_QUEUE.put('Chauff Marcel   \n' + str(TEMPNOW) + 'C       '+str(TEMPNEEDED)+'C   ', True)
					else:
						LCD_QUEUE.put('Chauff Marcel   \n' + str(TEMPNOW) + 'C       '+str(TEMPNEEDED)+'C   ', True)
                                elif(TEMPNEEDED <= float(TEMPNOW)):
					if(CHAUFF == True):
                                        	chauffMarcel(False)
                                        	CHAUFF = False
                                        	LCD_QUEUE.put('Chauffage eteint\n' + str(TEMPNOW) + 'C       '+str(TEMPNEEDED)+'C   ', True)
					else:
						LCD_QUEUE.put('Chauffage eteint\n' + str(TEMPNOW) + 'C       '+str(TEMPNEEDED)+'C   ', True)
		delay_milliseconds(90)
	update_lcd.join()


# ----------------------------  
# READ SWITCHES  
# ----------------------------  

def read_buttons():  
  
   buttons = LCD.buttons() 
   # Debounce push buttons
   if(buttons != 0):
      while(LCD.buttons() != 0):
         delay_milliseconds(1)
   return buttons
  
  
  
def delay_milliseconds(milliseconds):  
   seconds = milliseconds / float(1000) # divide milliseconds by 1000 for seconds  
   sleep(seconds)  
  
  
  
# ----------------------------  
# Get Temperature  
# ----------------------------  
  
def getTemperature():
	try:
		humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302,4)
	except:
		print('Failed to get reading. Try again!')
	if humidity is not None and temperature is not None:
        	print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))
		return '{0:0.1f}'.format(temperature)
	else:
	        print('Failed to get reading. Try again!') 
	return choice(c) 

def getTempNeeded():
	global TEMPNEEDED
	try:
		conn=sqlite3.connect('/home/pi/temperature/temperature.db')
        	curs=conn.cursor()
        	curs.execute("Select degree from tempneed")
		rows=curs.fetchall()
        	conn.close()
		return rows[0][0]
	except:
		return TEMPNEEDED

def setTempNeeded(degree):
	try:
        	conn=sqlite3.connect('/home/pi/temperature/temperature.db')
        	curs=conn.cursor()
        	curs.execute("replace into tempneed values(1,"+ str(degree) +")")
       	 	conn.commit()
        	conn.close()
	except:
		conn.close()		

def chauffMarcel(choix):
        #control gpio to on/off relai
        if(choix == True):
                GPIO.output(16,True)
                sleep(0.3)
                GPIO.output(16,False)
		GPIO.output(22,True)
        elif(choix == False):
                GPIO.output(18,True)
                sleep(0.3)
                GPIO.output(18,False)
		GPIO.output(22,False)
        elif(choix == 'init'):
		GPIO.output(18,True)
                sleep(0.3)
                GPIO.output(18,False)
                GPIO.output(22,False)

 
# ----------------------------  
# SETUP MENU  
# ----------------------------  
  
def menu_pressed():  
   global STATION  
  
   MENU_LIST = [  
      '1. Display Time \n   & IP Address ',  
      '2. Chauff Marcel\n  mais que 5min ',  
      '3. System       \n   ShutDown!    ',  
      '4. Reboot pi!   \n                ',  
      '5. Exit         \n                ']  
  
   item = 0  
   LCD.clear()  
   LCD.backlight(LCD.YELLOW)  
   LCD_QUEUE.put(MENU_LIST[item], True)  
  
   keep_looping = True  
   while (keep_looping):  
  
      # Wait for a key press  
      press = read_buttons()  
  
      # UP button  
      if(press == UP):  
         item -= 1  
         if(item < 0):  
            item = len(MENU_LIST) - 1  
         LCD_QUEUE.put(MENU_LIST[item], True)  
  
      # DOWN button  
      elif(press == DOWN):  
         item += 1  
         if(item >= len(MENU_LIST)):  
            item = 0  
         LCD_QUEUE.put(MENU_LIST[item], True)  
  
      # SELECT button = exit  
      elif(press == SELECT):  
         keep_looping = False  
  
         # Take action  
         if(  item == 0):  
            # 1. display time and IP address  
            display_ipaddr()  
         elif(item == 1):  
            # 2. chauff marcel 5min 
            LCD_QUEUE.put('chauff marcel   \n  pendant 5min  ',True) 
            chauffMarcel(True)
            sleep(300)
            chauffMarcel(False)
         elif(item == 2):  
	        # 3. shutdown the system  
            LCD_QUEUE.put('Shutdown        \nLinux now! ...  ', True)  
            LCD_QUEUE.join()  
            output = run_cmd("sudo shutdown now")  
            LCD.clear()  
            #LCD.backlight(LCD.OFF)  
            exit(0) 
         elif(item == 3):
            # 4. reboot the system  
            LCD_QUEUE.put('Reboot Pi      \nLinux now! ...  ', True)  
            LCD_QUEUE.join()  
            output = run_cmd("sudo reboot -f")  
            LCD.clear()  
            #LCD.backlight(LCD.OFF)  
            exit(0)  
      else:  
         delay_milliseconds(99)  
  
   # Restore display  
   LCD_QUEUE.put("re", True)  
  
  
  
# ----------------------------  
# DISPLAY TIME AND IP ADDRESS  
# ----------------------------  
  
def display_ipaddr():  
	show_wlan0 = "ip addr show wlan0 | cut -d/ -f1 | awk '/inet/ {printf \"w%15.15s\", $2}'"  
	show_eth0  = "ip addr show eth0  | cut -d/ -f1 | awk '/inet/ {printf \"e%15.15s\", $2}'"  
	ipaddr = run_cmd(show_eth0)  
	if ipaddr == "":  
		ipaddr = run_cmd(show_wlan0)  
  
	i = 29  
	muting = False  
	keep_looping = True  
	while (keep_looping):  
		# Every 1/2 second, update the time display  
		i += 1  
		#if(i % 10 == 0):  
		if(i % 5 == 0):  
			LCD_QUEUE.put(datetime.now().strftime('%b %d  %H:%M:%S\n')+ ipaddr, True)  
	  
		     # Every 3 seconds, update ethernet or wi-fi IP address  
		if(i == 60):  
			ipaddr = run_cmd(show_eth0)  
			i = 0  
		elif(i == 30):  
			ipaddr = run_cmd(show_wlan0)  
	  
		# Every 100 milliseconds, read the switches  
		press = read_buttons()  
		# Take action on switch press  
		
		# UP button pressed  
		if(press == UP):  
			output = run_cmd("mpc volume +2")  
	  
		# DOWN button pressed  
		if(press == DOWN):  
			output = run_cmd("mpc volume -2")  
	  
		# SELECT button = exit  
		if(press == SELECT):  
			keep_looping = False  
	  
		# LEFT or RIGHT toggles mute  
		elif(press == LEFT or press == RIGHT ):  
			if muting:  
				#amixer command not working, can't use next line  
				#output = run_cmd("amixer -q cset numid=2 1")  
				mpc_play(STATION)  
				# work around a problem.  Play always starts at full volume  
				delay_milliseconds(400)  
				output = run_cmd("mpc volume +2")  
				output = run_cmd("mpc volume -2")  
			else:  
				#amixer command not working, can't use next line  
				#output = run_cmd("amixer -q cset numid=2 0")  
				output = run_cmd("mpc stop" )  
				muting = not muting  
		   
      	delay_milliseconds(99)  
  
  
  
# ----------------------------  
  
def run_cmd(cmd):  
	p = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)  
	output = p.communicate()[0]  
	return output  
  
  
  
#def run_cmd_nowait(cmd):  
#   pid = Popen(cmd, shell=True, stdout=NONE, stderr=STDOUT).pid  

if __name__ == '__main__':
	main()
