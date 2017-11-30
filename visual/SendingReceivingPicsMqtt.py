# msm: source - https://developer.ibm.com/recipes/tutorials/sending-and-receiving-pictures-from-a-raspberry-pi-via-mqtt/

import picamera
from time import sleep

camera = picamera.PiCamera()

try: 
    camera.start_preview()
    sleep(1)
    camera.capture('image_test.jpg', resize=(500,281))
    camera.stop_preview()
    pass
finally:
    camera.close()
 
import base64

def convertImageToBase64():
    with open("image_test.jpg", "rb") as image_file:
        encoded = base64.b64encode(image_file.read())
    return encoded
 
import ibmiotf.device

options = ibmiotf.device.ParseConfigFile("/home/pi/device2.cfg")
client = ibmiotf.device.Client(options)
client.connect()

import random, string

def randomword(length):
    return ''.join(random.choice(string.lowercase) for i in range(length))
 
import math

packet_size=3000

def publishEncodedImage(encoded): 
    end = packet_size
    start = 0
    length = len(encoded)
    picId = randomword(8)
    pos = 0
    no_of_packets = math.ceil(length/packet_size)
 
    while start <= len(encoded):
        data = {"data": encoded[start:end], "pic_id":picId, "pos": pos, "size": no_of_packets}
        client.publishEvent("Image-Data",json.JSONEncoder().encode(data))
        end += packet_size
        start += packet_size
        pos = pos +1
