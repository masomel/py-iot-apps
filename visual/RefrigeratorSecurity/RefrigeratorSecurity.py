"""
    RefrigeratorSecurity.py
    Created by Dmitry Chulkov
    Security system for refrigerator. When a person opens refrigerator
    this program takes a picture of him/her, identify (with Microsoft Face API),
    checks permission for this person, send result to Node-Red
"""

import RPi.GPIO as GPIO

import getImage, recognition, access, sendData

global button1
button1 = False

    
def sensor1(channel):
    global button1
    button1 = True

def sensor2(channel):
    global button1
    if button1 == True:
        button1 = False
        process()


# this function starts all analyzing stuff 
def process():
    path = "/home/pi/"
    host = "192.168.1.40:8080"

    # save a picture of a violator
    getImage.fromIpCam(path, host)
    # get name of person on the photo
    name = recognition.checkPerson(path + "image.jpg", "fff-fff")
    # check this person for access permissions
    status = access.check(name)
    if status['access'] != True:
        if status['trustedPerson'] == False:
            msg = {
                'trustedPerson': False,
                'message': 'Stransger use your refrigerator',
                'emailTopic': 'Security Breach'
                }
            sendData.toNodeRed(msg)
        elif status['trustedPerson'] == True:
            msg = {
                'trustedPerson': True,
                'message': name + ' has violated access restriction',
                'emailTopic': 'Access Violation'
                }
            sendData.toNodeRed(msg)
    

GPIO.setmode(GPIO.BCM)

# attach sensor buttons to pins 23 and 24
# 0 - button pressed, 1 - released
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# wait for Rising Edge for button 1 (23 pin)
GPIO.add_event_detect(23, GPIO.RISING, callback=sensor1, bouncetime=300)
# wait for Falling Edge for button 2 (24 pin)
GPIO.add_event_detect(24, GPIO.FALLING, callback=sensor2, bouncetime=300)




while True:
    x = True


GPIO.cleanup()


