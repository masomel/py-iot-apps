# msm: source - https://hackaday.io/project/11688-iot-twitter-sentry-ward-using-intel-edison

import tweepy
import cv2
import urllib.request, urllib.parse, urllib.error
import time
import mraa

consumer_key = "YOUR KEY HERE"
consumer_secret = "YOUR KEY HERE"
access_token = "YOUR TOKEN HERE"
access_token_secret = "YOUR TOKEN HERE"
your_handle = "ENTER YOUR TWITTER HANDLE HERE"
camip = "YOUR CAMERA IP HERE"

chk_old=0

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
imag = urllib.request.URLopener()
light = mraa.Aio(0)

tweet = tweepy.Cursor(api.search, q = your_handle , lang = 'en')
count = 0
for tweet in list(tweet.items()):
	print((tweet.text, tweet.author.screen_name,tweet.id))
	txt = tweet.text
	hand = tweet.author.screen_name
	chk = tweet.id
	cond = chk_old!=chk
	print(cond)
	break
if txt== your_handle + ' Start!':
	print('Security System Started!')
	while count<1:
		tweet = tweepy.Cursor(api.search, q = '@satyasiot', lang = 'en')
		count = 2
		val = float(light.read())
		print(val)
		if val > 500:  
			if cond:
				imag.retrieve('http://'+camip+':8080/shot.jpg','shot.jpg')
				img = cv2.imread('shot.jpg')
				time.sleep(3)
				this = '/home/root/shot.jpg'
				psts = '@satyasiot Intruder Alert!'
				api.update_with_media(filename=this, in_reply_to_status_id=chk, status=psts)
				chk_old = chk
				print(chk_old)
				print('done')
		time.sleep(11)
		for tweet in list(tweet.items()):
			txt = tweet.text
			hand = tweet.author.screen_name
			chk = tweet.id
