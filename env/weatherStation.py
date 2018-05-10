# msm: source - http://www.instructables.com/id/Raspberry-Pi-Weather-Station/?ALLSTEPS

import time
import RPi.GPIO as GPIO
import Adafruit_DHT as dht
import smtplib
import os

GPIO.setmode(GPIO.BOARD)
GPIO.setup(18,GPIO.IN)
GPIO.setup(13,GPIO.IN)
GPIO.setup(15,GPIO.IN)
GPIO.setup(16,GPIO.IN)

timeset_HH = eval(input('Enter the hour you would like to be emailed at: ')) #Enter time to be emailed at in 24-hour time

timeset_MM = eval(input('Enter the minute you would like to be emailed at: '))

mail = smtplib.SMTP('smtp.gmail.com',587) #Set up and login to email

mail.ehlo()

mail.starttls()

mail.login('your email','your password')

h,t = dht.read_retry(dht.DHT11, 4)

humid_temp = 'Temp={0:0.1f}*C Humidity={1:0.1f}%'.format(t, h) #Read the sensor

while True: #This loop waits until the set time to send and email

    now = time.localtime()

    if now.tm_hour == int(timeset_HH) and now.tm_min == int(timeset_MM):

        break

    else:

        pass

    timeout = 60 - now.tm_sec

    if (GPIO.input(16)): #Read sensor and then email readings

        mail.sendmail('your email','your email','2in of rain ' + humid_temp)

    elif (GPIO.input(18)):

        mail.sendmail('your email','your email','1.5in of rain ' + humid_temp)

    elif (GPIO.input(13)):

        mail.sendmail('your email','your email','1in ofrain ' + humid_temp)

    elif (GPIO.input(15)):

        mail.sendmail('your email','your email','.5in of rain ' + humid_temp)

    else:

        mail.sendmail('your email','your email','0in ofrain ' + humid_temp)

mail.close()
GPIO.cleanup()
