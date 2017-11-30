# msm: source - https://www.hackster.io/pidoorbell-team/pidoorbell-7ef917?

from time import sleep
import os
import http.client, urllib
import RPi.GPIO as GPIO
import subprocess
import datetime
import MySQLdb
import socket
import fcntl
import struct


 
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN)
#GPIO.setup(23, GPIO.IN)

# setup variables
count = 0 
up = False
down = False
command = ""
filename = ""
index = 0
camera_pause = "500"
command2=""
db=MySQLdb.connect(host="localhost", user="root", passwd="raspberry", db="admin_pidoorbell")
cur=db.cursor()


hostname = socket.gethostname()
address= socket.gethostbyname("%s.local" % hostname)

#def restart():
	#print("Restarting... ")
	#command2="sudo reboot"
	#print(command2)
	#os.system(command2)

def takepic(imageName):
	print("click")
	command = "sudo fswebcam -r 640x480 --title Picture_taken_by_PiDoorBell_Copyright_2014 /var/www/pidoorbell/img/" + imageName
	print(command)
	os.system(command)
 
def PushOver(title,message,url):
   application_token = "YOUR_APPLICATION_TOKEN_HERE"
   user_token = "YOUR_USER_TOKEN_HERE"
   # Start your connection with the Pushover API server
   conn = http.client.HTTPSConnection("api.pushover.net:443")
 
   # Send a POST request in urlencoded json
   conn.request("POST", "/1/messages.json",
   urllib.parse.urlencode({
   "token": application_token,
   "user": user_token,
   "title": title,
   "message": message,
   "url": url,
   }), { "Content-type": "application/x-www-form-urlencoded" })
 
   # Listen for any error messages or other responses
   conn.getresponse()
 
# Application specific variables
 
# PushOver('Doorbell','Started','')
print 'Doorbell Server Started\r'
 
while True:
	if (GPIO.input(18) == False):
      		print 'Button Pushed!\r'
		

      		os.system('mpg321 -g 100 /home/pi/Ringtones/doorbell1.mp3 &amp;')

		now = datetime.datetime.now()
                timeString = now.strftime("%Y-%m-%d_%H_%M_%S")
                print("request received" + timeString)
		filename = timeString + '.jpg'
		
		print "BUTTON DOWN PRESSED"
		takepic(filename)

		#query="INSERT INTO images (id,url,date) VALUES (NULL," + filename  + ",NULL)"
		cur.execute("INSERT INTO images (id,url,date) VALUES (NULL,'" + filename  + "',NULL)")
		PushOver('PiDoorBell','Ding Dong! Someone is ringing at your door!','http://' + address + '/pidoorbell/img/' + filename)
		#print query
		up = GPIO.input(18)
		count = count +1

		
		sleep(.1)
	#if (GPIO.input(23)==False):
		#restart()
	
# this is never hit, but should be here to indicate if you plan on leaving the main loop

print "done"
sleep(0.2);
