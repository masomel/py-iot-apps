# this source is part of my Hackster.io project:  https://www.hackster.io/mariocannistra/radio-astronomy-with-rtl-sdr-raspberrypi-and-amazon-aws-iot-45b617

# use this program to test the AWS IoT certificates received by the author
# to participate to the spectrogram sharing initiative on AWS cloud

# this program will publish test mqtt messages using the AWS IoT hub
# to test this program you have to run first its companion awsiotsub.py
# that will subscribe and show all the messages sent by this program

import tracer
import paho.mqtt.client as paho
import os
import socket
import ssl
from random import uniform

connflag = False

def on_connect(client, userdata, flags, rc):
    global connflag
    connflag = True
    print("Connection returned result: " + str(rc) )

def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

#def on_log(client, userdata, level, buf):
#    print(msg.topic+" "+str(msg.payload))

def pub():
    mqttc = paho.Client()
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    #mqttc.on_log = on_log

    awshost = "a1vs5y6cjuptwy.iot.us-east-1.amazonaws.com"
    awsport = 8443
    clientId = "thingy"
    thingName = "thingy"
    caPath = "apps/aws-iot-rootCA.crt"
    certPath = "apps/cert.pem"
    keyPath = "apps/privkey.pem"

    mqttc.tls_set(caPath, certfile=certPath, keyfile=keyPath, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

    mqttc.connect(awshost, awsport, keepalive=60)

    mqttc.loop_start()

    if connflag == True:
        tempreading = uniform(20.0,25.0)
        mqttc.publish("temperature", tempreading, qos=1)
        print("msg sent: temperature "+ "%.2f" % tempreading )
    else:
        print("no connection...")

tracer.start_tracer(pub)
