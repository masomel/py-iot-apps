# msm: source - https://hackaday.io/project/5721-piscream

''' Home Automation With Camera '''
import picamera
import requests
import time
import RPi.GPIO as GPIO
''' The following code will be used to send a picture '''
url_image = 'http:localhost:4000/pagemulti'

camera = picamera.PiCamera()
camera.resolution =(640,460)

####################################### Image Posting #######################################################
def fileName (cur_name,post_name):
        files ={post_name:open(cur_name,'rb')}
        r = requests.post(url_image,files=files)
        if (r.status_code) ==200:
                print "Posted"
        else:
                print r.status_code

####################################Capturing Image ##########################################################
def captureImage(initialName,finalName,timeInterval):
        camera.capture(initialName+'.jpg')
        time.sleep(timeInterval)
        fileName(initialName+'.jpg',finalName) #This function is going to add the extension to finalName
'''The image being captured here will be stored in the same folder as the code '''
###################################### Input from PIR sensor and various values ###############################
''' Define input pins '''
pin = 4
''' GPIO Setup '''
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(pin,GPIO.IN) #Define input
time.sleep(5)
#######################Function form voice input and app button or webpage button ######################
link1 = "https://still-tundra-5719.herokuapp.com/home" #Do not change this link, all this has been tested.
def checkCommandInp():

        r = requests.get(link1)
        cmd = r.text
        #print cmd
        if cmd =="none":
                return "nothing received"
        else:
                if "lights" in cmd and "on" in cmd:
                        print "ligts on"
                        #code for lights
                elif "lights" in cmd and "off" in cmd:
                        print "lights off"
                        #code for ligts off
                elif "fan" in cmd and "on" in cmd:
                        print "fan on"
                        #code for fan on
                elif "fan" in cmd and "off" in cmd:
                        print "fan off"
                elif "Y" in cmd:
                        print "opening the door"
                        #open the door
                elif "N" in cmd:
                        print "closing the door"

while True:
        checkCommandInp()
        if (GPIO.input(4)): #input from PIR
                captureImage("newName","intruder", 0.5)
                print "Intruder captured"



