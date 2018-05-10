#! /usr/bin/env python

import os
import time
import RPi.GPIO as GPIO
import alsaaudio
from creds import *
import requests
import json
from memcache import Client
import vlc
import email
import sys
import datetime
import webrtcvad

#Settings
button = 26         # GPIO Pin with button connected
plb_light = 6        # GPIO Pin for the playback light
act_light = 13        # GPIO Pin for the activity light
rec_light = 19        # GPIO Pin for the recording light
device = "plughw:1" # Name of your microphone/sound card in arecord -L
debug = True

#Set the GPIO for the LEDs and the button
GPIO.setmode(GPIO.BCM)

GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(plb_light, GPIO.OUT)
GPIO.output(plb_light, GPIO.LOW)

GPIO.setup(act_light, GPIO.OUT)
GPIO.output(act_light, GPIO.LOW)

# The red LED (recording) is set to PWM as I want 2 grades in light; 20% for recording, 100% for recognizing voice
rec_dim = 20         # the brightness of the LED in dimmed mode
GPIO.setup(rec_light, GPIO.OUT)
rec_light_pwm = GPIO.PWM(rec_light, 100)    # create object for PWM at 100 Hertz  
rec_light_pwm.start(1) #Start very dim to show that Alexa is awake


#Setup Alexa
recorded = False
servers = ["127.0.0.1:11211"]
mc = Client(servers, debug=1)
path = os.path.realpath(__file__).rstrip(os.path.basename(__file__))

#Variables
p = ""
position = 0
audioplaying = False
button_pressed = False
start = time.time()
vad = webrtcvad.Vad(2)
currVolume = 100

# constants 
VAD_SAMPLERATE = 16000
VAD_FRAME_MS = 30
VAD_PERIOD = (VAD_SAMPLERATE / 1000) * VAD_FRAME_MS
VAD_SILENCE_TIMEOUT = 1000
MAX_RECORDING_LENGTH = 8 

#Colors for logging
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def internet_on():
    print("Checking Internet Connection...")
    try:
        r =requests.get('https://api.amazon.com/auth/o2/token')
        print(("Connection {}OK{}".format(bcolors.OKGREEN, bcolors.ENDC)))
        return True
    except:
        print(("Connection {}Failed{}".format(bcolors.WARNING, bcolors.ENDC)))
        return False

def gettoken():
    token = mc.get("access_token")
    refresh = refresh_token
    if token:
        return token
    elif refresh:
        payload = {"client_id" : Client_ID, "client_secret" : Client_Secret, "refresh_token" : refresh, "grant_type" : "refresh_token", }
        url = "https://api.amazon.com/auth/o2/token"
        r = requests.post(url, data = payload)
        resp = json.loads(r.text)
        mc.set("access_token", resp['access_token'], 3570)
        return resp['access_token']
    else:
        return False

def alexa_speech_recognizer():
    # https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/rest/speechrecognizer-requests
    GPIO.output(act_light, GPIO.HIGH)
    if debug: print(("{}Sending Speech Request...{}".format(bcolors.OKBLUE, bcolors.ENDC)))
    url = 'https://access-alexa-na.amazon.com/v1/avs/speechrecognizer/recognize'
    headers = {'Authorization' : 'Bearer %s' % gettoken()}
    d = {
        "messageHeader": {
            "deviceContext": [
                {
                    "name": "playbackState",
                    "namespace": "AudioPlayer",
                    "payload": {
                    "streamId": "",
                        "offsetInMilliseconds": "0",
                        "playerActivity": "IDLE"
                    }
                }
            ]
        },
        "messageBody": {
            "profile": "alexa-close-talk",
            "locale": "en-us",
            "format": "audio/L16; rate=16000; channels=1"
        }
    }
    with open(path+'recording.wav') as inf:
        files = [
                ('file', ('request', json.dumps(d), 'application/json; charset=UTF-8')),
                ('file', ('audio', inf, 'audio/L16; rate=16000; channels=1'))
                ]
        r = requests.post(url, headers=headers, files=files)
    GPIO.output(act_light, GPIO.LOW)
    process_response(r)
    

