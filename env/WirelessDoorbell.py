# msm: source - http://www.instructables.com/id/Wireless-Doorbell-Raspberry-PI-Amazon-Dash/?ALLSTEPS

"""********************
Doorbell script redone for python3
must run pip3 install scapy-python3
 
********************"""

from scapy.all import *
import urllib.request

def arp_display(pkt):

	url_pc = 'http://autoremotejoaomgcd.appspot.com/sendmessage?key=YOUR_AUTOREMOTE_KEY_HERE&message='
	url_mobile = 'http://autoremotejoaomgcd.appspot.com/sendmessage?key=YOUR_AUTOREMOTE_KEY_HERE&message='

	if pkt[ARP].op == 1:
		if pkt[ARP].psrc == '0.0.0.0':
			if pkt[ARP].hwsrc == 'AA:AA:AA:AA:AA:AA': #Your button MAC
				button = 'BUTTON 1'		
			elif pkt[ARP].hwsrc == 'AA:AA:AA:AA:AA:AA': #Other button mac if you have more than one, OTHERWISE  delete this and next line
				button	= 'BUTTON 2'
			#putting URL together before sent
			messagePc = url_pc + button
			messageMobile = url_mobile + button	
			#sending message to pc/mobile		
			response = urllib.request.urlopen(messagePc).read()
			response = urllib.request.urlopen(messageMobile).read()
			
			#print ("Call from: " + button) #unhash for testing
		#print (pkt[ARP].hwsrc) #unhash for finding MAC of your button
print (sniff(prn=arp_display, filter="arp", store=0, count=0))