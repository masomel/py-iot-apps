import wolframalpha
import sys
import os.path
import subprocess


# Get a free API key here http://products.wolframalpha.com/api/
# This is a fake ID, go and get your own, instructions on my blog.
app_id = "<WolframAlpha Key>"
client = wolframalpha.Client(app_id)
query = " ".join(sys.argv[1:])
res = client.query(query)

def execute_unix(inputcommand):
   p = subprocess.Popen(inputcommand, stdout=subprocess.PIPE, shell=True)
   (output, err) = p.communicate()
   return output



#os.system("espeak  -s 125 -a 200 -p 90 -f 'Sorry, I am not sure.' --stdout | aplay")
if len(res.pods) > 0:
	texts = ""
	pod = res.pods[1]
	if pod.text:
		texts = pod.text
	else:
		texts = "I have no answer for that"
		# to skip ascii character in case of error
	texts = texts.encode('ascii', 'ignore')
	print (texts)
#	espeak  -s 125 -a 200 -p 90 -f texts --stdout | aplay
else:
	texts = "Sorry, I am not sure."
#	espeak  -s 125 -a 200 -p 90 -f "Sorry, I am not sure." --stdout | aplay

# speak aloud
c = 'espeak -ven+m5 -k5 -s160 -a200 -p90 --punct="<characters>" "%s" 2>>/dev/null' % texts #speak aloud
execute_unix(c)
