# msm: source - http://www.instructables.com/id/Send-EmailTXT-when-you-return-home-detects-when-iP/?ALLSTEPS

import os
import socket
import time
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

#****************************************************************

#enter the MAC address for the smartphone you want to search for.

#****************************************************************

IphoneMac = "__:__:__:__:__:__"

#******************************************************************

#enter the phone number to send a text message to.  Use this format:

    #for AT&T,     use _______@txt.att.net

    #for T-Mobile, use _______@tmomail.net

    #for Verizon,  use _______@vtext.com

    #for Sprint,   use _______@pm.sprint.com

    #for Boost,    use _______@myboostmobile.com

    #for Cricket,  use _______@mms.cricketwireless.net

#******************************************************************

toSMS = "__________@______.com"

#**********************************************************

#enter the email address that you want to send alerts to

#**********************************************************

toemail = "__________@_____.com"


#**********************************************************************

#enter the email address and password that you want to send alerts from

#**********************************************************************

fromemail = "__________@gmail.com"

emailpassword = "__________"


def SendEmail():

    #**********************************************************

    #gmail's smtp server, change this if you're not using gmail

    #**********************************************************

    smtpserver = "smtp.gmail.com"
    print("Attempting to send email and SMS from", fromemail, "to", toemail, "and", toSMS)

    body = 'Detected smartphone at the house as of %s' % (str(time.asctime(time.localtime(time.time()))))

    msg = MIMEText(body)
    msg['To'] = toemail
    msg['From'] = fromemail
    msg['Subject'] = 'Raspberry PI detected activity'

    print("Setting up the SMTP server")

    s = smtplib.SMTP(smtpserver, 587)
    s.set_debuglevel(True)

    print("Start transport layer security")

    s.ehlo()
    s.starttls()
    s.ehlo()

    print("Logging in....")

    s.login(fromemail, emailpassword)

    print("Sending the email")

    s.sendmail(fromemail, toemail, msg.as_string())

    print("Sending the SMS")

    s.sendmail(fromemail, toSMS, msg.as_string())

    print("Done with email/SMS sending...")

    s.quit()

    return 0

#Open the log file that records when you last sent an email/SMS alert.  If one doesn't exist, create one.
try:

    SMSlogfile = open('iphonescanSMSlog.txt', 'rw+')

    lineList = SMSlogfile.readlines()

    #print lineList

    SMSlogfile.close()

    LastSMSSentAt = lineList[len(lineList)-1]

except IOError as inst:

    print("Couldn't find an existing SMS log file, creating a new one and setting the initial timestamp")

    SMSlogfile = open('iphonescanSMSlog.txt', 'w+')

    #print SMSlogfile

    SMSlogfile.write("00000\n")
    SMSlogfile.close()

    LastSMSSentAt = 00000

#Display the settings to the screen.  The curly braces aren't needed, they just make the output line up better

print("************************************************")

print("Running program with the following settings:")

print(" -{0:40} {1:20}".format("Detecting smartphone MAC address:", IphoneMac))

print(" -{0:40} {1:20}".format("Send email alerts to:", toemail))

print(" -{0:40} {1:20}".format("Send text message alerts to:", toSMS))

print(" -{0:40} {1:20}".format("Send alerts from:", fromemail))

print("************************************************")

#Start the endless loop where the program perpetually searches for your smartphone's MAC address

while 1==1:

        print("\nSearching network for MAC address", IphoneMac)

        response = os.popen("sudo nmap -sP 192.168.2.1/24 | grep " + IphoneMac + " | awk '{print$3}' ","r").readline()

        #strip the newline character \n from response

        response = response.rstrip('\n')

        if response == IphoneMac:
            print("The MAC address", response, "is on the network")

            #Get the current time

            CurrentTime = time.time()
            LastSMSSentAt = float(LastSMSSentAt)

            #verify it's currently between 4-9 pm, and it's Mon-Fri (0-4), and you haven't already sent out an SMS in the last 12 hours

            if ((16 <= datetime.now().hour <= 21) and (datetime.today().weekday() < 5) and (CurrentTime - LastSMSSentAt) > (60*60*12)):

                #send email/SMS alerts
                SendEmail()

                #update the file to reflect that an email/SMS was sent
                LastSMSSentAt = time.time()
                SMSlogfile = open('iphonescanSMSlog.txt', 'a')

                SMSlogfile.write('\n')
                SMSlogfile.write(str(LastSMSSentAt))
                SMSlogfile.close()

                print("Updating the log file with a new timestamp because you sent an email/SMS")

            else:
                print("An email/SMS was sent within the last 12 hours or it's not Mon-Fri 4-9PM, not sending an alert...")

                if LastSMSSentAt != 0:
                    print("--Last alert sent:", time.strftime("%H Hours, %M Minutes, %S Seconds ago", time.gmtime(CurrentTime-LastSMSSentAt)))
        else:
                print("Didn't detect MAC address", IphoneMac, "on the network ")
