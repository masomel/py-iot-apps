# lego-robot
This is the software required to build a lego robot with a webcam that streams over HTTP.
Full instructions are here [on the instructables website](http://www.instructables.com/id/Dog-Bot-Lego-Robot-Rover-With-Webcam/)

## Available Controllers
| Controller 			| Description 		                                    |
| --------------- | --------------------------------------------------- |
| Button  				| click the buttons to control dogbot  	              |
| Joystick        | touch joystick, nice to use on a tablet             |
| voice  		      | voice control, speak commands and watch dogbot move |



## Hardware

* Raspberry Pi model B+ (although earlier versions should work)
* Ryanteck RTK-000-001 Motor Controller Board
* Motor Robot Car chassis kit with Speed encoder (bought from Amazon)
* Recharge battery pack for power source
* 4 AA batteries for motor power
* Lots of bits of Lego form my sons lego sets and some from my old lego set


## Software
* PubNub realtime infrastructure-as-a-service
* Raspbian Jessie
* Python
* Javascript virtual joystick



## Installation on Raspian Jessie

* sudo apt-get update
* sudo apt-get install motion
* sudo apt-get install python-dev python-pip
* sudo pip install 'pubnub>=3,<4'
* git clone https://github.com/petekaras/lego-robot.git into your home directory

## Configure motion
### /etc/motion/motion.conf


| Property  			        | value   |
| ----------------------- | ------- |
| daemon  				        | on  		|
| ffmpeg_output_movies    | off  		|
| output_pictures  		    | off  	  |
| stream_maxrate		      | 30			|
| width					          | 480			|
| height				          | 360			|

You can vary the `stream_maxrate` to increase the quality of the video. Also play around with the width and height settings.

### /etc/default/motion

| Property  			      | value 		|
| --------------------- | --------- |
| start_motion_daemon  	| yes  			|

## auto run services on start up
add the following lines to `\etc\rc.local`

```
#Robot starts webcam
sudo motion

#Robot listens to commands
nohup sudo python /home/pi/lego-robot/server/robot.py &
```
## Creating a disk image
Find the name of the device of the plugged in SD-card, by typing:

`ls -la /dev/sd*`

plug and unplug the USB reader to find out which device to use. Now write the image:

`sudo dd if=2016-02-26-raspbian-jessie.img of=/dev/sdb`

Might take a while over USB 2.

##Connect with TTL serial cable
I used this to connect up to a newly installed Raspian OS, and set up the wifi. Saves having to connect up keyboard, mouse and screen.
The wires of the cable should be connected like this:

| Wire color | GPIO		|
| -----------| ------ |
| red 		   | 5V		  |
| black  	   | GND  	|
| white  	   | 14  		|
| green  	   | 15  		|

Install screen

`sudo apt-get install screen`

Run screen:

`bash screen`

You should then be prompted to logon to the pi
If that doesnt work try:

`sudo screen /dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0 115200`

##Setup wifi on the commandline
Update the config file `/etc/wpa_supplicant/wpa_supplicant.conf` with your wifi details:

```
network={
    ssid="Network_name"
    psk="Your_wifi_password"
}

```

See also [Raspberry Pis instructions for doing this](https://www.raspberrypi.org/documentation/configuration/wireless/wireless-cli.md)
