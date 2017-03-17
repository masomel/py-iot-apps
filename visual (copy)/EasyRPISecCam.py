# msm: source - http://www.instructables.com/id/Easy-Raspberry-Pi-Security-Cam-With-Automatic-Web-/?ALLSTEPS

import requests
import picamera
import os
import os.path
import time
from datetime import datetime 

# ----------------------- globals variables-----------------------

# ----Image Extension is JPG by default ----
gImgExt="jpg"

# ---- Number of images to be displayed at one time on the web gallery ----
gImgCount=6

# ---- Program Development/Production Mode ----
# To run program in debug mode, set  gDebugMode =1
# Make sure to have a file named sample_image.jpg in the same folder as the Watcher.py program
# Once testing is complete, set this flag to 0
gDebugMode=1

# ---- Program Execution Mode ----
# Instead of using the cron scheduler, you can run this program in an endless loop
# Set gRunMode to a value other than "single" to enable the endless loop
# Pros: You can skip the entire Crontab scheduling part
# Cons: You have to start the Watcher.py program manually each time you restart your Pi or make changes to it
# CAUTION: To run using Cron, set the gRunMode back to "single"
gRunMode="single"

# ---- Marker File ----
# This file will be created in the same folder as Watcher.py 
# If connection to the internet fails, the name of the last image captured by the
# camera will be written to this file. No more images will be captured until the
# image is successfully uploaded the next time internet connectivity is restored
gLogFile="0.txt"

# ---- Web API Service ----
# When gDebugMode is set to 1, the program looks for an API service on your local machine
# The gAccessKey key can be anything you want it to be, but the API service must also have an identical key!
# When Web APIs uplod method will not accept upload if no access key is provided with the image file

gUrl="http://your_web_service.com/"
gBizUrl="http://your_web_service.com/api/upload"
gAccessKey ="a-very-long-and-gibberish-key-must-be-set-here"


if(gDebugMode==1):
    gUrl="http://your_local_computer_name:port_number/Home/"
    gBizUrl="http://your_local_computer_name:port_number/api/upload/"
    

# ---- function to test internet connection ----
# note! this is a function to check for net connectivity
# and not for a valid domain. This function will still return
# success if an invalid url is specified.

def checkConnection():
    try:
        resp = requests.get(gUrl)
        return resp.status_code        
    except:
         return -1


# ---- function to upload the file to the remote server ----
# ---- The accessKey set above will need to be added to the upload request --
def UploadFile(imgFileNm,url):
    f = open (imgFileNm,'rb')
    textData = {'caption': imgFileNm, 'accessKey': gAccessKey, 'imgCount':gImgCount}
    resp = requests.post(url = url, files =  {'file':f}, data = textData)
    if(gDebugMode==1):
        print resp.text
    return resp.status_code

# ---- function to write to a local log file  ----
def WriteToLog(imageFileNm,logFileNm,erase):
    lf=open(logFileNm,'w')
    if(erase):
        lf.truncate()
    lf.write(imageFileNm)
    lf.close()

# ---- function to read from a local log file  ----
# ---- limitation: file contains one line with just the image name --
def ReadLog(logFileNm):
    lf=open(logFileNm)
    fn=lf.read()
    lf.close()
    return fn


# ---- function to read from a local log file  ----
def DeleteFile(fileNm):
    if(os.path.isfile(fileNm)):
        os.remove(fileNm)

# ---- function to build image file name  ----
# ---- name of the file will be in the current date-time stamp
# ---- the remote API service contains logic to use the file name to identify
# ---- the time the image was captured by the camera and display it as a caption
# ---- under the corresponding image in the web gallery

def BuildFileNm(fileExt):
    today = datetime.now()
    fileNm=str(today.month)+"_"+str(today.day)+"_"+str(today.year)+ "__" + \
            str(today.hour)+"_"+str(today.minute)+"_"+str(today.second)+"_"+str(today.microsecond)
    return "{0}.{1}".format(fileNm,fileExt)

# ---- function to check for a fle --
def FileExists(fileNm):
    if(os.path.isfile(fileNm)):
        return 1
    else:
        return 0


# -- the main function --
def main():
    
    #   activate the camera
    camera = picamera.PiCamera()
    #   forever loop - this loop will break after the first run if program is set to "single" mode as described above
    while(1==1):
        imgFileNm=""
        if(FileExists(gLogFile)==0):
            #   last upload succeeded | generate new image file name | capture new image with the pi camera
            imgFileNm=BuildFileNm(gImgExt)
            #   to avoid triggering the camera during testing, simply upload an image from the local folder
            if(gDebugMode==1):
                imgFileNm="sample_image.jpg"
            else:
                print("picam will capture an image named {0}".format(imgFileNm))
                camera.capture(imgFileNm)
        else:
            #   last upload failed | read image name from file | a file with this name should exist when it was captured last time
            imgFileNm=ReadLog(gLogFile)
            if(gDebugMode==1):
                print("name of image captured last time is {0}".format(imgFileNm))


        #   check internet connection before attempting upload
        if (checkConnection() == 200):
            print("Success! Connected to Internet, proceeding to upload...")
            #   upload image to web api
            r = UploadFile(imgFileNm,gBizUrl)
            if(r==200):
                #   upload successful - delete marker file but retain image if debugging for testing next time
                print("Upload Success! purging local image...")
                DeleteFile(gLogFile)
                if(gDebugMode==0):
                    DeleteFile(imgFileNm)
            else:
                #  upload failed - cache current image to marker file
                WriteToLog(imgFileNm,gLogFile,1)
        else:
            print("Fail! No connection, service unavailable or incorrect service URL")
            #   cache image to log | don't capture image until the last image has been uploaded successfully
            WriteToLog(imgFileNm,gLogFile,1)
            print("Local image saved to log file...will be uploaded next time internet or service is available")

        #   Exit program if execution is set to single mode 
        if(gRunMode=="single"):
            break

    #   release camera resources before exit
    camera.close()
                                
    

# -- execute main function --
main()
