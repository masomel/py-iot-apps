# msm: source - https://www.hackster.io/archieroques/iot-tweeting-plants-with-raspberry-pi-f99da2

#imports the time module (used for waiting)
import time
#imports the datetime module (used to get the current mintue)
from datetime import datetime
#imports all parts of the envirophat module
from envirophat import *
#imports the OS module, which we use for executing the command to take the picture
import os

#blinks leds to show working
leds.on()
time.sleep(1)
leds.off()

def SetupTweepy():
    #this imports the tweepy module (twitter for python)
    import tweepy
    #this sets up all the variables tweepy needs to use
    consumer_key = 'yours_goes_here'
    consumer_secret = 'yours_goes_here'
    access_token = 'yours_goes_here'
    access_token_secret = 'yours_goes_here'
    #this runs the authentication process
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    #this allows us to tweet from within a different function
    global api
    api = tweepy.API(auth)
    #lets us know it's all running well
    print("Tweepy Setup Done!")

def TweetText(texttotweet, medialoc):
    #tells us if we've asked it to tweet something to big, to avoid tweepy errors
    if len(texttotweet) > 144:
        print("text too long for a tweet!")
        return False
    else:
        #this actually tweets the text
        api.update_with_media(medialoc, status=texttotweet)
        #tells us what it's tweeted
        print(" \" %s \" tweeted!" % (texttotweet))
        return True

def TweetConditions(addlmessage):
    #sets up an empty variable for the text to tweet to be stored in
    tweet = str()
    #adds the additional text (like motion detected)
    tweet += addlmessage
    #adds the light level to the tweet
    tweet += ("Light level: " + str(light.light()))
    #adds the temperature
    tweet += (", Temperature: " + str(round(weather.temperature(), 1)) + " C")
    #adds the pressure
    tweet += (", Pressure: " + str(round(weather.pressure(), 0)) + " hPa")
    '''If you want to add additional analogue sensors connected
    to the analogue header on the Enviro pHAT, then add this line:
    tweet += ("<<your value name here>>: " + your_analog_value_here)
    You will need to map your value from between 0 and 3.3v to a
    value that people will understand (like degrees C for example)
    more info on this in Pimoroni's tutorial, at learn.pimoroni.com'''

    #executes a command line command to take a picture
    os.system("cd Desktop\nsudo fswebcam image.jpg")
    #sleep for half a min to give it time to do all its picturey stuff
    time.sleep(30)

    #sets the media variable to the location of the media
    media = "/home/pi/Desktop/image.jpg"
    #sends this to the function that sends and checks the tweet
    TweetText(tweet, media)

#sets all needed variables to initial values:
#the threshold for detecting whether something was moved (change this if it seems
#to be moved all the time)
threshold = 0.3
#an empty list to store acceleroneter values in
readings = []
#defaults the last Z reading to 0
last_z = 0
#sets up minutes as a global so it can be accessed anywhere
global mins
#sets minutes to the current mintue
mins = (datetime.now().strftime('%M'))
#defaults motion detected to false
motiondetected = False
#splits the RGB values into 3 separate variables
r, g, b = light.rgb()

#runs the tweepy setup code
SetupTweepy()

#do the following forever
while True:
    #if it's at one of the 15 minute intervals:
    if mins == "00" or mins == "15" or mins == "30" or mins == "45":
        print(("Reached an interval:, ", mins))
        #if it has been moved, add that to the tweet and send it
        if motiondetected:
            TweetConditions("Ow! Someone moved me! ")
        #if the temp is above 32C, then add that to the tweet and send it
        elif (round(weather.temperature(), 1)) > 32:
            TweetConditions("Woah - it's hot in here! ")
        #if the blue light is greater than all others, add that to the tweet and send it
        elif b > r and b > g:
            TweetConditions("There seems to be a lot of blue light at the moment. ")
        #if the red light is greater than all others, add that to the tweet and send it
        elif r > b and r > g:
            TweetConditions("There seems to be a lot of red light at the moment. ")
        #if the green light is greater than all others, add that to the tweet and send it
        elif g > r and g > b:
            TweetConditions("There seems to be a lot of green light at the moment. ")
        #if nothing notable has happened, just send a plain old tweet
        else:
            TweetConditions("")
        #wait a minute to avoid more than one tweet going out
        time.sleep(61)
        #update the minutes again to avoid a neverending loop
        mins = "1"
        mins = (datetime.now().strftime('%M'))
        #reset motiondetected back to false
        motiondetected = False
    #if it's not time to tweet:
    else:
        #this next part is adapted from Pimoroni's example. It detects if the plants were disturbed.
        readings.append(motion.accelerometer().z)
        readings = readings[-4:]
        z = sum(readings) / len(readings)
        if last_z > 0 and abs(z-last_z) > threshold:
            motiondetected = True
        last_z = z
        time.sleep(0.01)
        #updates the RGB light values
        r, g, b = light.rgb()
        #sets minutes to the current mintue
        mins = (datetime.now().strftime('%M'))
