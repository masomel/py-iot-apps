# msm: source - http://www.instructables.com/id/Twitter-Photo-Live-Feed/?ALLSTEPS

#!/usr/bin/env python2.7

import tweepy
import time
import random
from subprocess import call
from datetime import datetime

#These are the phrases variables that will be sent with the tweet
tweet = ['A tweet from my pi  ', 'Hello!  ']

while True:

        #time and date for filename
        i = datetime.now()               
        now = i.strftime('%Y%m%d-%H%M%S')
        photo_name = now + '.jpg'
        #creates command and destination for photo
        cmd = 'raspistill -t 500 -w 1024 -h 768 -o /tmp/' + photo_name
        #shoot the photo
        call ([cmd], shell=True)         

        # Replace each with the keys and tokens from your twitter app
        consumer_key = ''
        consumer_secret = ''
        access_token = ''
        access_token_secret = ''

        # OAuth process, using the keys and tokens
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

        # Creation of the actual interface, using authentication
        api = tweepy.API(auth)

        # Send photo to destination
        photo_path = '/tmp/' + photo_name
        # Tweet text
        status = (random.choice(tweet)) +  i.strftime('%Y/%m/%d %H:%M:%S')
         # Send the tweet with photo
        api.update_with_media(photo_path, status=status)

        #How many seconds before the script runs again
        time.sleep(900)
