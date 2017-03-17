import socket
import mraa
import sys
import time

TCP_IP = ""
TCP_PORT = 5005
BUFFER_SIZE = 1024
MESSAGE = "Edison Here"
hum = mraa.Aio(0)
lig = mraa.Aio(1)

humval = int(hum.read())
ligval = int(lig.read())

time.sleep(10)

while(1):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))

    humval = int(hum.read())
    humval = str(humval)
    print "Temperature : "+humval
    sendis = "Temperature/"+humval
    bytes = str.encode(sendis)
    s.send(bytes)
    time.sleep(2)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))
    ligval = int(lig.read())
    ligval = str(ligval)
    print "Light : "+ligval
    sendis = "Light/"+ligval
    bytes = str.encode(sendis)
    s.send(bytes)

    print ("Done!")
    print (" ")
    time.sleep(60)
