ReSpeaker Messenger: Sending and receiving Slack and Telegram messages using ReSpeaker Voice Interaction Board
===

My previous project using ReSpeaker was a Home Automation project to control different lights using your voice. This projects is about sending messages to Slack or Telegram using voice input and read out the message from the messenger. User can touch button 1 to send Slack message and touch button 7 to send Telegram message. For Telegram message, first you need to initiate the chat from Telegram client. This is because to send a message to Telegram you need the `userid` of the receiving person.

How it works
--
This project uses [Slack](https://slack.com/), [Telegram](https://telegram.org/), [MQTT](http://mqtt.org/), [hook.io](http://hook.io/) and [ReSpeaker](http://respeaker.io/). 

In case of Slack messenger, We set an Outgoing Webhook to a *hook.io* microservice written in Node.js. This Node.js script receives the text and publish MQTT message with a specified topic. The Python script running on ReSpeaker subscribe this topic and upon receiving this message, the text is converted to audio using Microsoft Cognitive Computing Text to Speech API. This is read out uinsg PyAudio. 

In case of Telegram, the ReSpeaker python application use [Telepot](https://github.com/nickoala/telepot) Python library to integrate Telegram API. Whenever a message is received the text is send to Microsoft Cognitive Service API and the receiving audio is played using PyAudio.

We have two applications running on the ReSpeaker, on Arduino Sketch and Python script. The Arduino Sketch receives touch event and send to the Python Script using Serial to start recording the voice input. When the start recording message is received, the script records the user's voice input and convert to text using Microsoft Cognitive Service Speech to Text API and send to the corresponding messenger depending on the touch button id. If the button touched is 1 then send to Slack messenger and if the touch button id is 7 then to Telegram messenger. Telepot library is used to send to Telegram messenger. For Slack, we have created a Slack Incoming Webhook. Below picture depicts working of the application.

![application diagram](https://raw.githubusercontent.com/krvarma/respeaker-messenger/master/images/app.png)

How to communicate from Arduino to Python
--
As you know ReSpeaker has two UART connections, "*serial*" and "*serial1*". The serial is connected to the USB port. The serial1 can be used to communicate from Arduino to the Python script. The serial1 is connected to the UART_RXD2 and UART_TXD2 of MT7688. So you can just open the Serial port `/dev/ttyS2` and read the incoming data. The following test script opens the `/dev/ttyS2` port and reads strings (*Thanks to Jerry of Seeedstudio for suggesting this*). 

    import serial
	import io
    
    port = '/dev/ttyS2'
    baud = 57600
    
    ser = serial.Serial(port, baud, timeout=1)
    sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
    
    if ser.isOpen():
    	print(ser.name + ' is open...')
    
    while True:
    	serialdata = sio.readline()
    	print(serialdata)

Setting up ReSpeaker
-
Follow [this document](https://github.com/respeaker/get_started_with_respeaker/wiki) to get started with ReSpeaker

How to use the application
-
1. Open Arduino IDE and load [this file](https://github.com/krvarma/respeaker-messenger/blob/master/arduino/detecttouch.ino)
2. Connect your ReSpeaker to the network
3. SSH to your ReSpeaker
4. Create a folder to clone the project files
5. Move to the folder and clone the repo https://github.com/krvarma/respeaker-messenger.git
6. Got to `respeaker-messenger` folder
7. Create an account or log on to Microsoft Cognitive Service Speech API](https://www.microsoft.com/cognitive-services/en-us/speech-api)
8. Get an API Key and replace the variable BING_KEY in the Python Script `Settings.py`
9. Log on to [Slack.com](https://slack.com/), go to Settings->Add and app or integrations
10. Go to Manage->Custom Integrations->Incoming Webhook. Create Incoming Webhook and copy the URL
11. Replace the variable SLACK_WEBHOOK in the Python Script `Settings.py`
12. Go to Slack->Manage->Custom Integrations->Incoming Webhook and create Outgoing Webhook. Copy the Token
13. Log on to [hook.io](https://hook.io/) and create a new hook
14. Copy the contents of [this file](https://github.com/krvarma/respeaker-messenger/blob/master/microservice/slack-to-mqtt.js) to the hook
15. Replace the [access_token](https://github.com/krvarma/respeaker-messenger/blob/master/microservice/slack-to-mqtt.js#L6)
16. Log on to [Telegram.org](https://telegram.org/) and create a new bot following [this instructions](https://core.telegram.org/bots#create-a-new-bot)
17. Copy the token and replace the variable TELEGRAM_KEY in the Python Script `Settings.py`
18. Install required Python package paho-mqtt using pip install paho-mqtt
19. Install required Python package paho-mqtt using pip install telepot
20. Install required Python package monotonic using pip install monotonic
21. Run `messenger.py` using command line python `messenger.py`
22. Open Telegram client application and send a simple 'hi' to any user, this will receive at the ReSpeaker end and the `userid` will be saved for sending future messages. This step is necessary because to send a message to Telegram, you need the *userid* of the user to whom you want to send the message.
23. Touch the button 1 to send to messages to Slack and touch button 7 to send messages to Telegram.
24. You can also send messages from Slack to the specified channel using the specified trigger work, this will be send to ReSpeaker and it will read out the text

If everything goes well, you have a working ReSpeaker Messenger and you can send messages using your voice. The application will read out the messages send from Slack or Telegram.

Demo Video
-
**Slack Messenger**
https://www.youtube.com/watch?v=Q7amXfVdt4k

**Telegram Messenger**
https://www.youtube.com/watch?v=_FrRhzkRTGc

