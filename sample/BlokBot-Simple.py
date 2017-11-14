# msm: source - https://www.thingiverse.com/thing:1706105/#files

import subprocess, os, sys, unirest, time
from espeak import espeak
a1 = "arecord -d 5 -D plughw:1,0 -r 16000 -f S16_LE /home/pi/apps/sample/sample.wav"
print ("Recording Voice")
subprocess.call(a1,shell= True)
print ("Done")

response = unirest.post("https://api.wit.ai/speech?v=20160526",
headers={
"Authorization": "Bearer JIAK5Q5KOHEBZEBREPDLVM3ILPGNJYFE",
"Content-Type": "audio/wav",
"Content-Length": "100000",
},
params=(

     open("/home/pi/apps/sample/sample.wav")
)
)
#time.sleep(2)
print" ===========after sleep"
print str(response.code)
print"response.code"
print str(response.headers)
print" response.headers"
print str(response.body)
x = str(response.body)
print" response.body"
print str(response.raw_body)
o = str(response.raw_body)
print"raw"
import re
p = re.compile(ur'"_text" : "(?s)(.*)",')
t = re.search(p, o)
t = t.group(1)
print t

espeak.synth(t)
time.sleep(2)
