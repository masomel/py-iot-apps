#adapted from https://www.hackster.io/archieroques/iot-tweeting-plants-w-raspberry-pi-f99da2

import tracer

#imports the time module (used for waiting)
import time
#imports the datetime module (used to get the current mintue)
from datetime import datetime

def SetupTweepy():
    #this imports the tweepy module (twitter for python)
    import tweepy
    #this sets up all the variables tweepy needs to use
    consumer_key = '123'
    consumer_secret = '123'
    access_token = '123'
    access_token_secret = '123'
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
        return True

def TweetPic(addlmessage):
    #sets up an empty variable for the text to tweet to be stored in
    tweet = str()
    #adds the additional text (like motion detected)
    tweet += addlmessage

    #sets the media variable to the location of the media
    media = "apps/tweetpic/image.jpg"    
    #sends this to the function that sends and checks the tweet
    TweetText(tweet, media)

def send_tweet():
    SetupTweepy()
    TweetPic("hello")

tracer.start_trace(send_tweet)


    
