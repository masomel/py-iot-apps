#!/usr/bin/env python
# encoding: utf-8
"""
lego-robot
This code was adapted from RyanTeks example scripts
https://github.com/ryanteck
"""
from sys import exit
import RPi.GPIO as GPIO
import time
import keys
from pubnub import Pubnub

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(17,GPIO.OUT)
GPIO.setup(18,GPIO.OUT)
GPIO.setup(22,GPIO.OUT)
GPIO.setup(23,GPIO.OUT)
GPIO.setup(21,GPIO.OUT)
GPIO.setup(20,GPIO.OUT)

def right():
        GPIO.output(17,1)
        GPIO.output(18,0)
        GPIO.output(22,1)
        GPIO.output(23,0)

def left():
        GPIO.output(17,0)
        GPIO.output(18,1)
        GPIO.output(22,0)
        GPIO.output(23,1)

def forwards():
        GPIO.output(17,0)
        GPIO.output(18,1)
        GPIO.output(22,1)
        GPIO.output(23,0)

def backwards():
        GPIO.output(17,1)
        GPIO.output(18,0)
        GPIO.output(22,0)
        GPIO.output(23,1)

def stop():
        GPIO.output(17,0)
        GPIO.output(18,0)
        GPIO.output(22,0)
        GPIO.output(23,0)
def lightOn():
	GPIO.output(21, True)
        GPIO.output(20, True)
def lightOff():
	GPIO.output(21, False)
        GPIO.output(20, False)

pubnub = Pubnub(publish_key=keys.PUBLISH, subscribe_key=keys.SUBSCRIBE)

def callback(message, channel):
    print(message['move'])
    if message['move'] == 'forwards':
        forwards()
    elif message['move'] == 'backwards':
        backwards()
    elif message['move'] == 'left':
        left()
    elif message['move'] == 'right':
        right()
    elif message['move'] == 'nudge-left':
        left()
        time.sleep(0.1)
        stop()
    elif message['move'] == 'nudge-right':
        right()
        time.sleep(0.1)
        stop()
    elif message['move'] == 'stop':
        stop()
    elif message['move'] == 'lightOn':
	lightOn()
    elif message['move'] == 'lightOff':
	lightOff()
    else:
        stop()

def error(message):
    print("ERROR : " + str(message))


def connect(message):
    print("CONNECTED")
    print pubnub.publish(channel='my_channel', message='Hello from the PubNub Python SDK')



def reconnect(message):
    print("RECONNECTED")


def disconnect(message):
    print("DISCONNECTED")


pubnub.subscribe(channels=keys.CHANNEL, callback=callback, error=callback,
                 connect=connect, reconnect=reconnect, disconnect=disconnect)

try:
    while 1:
        pass
except KeyboardInterrupt:
    GPIO.cleanup()
    sys.exit(1)
