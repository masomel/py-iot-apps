import pyaudio
import webrtcvad
import collections
import sys
import serial
import signal
import time
import telepot

import paho.mqtt.client as mqtt
from pprint import pprint
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from bing_voice import *
from player import Player
from settings import BING_KEY
from settings import TELEGRAM_KEY
from settings import SLACK_WEBHOOK
from settings import MQTT_SERVER

port = '/dev/ttyS2'
baud = 57600

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK_DURATION_MS = 30  # supports 10, 20 and 30 (ms)
PADDING_DURATION_MS = 1000
CHUNK_SIZE = int(RATE * CHUNK_DURATION_MS / 1000)
CHUNK_BYTES = CHUNK_SIZE * 2
NUM_PADDING_CHUNKS = int(PADDING_DURATION_MS / CHUNK_DURATION_MS)
NUM_WINDOW_CHUNKS = int(240 / CHUNK_DURATION_MS)

vad = webrtcvad.Vad(2)
pa = pyaudio.PyAudio()
player = Player(pa)
bing = BingVoice(BING_KEY)

stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, start=False, frames_per_buffer=CHUNK_SIZE)
got_a_sentence = False
leave = False
got_trigger = False
got_message = False
trigger_word_found = False
messenger = 1
telegramid = 0

ser = serial.Serial(port, baud, timeout=1)
sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
bot = telepot.Bot(TELEGRAM_KEY)

if ser.isOpen():
	print((ser.name + ' is open...'))

def handle_int(sig, chunk):
	global leave, got_a_sentence, got_message
    
	leave = True
	got_a_sentence = True
	got_message = False
    
signal.signal(signal.SIGINT, handle_int)

def on_connect(client, userdata, flags, rc):
	print(("Connected with result code "+str(rc)))

	client.subscribe("respeaker/slack/text")
	
def on_message(client, userdata, msg):
	global got_message
	
	print((msg.topic+" "+str(msg.payload)))
	
	got_message = True
	
	payload = json.loads(msg.payload)
	tts_data = bing.synthesize(payload["text"])
	player.play_raw(tts_data)
	
	got_message = False
	
def handleText(msg):
	global telegramid

	#payload = json.loads(msg)
	
	if telegramid == 0:
		telegramid = msg['from']['id']
		
	pprint(msg)
	print(telegramid)
	
	tts_data = bing.synthesize(msg["text"])
	player.play_raw(tts_data)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("iot.eclipse.org", 1883, 60)
client.loop_start()

bot.message_loop(handleText)
updates = bot.getUpdates()

pprint(updates)

while not leave:
	serialdata = sio.readline()
	messenger = 0
		
	if len(serialdata) > 0:
		serialdata = serialdata.replace('\n', '')
		
		print(serialdata)
		
		tokens = serialdata.split('=')
		
		print((tokens[0]))
		print((tokens[1]))
		
		if tokens[0] == 'start-recording':
			print('Touch start')
			got_message = True
			
			if tokens[1] == '0':
				messenger = 1
			elif tokens[1] == '7':
				messenger = 2
		else:
			got_message = False
	else:
		got_message = False
	
	if not got_message:
		continue
	
	ring_buffer = collections.deque(maxlen=NUM_PADDING_CHUNKS)
	triggered = False
	voiced_frames = []
	ring_buffer_flags = [0] * NUM_WINDOW_CHUNKS
	ring_buffer_index = 0
	buffer_in = ''
    
	print("* recording")
	stream.start_stream()
	while not got_a_sentence and not leave:
		chunk = stream.read(CHUNK_SIZE)
		active = vad.is_speech(chunk, RATE)
		sys.stdout.write('1' if active else '0')
		ring_buffer_flags[ring_buffer_index] = 1 if active else 0
		ring_buffer_index += 1
		ring_buffer_index %= NUM_WINDOW_CHUNKS
		if not triggered:
			ring_buffer.append(chunk)
			num_voiced = sum(ring_buffer_flags)
			if num_voiced > 0.5 * NUM_WINDOW_CHUNKS:
				sys.stdout.write('+')
				triggered = True
				voiced_frames.extend(ring_buffer)
				ring_buffer.clear()
		else:
			voiced_frames.append(chunk)
			ring_buffer.append(chunk)
			num_unvoiced = NUM_WINDOW_CHUNKS - sum(ring_buffer_flags)
			if num_unvoiced > 0.9 * NUM_WINDOW_CHUNKS:
				sys.stdout.write('-')
				triggered = False
				got_a_sentence = True

		sys.stdout.flush()

	sys.stdout.write('\n')
	data = b''.join(voiced_frames)
    
	stream.stop_stream()
	print("* done recording")
	
	if not got_message:
		print('Not start message')
		continue

	# recognize speech using Microsoft Bing Voice Recognition
	try:
		text = bing.recognize(data, language='en-US')
		
		if "header" in text and "lexical" in text["header"]:
			recognizedText = text["header"]["lexical"]
			
			print(recognizedText)
			
			print(messenger)

			if messenger == 1:
				print('Send Slack message')
				
				payload = json.dumps({
					"text": recognizedText
				})
		
				request = Request(SLACK_WEBHOOK, data = payload, headers = {
					"Content-Type": "application/json"
				})
	
				try:
					response = urlopen(request)
				except HTTPError as e:
					raise RequestError("recognition request failed: {0}".format(e.reason))
				except URLError as e:
					raise RequestError("recognition connection failed: {0}".format(e.reason))
		
				response_text = response.read().decode("utf-8")
		
				print(response_text);
			elif messenger == 2:
				print('Send Telegram message')
				
				bot.sendMessage(telegramid, recognizedText)
		
			got_message = False
			trigger_word_found = False
		else:
			print('Cannot recognize audio')
			
		serialdata = '';
			
	except UnknownValueError:
		print("Microsoft Bing Voice Recognition could not understand audio")
	except RequestError as e:
		print(("Could not request results from Microsoft Bing Voice Recognition service; {0}".format(e)))
        
	got_a_sentence = False
        
sio.close()
ser.close()
client.loop_stop()
stream.close()