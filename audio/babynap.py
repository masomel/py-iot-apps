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
        print("Connected to the AWS IoT service!")
    else :
        print(("Error connecting to AWS IoT service! (Error code " + str(rc) + ": " + RESULT_CODES[rc] + ")"))
        client.disconnect()

#Connect to AWS IoT
client = mqtt.Client(client_id="odroid-c1", protocol=mqtt.MQTTv311)
client.on_connect = on_connect
client.tls_set("certs/root-CA.crt", certfile="certs/certificate.pem.crt", keyfile="certs/private.pem.key", tls_version=ssl.PROTOCOL_SSLv23, ciphers=None)
client.tls_insecure_set(True)
client.connect("A32L40P6IYKK8W.iot.us-east-1.amazonaws.com", 8883, 60)
client.loop_start()

# GPIO pin setup
wpi.wiringPiSetup()
wpi.pinMode(2, 0) # PIR sensor on wpi GPIO2
wpi.pinMode(3, 0) # mat pressure sensor on wpi GPIO3
wpi.pinMode(21, 0) # sound sensor GATE on wpi GPIO21

# I2C TSL2561 setup
tsl = TSL2561(0x39,"/dev/i2c-1")
tsl.enable_autogain()
tsl.set_time(0x00)

# nfc functions
def connected(tag):
    global nfcid
    nfcid = str(tag)[12:]
    print("read successful")
    time.sleep(3)
    return False

def reader():
    while True:
        # we do a read every 5s
        timeout = lambda: time.time() - started > 5
        started = time.time()
        device = nfc.ContactlessFrontend('tty:S2:pn532')
        device.connect(rdwr={'on-connect': connected}, terminate=timeout)
        device.close()
        

nfcid = 0
thread = threading.Thread(target=reader)
thread.start()
# end nfc setup

count = 0
mlux = mpir = mmat = msound = mvolume = 0

while True:
    time.sleep(3)
    # read sensor data
    ts = int(time.time())
    lux = tsl.lux()
    pir = wpi.digitalRead(2)
    mat = wpi.digitalRead(3)
    sound = wpi.digitalRead(21)
    volume = wpi.analogRead(0)*255/2047 # 0-10=quiet, 10-30=moderate, 30-127=loud

    mom = 0
    dad = 0
    if mat == 0:
        if nfcid == 'F10B330F':
            mom = 1
        elif nfcid == '833BC4A2':
            dad = 1

    if lux > mlux:
        mlux = lux
    if pir > mpir:
        mpir = pir
    if mat < mmat:
        mmat = mat
    if sound > msound:
        msound = sound
    if volume > mvolume:
        mvolume = volume

    # send data to AWS
    if count == 0:
        msg = {'ts': ts, 'lux': mlux, 'pir': mpir, 'mat': mmat, 'sound': msound, 'volume': mvolume, 'mom': mom, 'dad': dad}
        print(json.dumps(msg))
        client.publish('sensors', json.dumps(msg))
        mlux = mpir = mmat = msound = mvolume = 0
        if mmat == 1:
            nfcid = 0
thread = threading.Thread(target=reader)
thread.start()
# end nfc setup

count = 0
mlux = mpir = mmat = msound = mvolume = 0

while True:
    time.sleep(3)
    # read sensor data
    ts = int(time.time())
    lux = tsl.lux()
    pir = wpi.digitalRead(2)
    mat = wpi.digitalRead(3)
    sound = wpi.digitalRead(21)
    volume = wpi.analogRead(0)*255/2047 # 0-10=quiet, 10-30=moderate, 30-127=loud

    mom = 0
    dad = 0
    if mat == 0:
        if nfcid == 'F10B330F':
            mom = 1
        elif nfcid == '833BC4A2':
            dad = 1

    if lux > mlux:
        mlux = lux
    if pir > mpir:
        mpir = pir
    if mat < mmat:
        mmat = mat
    if sound > msound:
        msound = sound
    if volume > mvolume:
        mvolume = volume

    # send data to AWS
    if count == 0:
        msg = {'ts': ts, 'lux': mlux, 'pir': mpir, 'mat': mmat, 'sound': msound, 'volume': mvolume, 'mom': mom, 'dad': dad}
        print(json.dumps(msg))
        client.publish('sensors', json.dumps(msg))
        mlux = mpir = mmat = msound = mvolume = 0
        if mmat == 1:
            nfcid = 0
    count = (count + 1) % 20
