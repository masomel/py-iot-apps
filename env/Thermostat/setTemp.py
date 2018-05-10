#!/usr/bin/python

import sys, getopt
import sqlite3
import time

def setTempNeeded(degree):
	try:
		conn=sqlite3.connect('/home/pi/temperature/temperature.db')
		curs=conn.cursor()
		curs.execute("replace into tempneed values(1,"+ degree +")")
		conn.commit()
		conn.close()
	except:
		conn.close()
		raise
def main(argv):
	temperature = ''
	try:
		opts, args = getopt.getopt(argv,"h:t:",["temperature="])
   	except getopt.GetoptError:
         	print('usage: setTemp.py -t <temperatureNeeded>')
      		sys.exit(2)
   	for opt, arg in opts:
      		if opt == '-h':
         		print('usage: setTemp.py -t <temperatureNeeded>')
         		sys.exit()
      		elif opt in ("-t", "--temperature"):
         		temperature = arg
   	#print 'temperature needed is ' + temperature
	if temperature:
		try:
			setTempNeeded(temperature)
		except:
			time.sleep(10)
			print('retry')
			setTempNeeded(temperature)

if __name__ == "__main__":
   	main(sys.argv[1:])
