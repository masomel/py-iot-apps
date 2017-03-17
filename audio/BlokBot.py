# msm: source - https://www.thingiverse.com/thing:1706105/#files

import subprocess, os, sys, unirest, time
from espeak import espeak 
a1 = "arecord -d 5 -D plughw:1,0 -r 16000 -f S16_LE sample.wav"
print ("Recording Voice")
subprocess.call(a1,shell= True)
print ("Done")
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
time.sleep(0.2)
# Raspberry Pi pin configuration:
RST = 24
# Note the following are only used with SPI:
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0
# 128x64 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)

# Initialize library.
disp.begin()

# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = 2
shape_width = 20
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = padding
# Draw an ellipse.



# Load default font.
font = ImageFont.load_default()

# Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
#font = ImageFont.truetype('Minecraftia.ttf', 8)
#-*- coding: utf-8 -*-
# Write two lines of text.
draw.text((x, top),    '(-.-)zz',  font=ImageFont.truetype('/usr/share/fonts/truetype/roboto/Roboto-Bold.ttf', 40), fill=255)
#draw.text((x, top+20), 'World!', font=font, fill=255)
# Display image.
disp.image(image)
disp.display()

response = unirest.post("https://api.wit.ai/speech?v=20160526",
headers={
"Authorization": "Bearer JIAK5Q5KOHEBZEBREPDLVM3ILPGNJYFE",
"Content-Type": "audio/wav",
"Content-Length": "100000",    
},
params=(
    
     open("/home/pi/Downloads/sample.wav")
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



# Initialize library.
#disp.begin()
#disp.clear()
#disp.display()
width = disp.width
height = disp.height
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)
draw.rectangle((0,0,width,height), outline=0, fill=0)
padding = 2
shape_width = 20
top = padding
bottom = height-padding
x = padding
font = ImageFont.load_default()
# Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
#font = ImageFont.truetype('Minecraftia.ttf', 8)
#-*- coding: utf-8 -*-
# Write two lines of text.
draw.text((x, top),    '(O.O)',  font=ImageFont.truetype('/usr/share/fonts/truetype/roboto/Roboto-Bold.ttf', 40), fill=255)
#draw.text((x, top+20), 'World!', font=font, fill=255)
# Display image.
disp.image(image)
disp.display()


espeak.synth(t)
time.sleep(2)
width = disp.width
height = disp.height
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)
draw.rectangle((0,0,width,height), outline=0, fill=0)
padding = 2
shape_width = 20
top = padding
bottom = height-padding
x = padding
font = ImageFont.load_default()
# Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
#font = ImageFont.truetype('Minecraftia.ttf', 8)
#-*- coding: utf-8 -*-
# Write two lines of text.
draw.text((x, top),    '(-.-)Zz',  font=ImageFont.truetype('/usr/share/fonts/truetype/roboto/Roboto-Bold.ttf', 40), fill=255)
#draw.text((x, top+20), 'World!', font=font, fill=255)
# Display image.
disp.image(image)
disp.display()