def alexa_playback_progress_report_request(requestType, playerActivity, streamid):
    # https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/rest/audioplayer-events-requests
    # streamId                  Specifies the identifier for the current stream.
    # offsetInMilliseconds      Specifies the current position in the track, in milliseconds.
    # playerActivity            IDLE, PAUSED, or PLAYING
    if debug: print(("{}Sending Playback Progress Report Request...{}".format(bcolors.OKBLUE, bcolors.ENDC)))
    headers = {'Authorization' : 'Bearer %s' % gettoken()}
    d = {
        "messageHeader": {},
        "messageBody": {
            "playbackState": {
                "streamId": streamid,
                "offsetInMilliseconds": 0,
                "playerActivity": playerActivity.upper()
            }
        }
    }
    
    if requestType.upper() == "ERROR":
        # The Playback Error method sends a notification to AVS that the audio player has experienced an issue during playback.
        url = "https://access-alexa-na.amazon.com/v1/avs/audioplayer/playbackError"
    elif requestType.upper() ==  "FINISHED":
        # The Playback Finished method sends a notification to AVS that the audio player has completed playback.
        url = "https://access-alexa-na.amazon.com/v1/avs/audioplayer/playbackFinished"
    elif requestType.upper() ==  "IDLE":
        # The Playback Idle method sends a notification to AVS that the audio player has reached the end of the playlist.
        url = "https://access-alexa-na.amazon.com/v1/avs/audioplayer/playbackIdle"
    elif requestType.upper() ==  "INTERRUPTED":
        # The Playback Interrupted method sends a notification to AVS that the audio player has been interrupted. 
        # Note: The audio player may have been interrupted by a previous stop Directive.
        url = "https://access-alexa-na.amazon.com/v1/avs/audioplayer/playbackInterrupted"
    elif requestType.upper() ==  "PROGRESS_REPORT":
        # The Playback Progress Report method sends a notification to AVS with the current state of the audio player.
        url = "https://access-alexa-na.amazon.com/v1/avs/audioplayer/playbackProgressReport"
    elif requestType.upper() ==  "STARTED":
        # The Playback Started method sends a notification to AVS that the audio player has started playing.
        url = "https://access-alexa-na.amazon.com/v1/avs/audioplayer/playbackStarted"
    
    r = requests.post(url, headers=headers, data=json.dumps(d))
    if r.status_code != 204:
        print(("{}(alexa_playback_progress_report_request Response){} {}".format(bcolors.WARNING, bcolors.ENDC, r)))
    else:
        if debug: print(("{}Playback Progress Report was {}Successful!{}".format(bcolors.OKBLUE, bcolors.OKGREEN, bcolors.ENDC)))

