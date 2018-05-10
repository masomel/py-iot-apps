# msm: source - https://www.hackster.io/phantom-formula-e97912/network-monitoring-with-aws-iot-b8b57c?ref=search&ref_id=IoT%20python&offset=18

'''
Network Monitoring with AWS IoT
Copyright (C) 2016 Louis Tam

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import json
import ssl
import time
import subprocess
import os
import paho.mqtt.client as mqtt

devicecert = "/root/key/a1a97c3bfe-certificate.pem.crt"
devicekey = "/root/key/a1a97c3bfe-private.pem.key"
servercert = "/root/key/root-CA.crt"
server = "A3UTD0DHSM47I.iot.us-west-2.amazonaws.com"
topic="$aws/things/netmon1/shadow/update"
mac = 'YOUR PC MAC ADDRESS'
qos=0
retain=False

def powerup():
    print(("send magic packet to "+mac))
    subprocess.Popen(["wakeonlan", mac])
    time.sleep(1)
    subprocess.Popen(["wakeonlan", mac])
    time.sleep(1)
    subprocess.Popen(["wakeonlan", mac])
    #Assume target is waken
    return 1

def powerdown():
    print ("Power down PC")
    p = subprocess.Popen(["arp","-a"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output, errors = p.communicate()
    output=output.decode()
    output=output.splitlines()
    
    for i in range(len(output)):
        if mac in str(output[i]):
            a = output[i].split('(', 1 )
            a = a[1].split(')',1)
            ip = a[0]
    subprocess.Popen(["net", "rpc", "shutdown", "-I", ip, "-U", "user%pass"]) #For Windows PC, configure the actual username/password here
    return 1

def scan():
    print ("Scan subnet now")
    subprocess.Popen(["fping", "-c", "1", "-g", "192.168.1.0/24"]) #Configure the actual subnet of network
    time.sleep(20)
    p = subprocess.Popen(['arp','-a'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output, errors = p.communicate()
    output=output.decode()
    print (output)
    output=output.splitlines()
    print((len(output)))
    return "Active IP: " + str(len(output))

def checkspeed(index):
    print ("check network traffic")
    p = subprocess.Popen(["snmpwalk","-v2c","-c","public","192.168.1.1",".1.3.6.1.2.1.2.2.1.10"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output, errors = p.communicate()
    time.sleep(1)
    output=output.decode()
    output=output.splitlines()
    a = [0] * len(output)
    for i in range(len(output)):
        a[i] = output[i].split(' = Counter32: ', 1 )

    time.sleep(5)
    p = subprocess.Popen(["snmpwalk","-v2c","-c","public","192.168.1.1",".1.3.6.1.2.1.2.2.1.10"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output, errors = p.communicate()
    time.sleep(1)
    output=output.decode()
    output=output.splitlines()
    b = [0] * len(output)
    c = [0] * len(output)
    for i in range(len(output)):
        b[i] = output[i].split(' = Counter32: ', 1 )
    for i in range(len(a)):
        c[i] = int((((int(b[i][1])-int(a[i][1]))*8*100)/(5*100)))
        print((c[i]))
    return c
    
def monspeed():
    c = checkspeed(-1)
    if c[2] > 2000000: # customize the interface/speed to trigger the warning
        awsmsg = {'state':{ 'reported': {'warning': 'speed' , 'result': c}}}
        payload = json.dumps(awsmsg)
        print (awsmsg)
        client.publish(topic,payload,qos,retain)

def status():
    print ("report status")
    p = subprocess.Popen(["uptime"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output, errors = p.communicate()
    output=output.decode()
    output=output.split(',', 1 )
    return output[0]

def on_message(client, userdata, msg):
    print(("Message: " + msg.topic + " Payload:" + str(msg.payload)))
    if "timestamp" in str(msg.payload):
        return;
    if "request" not in str(msg.payload):
        return;
    print ("Process message")
    if "powerup" in str(msg.payload):
        ret = powerup()
        awsmsg = {'state':{ 'reported': {'action': 'powerup' , 'result': ret}}}
    if "powerdown" in str(msg.payload):
        ret = powerdown()
        awsmsg = {'state':{ 'reported': {'action': 'powerdown' , 'result': ret}}}
    if "status" in str(msg.payload):
        ret = status()
        awsmsg = {'state':{ 'reported': {'action': 'status' , 'result': ret}}}
    if "scan" in str(msg.payload):
        ret = scan()
        awsmsg = {'state':{ 'reported': {'action': 'scan' , 'result': ret}}}
    if "speed" in str(msg.payload):
        c = checkspeed(-1)
        awsmsg = {'state':{ 'reported': {'action': 'scan' , 'result': c}}}
    payload = json.dumps(awsmsg)
    print (awsmsg)
    client.publish(topic, payload, qos, retain)

def on_log(client, userdata, level, msg):
    print(("Log: " + msg))

def on_connect(client, userdata, flags, rc):
    client.subscribe("$aws/things/netmon1/#")

client = mqtt.Client("netmon1")
client.on_connect = on_connect
client.on_message = on_message
client.on_log = on_log
client.tls_set(servercert, devicecert, devicekey, ssl.CERT_REQUIRED, ssl.PROTOCOL_SSLv23)
client.connect(server, 8883, 60)

client.loop_start()

awsmsg = {'state':{ 'reported': {'powerup': 1 }}} #update on power up
payload = json.dumps(awsmsg)
client.publish(topic, payload ,qos, retain)

while True:
    monspeed()
