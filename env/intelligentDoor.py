# msm: source - https://www.hackster.io/vijayenthiran/intelligent-door-e59113?ref=search&ref_id=home%20security%20python&offset=5

from adxl345 import ADXL345
import time
import paho.mqtt.client as mqtt #make sure you have installed mqtt client library for python
import ssl
import json
import thread

#Creating a adxl345 object
adxl345 = ADXL345()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))


client = mqtt.Client()
client.on_connect = on_connect
client.tls_set(ca_certs='./cert/rootCA.pem', certfile='./cert/503a755ca4-certificate.pem.crt', keyfile='./cert/503a755ca4-private.pem.key', tls_version=ssl.PROTOCOL_SSLv23)
client.tls_insecure_set(True)
client.connect("AAAAAAAAAAAAAA.iot.us-west-2.amazonaws.com", 8883, 60) #Taken from REST API endpoint - Use your own.


def intrusionDetector(Dummy):
    while (1):
        #Enable Acccelerometer
        axes = adxl345.getAxes(True)
        #I did few expriment in certain orientation and found that when ever door opens the Z axis value becomes positive.
        if axes['z'] >= 0:
            print "Intruder Detected"
            client.publish("home/door", payload="Intruder Detected" , qos=0, retain=False)
        time.sleep(0.5)

thread.start_new_thread(intrusionDetector,("Create intrusion Thread",))

client.loop_forever() #MQTT's will never end
