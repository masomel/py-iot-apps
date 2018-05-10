import io
import os.path
import pycurl
import time
import sys
import subprocess

def execute_unix(inputcommand):
   p = subprocess.Popen(inputcommand, stdout=subprocess.PIPE, shell=True)
   (output, err) = p.communicate()
   return output

while True:
#variables
	filename = 'talkingganesha.flac'
	key = '<GoogleKey>'
	url = 'https://www.google.com/speech-api/v2/recognize?output=json&lang=en-us&key=' + key

#Listen to question and save it into file
	
	texts = "You can ask me any question now ?"
	c = 'espeak -vhi+m5 -k6 -s160 -a200 -p90 --punct="<characters>" "%s" 2>>/dev/null' % texts #speak aloud
	execute_unix(c)

	os.system("./stt.sh")


#send the file to google speech api
	c = pycurl.Curl()
	c.setopt(pycurl.VERBOSE, 0)
	c.setopt(pycurl.URL, url)
	fout = io.StringIO()
	c.setopt(pycurl.WRITEFUNCTION, fout.write)

	c.setopt(pycurl.POST, 1)
	c.setopt(pycurl.HTTPHEADER, [
      	          'Content-Type: audio/x-flac; rate=16000'])

	filesize = os.path.getsize(filename)
	c.setopt(pycurl.POSTFIELDSIZE, filesize)
	fin = open(filename, 'rb')
	c.setopt(pycurl.READFUNCTION, fin.read)
	c.perform()

	response_code = c.getinfo(pycurl.RESPONSE_CODE)
	response_data = fout.getvalue()

#since google replies with mutliple json strings, the built in python json decoders dont work well
	start_loc = response_data.find("transcript")
	tempstr = response_data[start_loc+13:]
	end_loc = tempstr.find("\"")
	final_result = tempstr[:end_loc]

	c.close()


	print("You Said:" + final_result)
	d = 'espeak -vhi+m5 -k5 -s160 -a200 -p90 --punct="<characters>" "%s" 2>>/dev/null' % final_result #speak aloud
	execute_unix(d)
#	final_result="Who is God Shiva?"
#part 2

	os.system("python queryProcess.py '" + final_result + "'")
	time.sleep(5);