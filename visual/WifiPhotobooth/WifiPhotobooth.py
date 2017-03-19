__author__ = 'andreas.kreuzer.ak2'

import os
import time
import random
import subprocess

import pygame
import picamera
import Image
from pygame.locals import *
import RPi.GPIO as GPIO

os.environ["SDL_FBDEV"] = "/dev/fb0"

class Photobooth:
    screen = None;
    logo = None;

    def __init__(self):
        global ScreenSize
        "Ininitializes a new pygame screen using the framebuffer"
        # Based on "Python GUI in Linux frame buffer"
        # http://www.karoltomala.com/blog/?p=679
        disp_no = os.getenv("DISPLAY")
        if disp_no:
            print "I'm running under X display = {0}".format(disp_no)

        # Check which frame buffer drivers are available
        # Start with fbcon since directfb hangs with composite output
        drivers = ['fbcon', 'directfb', 'svgalib']
        found = False
        for driver in drivers:
            # Make sure that SDL_VIDEODRIVER is set
            if not os.getenv('SDL_VIDEODRIVER'):
                os.putenv('SDL_VIDEODRIVER', driver)
            try:
                pygame.display.init()
            except pygame.error:
                print 'Driver: {0} failed.'.format(driver)
                continue
            found = True
            break

        if not found:
            raise Exception('No suitable video driver found!')

        ScreenSize = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        print "Framebuffer size: %d x %d" % (ScreenSize[0], ScreenSize[1])
        self.screen = pygame.display.set_mode(ScreenSize, pygame.FULLSCREEN)
        # Clear the screen to start
        self.screen.fill((0, 0, 0))
        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.display.update()
        pygame.mouse.set_visible(False)

    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."

    # Shows an arbitrary picture from the AllPicturesList
    def diashow(self):
        global AllPicturesList, PictureFolder, NumberOfPicturesTaken, IsCamActive
        if IsCamActive is True:  # Stop preview if it is active.
            self.StopPreview()

        # Load a random Picture from the list.
        NextPictureName = AllPicturesList[random.randint(0, NumberOfPicturesTaken - 1)]
        TempPicture = os.path.join(PictureFolder, NextPictureName)
        TempImage = pygame.image.load(TempPicture).convert()
        TempScreen = pygame.transform.scale(TempImage, (1024, 800))  # 1024x800 doesn't fit into the screen, but the picture is not deformed
        PB.screen.blit(TempScreen, (0, -100))                     # move 100 pixel up to show the middle of the picture

        # Display the image-name
        if NumberOfPicturesTaken > 1 :          # Skip if it is the instruction picture
            font = pygame.font.Font(None, 40)
            PictureNameText = font.render(str(NextPictureName), True, ( 0xFF, 0xFF, 0xFF ))  # White text
            PB.screen.blit(PictureNameText, (50, 700))

        # Update Display
        pygame.display.update()

    # Funktion to start the preview
    def startPreview(self):
        global cam, IsCamActive, CamFrameRate
        # Clear the screen to start
        PB.screen.fill((0, 0, 0))
        pygame.display.update()
        cam.resolution = PicturesSize
        cam.framerate = CamFrameRate
        cam.start_preview()
        # time.sleep(0)
        IsCamActive = True


    # Funktion to overlay the preview with the countdown images
    def CD(self):
        global LastPictures, cam, IsCamActive
        if IsCamActive is False:
            # print "CD Cameraactive is false"
            self.startPreview()
        countdownimages = ['03.png', '02.png', '01.png']
        # Long countdown: countdownimages = [ '05.png', '04.png', '03.png', '02.png', '01.png']
        for bild in countdownimages:
            # Load the arbitrarily sized image
            img = Image.open(bild)
            # // is integer division
            pad = Image.new('RGB', (
                ((img.size[0] + 31) // 32) * 32,
                ((img.size[1] + 15) // 16) * 16,
                ))
            pad.paste(img, (0, 0))
            o = cam.add_overlay(pad.tostring(), size=img.size, alpha=128, layer=3, fullscreen=False, window=(450, 250, 128, 128))
            time.sleep(1)
            o.close()
        self.takePicture()

    def qroverlay(self):
	img = Image.open("QR.png")
        # // is integer division
        pad = Image.new('RGB', (
             ((img.size[0] + 31) // 32) * 32,
             ((img.size[1] + 15) // 16) * 16,
             ))
        pad.paste(img, (0, 0))
        o = cam.add_overlay(pad.tostring(), size=img.size, alpha=255, layer=4, fullscreen=False, window=(32, 20, img.size[0], img.size[1]))
        # time.sleep(1)



    # Funktion to stop preview
    def StopPreview(self):
        global cam, IsCamActive
        if IsCamActive is True:
            print "Stoppreview cameraaktive is true"
            cam.stop_preview()
            IsCamActive = False


    # Funktion to take a picture
    def takePicture(self):
        global cam, IsCamActive
        if IsCamActive is False:
            self.startPreview()
        NewPictureName = "img_" + time.strftime("%Y%m%d%H%M%S") + ".jpg"
        cam.capture(NewPictureName)          # Take the picture!
        LastPictures.append(NewPictureName)  # keep it on the list for combining




# Global variables

# RPi.GPIO Layout verwenden (wie Pin-Nummern)
GPIO.setmode(GPIO.BCM)
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

cam = picamera.PiCamera()   # There is only one camera
IsCamActive = False         # Is the camera-preview active?
LastPictures = []           # List of the last pictures for combining
DiashowTimerCounter = 0     # counter to trigger the diashow
AllPicturesList = []        # List of all pictures ever taken
PictureFolder = os.path.join(os.getcwd(), 'Pictures')  # folder for the pictures
NumberOfPicturesTaken = 1   # how many pictures are in the AllPicturesList?

PicturesSize = (640, 480)   # Size for the camera
CamFrameRate = 12           # We don't need 25fps. relax!

# Touchscreen-calibration done manually. Add the offset and multiply with factor.
MouseOffset = ( 45, 55 )
MouseFactor = ( 1.084, 0.8522 )

#set size of the screen
ScreenSize = 1024, 600

# external shell-script-call: imagemagick convert ...
def combine():
    global LastPictures
    subprocess.call( ['/home/pi/pb/combine.sh', LastPictures[0], LastPictures[1], LastPictures[2], LastPictures[3]])
    LastPictures = []

# Update the list of all pictures taken, may be optimised for not to read all files again, but only add the new ones...
def UpdateAllPicturesList():
    global AllPicturesList, NumberOfPicturesTaken, PictureFolder
    AllPicturesList = []
    NumberOfPicturesTaken = 0
    for dat in os.listdir(PictureFolder):
        if dat.endswith('.jpg'):
            AllPicturesList.append(dat)
            NumberOfPicturesTaken += 1


def safeshutdown(arg):
        #print "Taster gedrueckt" + str(arg)
	# shutdown our Raspberry Pi
	os.system("sudo shutdown -h now")

# Main
PB = Photobooth()
PB.startPreview()
time.sleep(0.1)

# Implement Button-Callback to shut down the raspberry.
GPIO.add_event_detect(10, GPIO.RISING, callback=safeshutdown, bouncetime=300)

# After start, show the instructable
AllPicturesList.append('Instructable.png')
DiashowTimerCounter = 140  # sofortiger Start mit Infoscreen nach dem Booten

while True:
    event = pygame.event.poll()     # a NoEvent is given back, when there was no touch Event.

    # If there was a touch-Event: Go and take some pictures
    if event.type == pygame.MOUSEBUTTONDOWN:
        # print time.strftime("%Y-%m-%d-%H-%M-%S") + "button pressed"
        #pos = (pygame.mouse.get_pos() [0], pygame.mouse.get_pos() [1])
        pos = (int((pygame.mouse.get_pos()[0] + MouseOffset[0]) * MouseFactor[0]),
               int((pygame.mouse.get_pos()[1] + MouseOffset[1]) * MouseFactor[1]) )
        # print pos  # for checking
        # The actual mouse position is absolutely irrelevant at the moment.
        PB.CD()  # First picture
        PB.CD()  # second picture
        PB.CD()  # third picture
        PB.CD()  # fourth picture
        combine()   # and combine them into one...
        for event in pygame.event.get():
            # empty the queue, in case someone touched the screen during the last photo-session
            pass

        # Update all pictures list
        UpdateAllPicturesList()
	
	# Overlay the last QR-Code to preview
	PB.qroverlay()

        # Reset the DiaShow-Counter
        DiashowTimerCounter = 0
    else:
        DiashowTimerCounter += 1    # increment Timer-Counter
        time.sleep(0.1)
        if DiashowTimerCounter > 120:
            # Start Diashow after 12s
            if DiashowTimerCounter % 40 == 0:
                # Change picture every 4s
                PB.diashow()
