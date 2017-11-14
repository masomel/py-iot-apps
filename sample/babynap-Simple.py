# msm: source - https://www.hackster.io/memeka/baby-nap-night-activity-program-aa5ab0?ref=search&ref_id=IoT%20python&offset=19

#!/usr/bin/python
import paho.mqtt.client  as mqtt
import paho.mqtt.publish as publish
import time,json,ssl
import wiringpi2 as wpi
from tentacle_pi.TSL2561 import TSL2561
import nfc, sys, threading

def on_connect(mqttc, obj, flags, rc):
    if rc == 0:
        print "Connected to the AWS IoT service!"
    else :
        print("Error connecting to AWS IoT service! (Error code " + str(rc) + ": " + RESULT_CODES[rc] + ")")
        client.disconnect()

#Connect to AWS IoT
client = mqtt.Client(client_id="odroid-c1", protocol=mqtt.MQTTv311)
client.on_connect = on_connect
client.tls_set("certs/root-CA.crt", certfile="certs/certificate.pem.crt", keyfile="certs/private.pem.key", tls_version=ssl.PROTOCOL_SSLv23, ciphers=None)
client.tls_insecure_set(True)
client.connect("A32L40P6IYKK8W.iot.us-east-1.amazonaws.com", 8883, 60)
client.loop_start()

count = 0
msound = mvolume = 0

for x in range (0, 100):
    time.sleep(3)
    # read sensor data
    ts = int(time.time())
    sound = wpi.digitalRead(21)
    volume = wpi.analogRead(0)*255/2047 # 0-10=quiet, 10-30=moderate, 30-127=loud
    if sound > msound:
        msound = sound
    if volume > mvolume:
        mvolume = volume

    # send data to AWS
    if count == 0:
        msg = {'sound': msound, 'volume': mvolume}
        print json.dumps(msg)
        client.publish('sensors', json.dumps(msg))
        msound = mvolume = 0
