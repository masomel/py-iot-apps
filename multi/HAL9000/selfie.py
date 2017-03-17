# -*- coding: utf-8-*-
# vim: set expandtab:ts=4:sw=4:ft=python
import random
import re
import os
import subprocess
from datetime import datetime

#send_email
import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

WORDS = ["SELFIE", "TAKE", "PICTURE", "PHOTO", "CHEESE"]

PRIORITY = 4

def send_mail(profile, subject, text, files=None):
    try:
        if 'mailgun' in profile:
            user = profile['mailgun']['username']
            password = profile['mailgun']['password']
            server = 'smtp.mailgun.org'
        else:
            user = profile['gmail_address']
            password = profile['gmail_password']
            server = 'smtp.gmail.com'
    except:
        pass

    send_to = profile['selfie']['email']
    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = send_to
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
            part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
            msg.attach(part)

    session = smtplib.SMTP(server, 587)
    session.starttls()
    session.login(user, password)
    session.sendmail(user, send_to, msg.as_string())
    session.quit()

def handle(text, mic, profile):
    import subprocess
    """
        Responds to user-input, typically speech text, by taking a webcam snapshot
        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        profile -- contains information related to the user (e.g., phone
                   number)
    """
    process = subprocess.Popen(['aplay', '/home/pi/sounds/shutter.wav'])
    filename = '/home/pi/images/webcam-%s.jpeg'%datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f')
    cmd = 'fswebcam -d /dev/video0 -p YUYV -r 1600x1200 --jpeg 85 -F 4 --set Gamma=4 --no-banner '+filename
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]


    messages = ["You look beautiful", "Errrmmm... nice", "How do you look? Do you want me to delete it?", "Nice."]
    message = random.choice(messages)
    mic.say(message)

    send_mail(profile, 'HAL9000 Webcam Snapshot', message, [filename])


def isValid(text):
    """
        Returns True if the input is related to the meaning of life.
        Arguments:
        text -- user-input, typically transcribed speech
    """
return bool(re.search(r'\b(selfie|photo|picture|cheese)\b', text, re.IGNORECASE))
