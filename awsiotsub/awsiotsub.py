# this source is part of my Hackster.io project:  https://www.hackster.io/mariocannistra/radio-astronomy-with-rtl-sdr-raspberrypi-and-amazon-aws-iot-45b617

# use this program to test the AWS IoT certificates received by the author
# to participate to the spectrogram sharing initiative on AWS cloud

# this program will subscribe and show all the messages sent by its companion
# awsiotpub.py using the AWS IoT hub

import tracer
import paho.mqtt.client as paho
import os
import socket
import ssl

def on_connect(client, userdata, flags, rc):
    print("Connection returned result: " + str(rc) )
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("#" , 1 )

def on_message(client, userdata, msg):
    print("topic: "+msg.topic)
    print("payload: "+str(msg.payload))

#def on_log(client, userdata, level, msg):
#    print(msg.topic+" "+str(msg.payload))

def sub():
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

tracer.start_tracer(sub)