def process_response(r):
    global currVolume, isMute
    if debug: print(("{}Processing Request Response...{}".format(bcolors.OKBLUE, bcolors.ENDC)))
    if r.status_code == 200:
        data = "Content-Type: " + r.headers['content-type'] +'\r\n\r\n'+ r.content
        msg = email.message_from_string(data)        
        for payload in msg.get_payload():
            if payload.get_content_type() == "application/json":
                j =  json.loads(payload.get_payload())
                if debug: print(("{}JSON String Returned:{} {}".format(bcolors.OKBLUE, bcolors.ENDC, json.dumps(j))))
            elif payload.get_content_type() == "audio/mpeg":
                filename = path + "tmpcontent/"+payload.get('Content-ID').strip("<>")+".mp3" 
                with open(filename, 'wb') as f:
                    f.write(payload.get_payload())
            else:
                if debug: print(("{}NEW CONTENT TYPE RETURNED: {} {}".format(bcolors.WARNING, bcolors.ENDC, payload.get_content_type())))
        
        # Now process the response
        if 'directives' in j['messageBody']:
            if len(j['messageBody']['directives']) == 0:
                if debug: print("0 Directives received")
                for x in range(0, 3):
                    time.sleep(.1)
                    GPIO.output(act_light, GPIO.HIGH)
                    time.sleep(.1)
                    GPIO.output(act_light, GPIO.LOW)
            for directive in j['messageBody']['directives']:
                if directive['namespace'] == 'SpeechSynthesizer':
                    if directive['name'] == 'speak':
                        GPIO.output(plb_light, GPIO.HIGH)
                        play_audio(path + "tmpcontent/"+directive['payload']['audioContent'].lstrip("cid:")+".mp3")
                        GPIO.output(plb_light, GPIO.LOW)
                    for directive in j['messageBody']['directives']: # if Alexa expects a response
                        if directive['namespace'] == 'SpeechRecognizer': # this is included in the same string as above if a response was expected
                            if directive['name'] == 'listen':
                                if debug: print(("{}Further Input Expected, timeout in: {} {}ms".format(bcolors.OKBLUE, bcolors.ENDC, directive['payload']['timeoutIntervalInMillis'])))

                                #play_audio(path+'audio/sound_beep.wav', 0, 100)
                                timeout = directive['payload']['timeoutIntervalInMillis']/116
                                # listen until the timeout from Alexa
                                silence_listener(timeout)
                                # now process the response
                                alexa_speech_recognizer()
        return
    elif r.status_code == 204:
        GPIO.output(rec_light, GPIO.LOW)
        for x in range(0, 3):
            time.sleep(.2)
            GPIO.output(plb_light, GPIO.HIGH)
            time.sleep(.2)
            GPIO.output(plb_light, GPIO.LOW)
        if debug: print(("{}Request Response is null {}(This is OKAY!){}".format(bcolors.OKBLUE, bcolors.OKGREEN, bcolors.ENDC)))
    else:
        print(("{}(process_response Error){} Status Code: {}".format(bcolors.WARNING, bcolors.ENDC, r.status_code)))
        r.connection.close()
        GPIO.output(lights, GPIO.LOW)
        for x in range(0, 3):
            time.sleep(.2)
            GPIO.output(rec_light, GPIO.HIGH)
            time.sleep(.2)
            GPIO.output(lights, GPIO.LOW)

def play_audio(file, offset=0, overRideVolume=0):
    global currVolume
    global p, audioplaying
    k = file.rfind("/") #find the start of the filename from the full path
    new_file = file[k+1:] #filname only
    if debug: print(("{}Play_Audio Request for:{} {}".format(bcolors.OKBLUE, bcolors.ENDC, new_file)))
    i = vlc.Instance('--aout=alsa') # , '--alsa-audio-device=mono', '--file-logging', '--logfile=vlc-log.txt')
    m = i.media_new(file)
    p = i.media_player_new()
    p.set_media(m)
    mm = m.event_manager()
    mm.event_attach(vlc.EventType.MediaStateChanged, state_callback, p)
    audioplaying = True
    if (overRideVolume == 0):
        p.audio_set_volume(currVolume)
    else:
        p.audio_set_volume(overRideVolume)
    p.play()
    while audioplaying:
        continue


def state_callback(event, player):
    global nav_token, audioplaying, streamurl, streamid
    state = player.get_state()
    #0: 'NothingSpecial'
    #1: 'Opening'
    #2: 'Buffering'
    #3: 'Playing'
    #4: 'Paused'
    #5: 'Stopped'
    #6: 'Ended'
    #7: 'Error'
    #if debug: print("{}Player State:{} {}".format(bcolors.OKGREEN, bcolors.ENDC, state))
    if state == 5:    #Stopped
        audioplaying = False
    elif state == 6:    #Ended
        audioplaying = False
    elif state == 7:
        audioplaying = False


def detect_button(channel):
    global button_pressed
    button_pressed = True
    if debug: print(("{}Button Pressed!{}".format(bcolors.OKBLUE, bcolors.ENDC)))
    time.sleep(.5) # time for the button input to settle down
    while (GPIO.input(button)==0): #button seems to still be pressed
        button_pressed = True
        time.sleep(.1)
    button_pressed = False
    time.sleep(.5) # more time for the button to settle down
        
