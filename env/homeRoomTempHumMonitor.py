# msm: source - http://www.instructables.com/id/Home-Room-Temprature-and-Humidity-Monitor-with-Web/?ALLSTEPS

import RPi.GPIO as GPIO
import time
import httplib, json

def bin2dec(string_num):
    return str(int(string_num, 2))

data = []

GPIO.setmode(GPIO.BCM)

GPIO.setup(4,GPIO.OUT)
GPIO.output(4,GPIO.HIGH)
time.sleep(0.025)
GPIO.output(4,GPIO.LOW)
time.sleep(0.02)

GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

for i in range(0,500):
    data.append(GPIO.input(4))

bit_count = 0
tmp = 0
count = 0
HumidityBit = ""
TemperatureBit = ""
crc = ""

try:
	while data[count] == 1:
		tmp = 1
		count = count + 1

	for i in range(0, 32):
		bit_count = 0

		while data[count] == 0:
			tmp = 1
			count = count + 1

		while data[count] == 1:
			bit_count = bit_count + 1
			count = count + 1

		if bit_count > 3:
			if i>=0 and i<8:
				HumidityBit = HumidityBit + "1"
			if i>=16 and i<24:
				TemperatureBit = TemperatureBit + "1"
		else:
			if i>=0 and i<8:
				HumidityBit = HumidityBit + "0"
			if i>=16 and i<24:
				TemperatureBit = TemperatureBit + "0"

except:
	print "ERR_RANGE"
	exit(0)

try:
	for i in range(0, 8):
		bit_count = 0

		while data[count] == 0:
			tmp = 1
			count = count + 1

		while data[count] == 1:
			bit_count = bit_count + 1
			count = count + 1

		if bit_count > 3:
			crc = crc + "1"
		else:
			crc = crc + "0"
except:
	#print "ERR_RANGE"
	headers = { "charset" : "utf-8", "Content-Type": "application/json" }
	conn = httplib.HTTPConnection("104.236.91.122")
        sample_1 = { "nodata" : no_data }
	sampleJson_1 = json.dumps(sample_1, ensure_ascii = 'False')
	   
	conn.request("POST", "/rpi/rpi.php", sampleJson_1, headers)
	response = conn.getresponse()
	print(response.read())
        conn.close() 
	exit(0)   

Humidity = bin2dec(HumidityBit)
Temperature = bin2dec(TemperatureBit)

if int(Humidity) + int(Temperature) - int(bin2dec(crc)) == 0:

	#Sending the data to the server
    headers = { "charset" : "utf-8", "Content-Type": "application/json" }
    conn = httplib.HTTPConnection("104.236.91.122")
    sample = { "humidity" : Humidity, "temperature" : Temperature }
    sampleJson = json.dumps(sample, ensure_ascii = 'False')
   
    conn.request("POST", "/rpi/rpi.php", sampleJson, headers)
    response = conn.getresponse()
    print(response.read())
    conn.close() 

else:
	print "ERR_CRC"
