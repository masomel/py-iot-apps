#http://www.rototron.info/dht22-tutorial-for-raspberry-pi/
#https://github.com/adafruit/Adafruit_Python_DHT


import Adafruit_DHT as dht
from time import sleep
from time import strftime
from datetime import *


def writeLogFile():
    f = open (("/home/pi/salena/data/DHT22-test.csv"),"a")
    # st = d.strftime("%d/%m/%Y %I:%M:%S %p") #date time AM/PM
    st = d.strftime("%d/%m/%Y %H:%M:%S,")      #date time 24 Hour
    st += "{0:0.1f},{1:0.1f},".format(t1,h1)  
    st += "{0:0.1f},{1:0.1f},".format(t2,h2)
    st += "{0:0.1f},{1:0.1f},".format(t3,h3)
    st += "{0:0.1f},{1:0.1f},".format(t4,h4)
    st += "{0:0.1f},{1:0.1f},".format(t5,h5)
    st += "\n"
    f.write (st) 
    f.close ()



while True:

    print  datetime.today().strftime("%d/%m/%Y %H:%M:%S") 
    
    h1,t1 = dht.read_retry(dht.DHT22, 5) #D1
    print 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(t1, h1)
    h2,t2 = dht.read_retry(dht.DHT22, 6) #D2
##    h3,t3 = dht.read_retry(dht.DHT22, 13)
##    h4,t4 = dht.read_retry(dht.DHT22, 19)
##    h5,t5 = dht.read_retry(dht.DHT22, 26)
##    print  d.strftime("%d/%m/%Y %H:%M:%S")      #date time 24 Hour

    print 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(t2, h2)
##    print 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(t3, h3)
##    print 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(t4, h4)
##    print 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(t5, h5)
    print '\n'
    
#    writeLogFile()
    
    sleep(5)
