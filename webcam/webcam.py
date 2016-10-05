# Takes a picture with a connected USB webcam

import tracer
import os

def take_pic():
    #executes a command line command to take a picture
    os.system("fswebcam --no-banner -r 640x480 image.jpg")

tracer.start_tracer(take_pic)
