#http://www.rototron.info/dht22-tutorial-for-raspberry-pi/
#https://github.com/adafruit/Adafruit_Python_DHT


import Adafruit_DHT as dht
h,t = dht.read_retry(dht.DHT22, 26)
print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(t, h))