def silence_listener(MaxRecordingLength):
    global rec_light_pwm

    rec_light_pwm.ChangeDutyCycle(rec_dim)
    print(("{}Recording...{}".format(bcolors.OKBLUE, bcolors.ENDC)))
    play_audio(path+"audio/sound_start.mp3")

    # Reenable reading microphone raw data
    inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, device)
    inp.setchannels(1)
    inp.setrate(VAD_SAMPLERATE)
    inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
    inp.setperiodsize(VAD_PERIOD)
    audio = ""

    # Buffer as long as we haven't heard enough silence or the total size is within max size
    thresholdSilenceMet = False
    frames = 0
    numSilenceRuns = 0
    silenceRun = 0
    start = time.time()
    isSpeech = False

    # Use VAD to find out when the user STARTS talking
    while (isSpeech == False and ((time.time() - start) < MaxRecordingLength)):
        l, data = inp.read()
        if l:
            isSpeech = vad.is_speech(data, VAD_SAMPLERATE)
            if (isSpeech == True):
                audio += data
                rec_light_pwm.ChangeDutyCycle(100)
            else:
                rec_light_pwm.ChangeDutyCycle(rec_dim)


    # now do VAD to find when the user STOPS talking
    while ((thresholdSilenceMet == False) and ((time.time() - start) < MaxRecordingLength)):
        l, data = inp.read()
        if l:
            audio += data

            if (l == VAD_PERIOD):
                isSpeech = vad.is_speech(data, VAD_SAMPLERATE)

                if (isSpeech == False):
                    silenceRun = silenceRun + 1
                    rec_light_pwm.ChangeDutyCycle(rec_dim)
                else:
                    silenceRun = 0
                    numSilenceRuns = numSilenceRuns + 1
                    rec_light_pwm.ChangeDutyCycle(100)

        # only count silence runs after the first one 
        # (allow user to speak for total of max recording length if they haven't said anything yet)
        if (numSilenceRuns != 0) and ((silenceRun * VAD_FRAME_MS) > VAD_SILENCE_TIMEOUT):
            thresholdSilenceMet = True


    # User stopped talking, save record
    rf = open(path+'recording.wav', 'w')
    rf.write(audio)
    rf.close()
    inp.close()

    print(("{}Recording Finished.{}".format(bcolors.OKBLUE, bcolors.ENDC)))
    play_audio(path+"audio/sound_stop.mp3")
    rec_light_pwm.ChangeDutyCycle(0)


def start():
    global audioplaying, p, vad, button_pressed
    GPIO.add_event_detect(button, GPIO.FALLING, callback=detect_button, bouncetime=100) # threaded detection of button press

    while True:
        record_audio = False

        while record_audio == False:
            time.sleep(.1)

            if button_pressed:
                if audioplaying: p.stop()
                record_audio = True

        silence_listener(MAX_RECORDING_LENGTH) # start listener and wait for a silence
        alexa_speech_recognizer() # then process to Alexa
        


def setup():
    while internet_on() == False:
        print(".")
    token = gettoken()
    if token == False:
        while True:
            for x in range(0, 5):
                time.sleep(.1)
                GPIO.output(act_light, GPIO.HIGH)
                time.sleep(.1)
                GPIO.output(act_light, GPIO.LOW)

    for x in range(0, 5):
        time.sleep(.1)

        GPIO.output(plb_light, GPIO.HIGH)
        GPIO.output(act_light, GPIO.HIGH)
        rec_light_pwm.ChangeDutyCycle(100)
        time.sleep(.1)

        GPIO.output(plb_light, GPIO.LOW)
        GPIO.output(act_light, GPIO.LOW)
        rec_light_pwm.ChangeDutyCycle(rec_dim)

    rec_light_pwm.ChangeDutyCycle(0)
    play_audio(path+"audio/alexa_hello.mp3")


if __name__ == '__main__':
    try:
        print('AlexaPi started, Press Ctrl-C to quit.')
        setup()
        start()
    finally:
        rec_light_pwm.stop()
        GPIO.cleanup()
        if debug == False: os.system("rm "+path+"tmpcontent/*")
        print('AlexaPi stopped.')

