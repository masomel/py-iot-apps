# -*- coding: utf-8-*-
import random
import re
import os
import subprocess

WORDS = ["SHUTDOWN", "SHUT", "DOWN"]

PRIORITY = 3

def handle(text, mic, profile):
    import subprocess
    """
        Responds to user-input, typically speech text, by shutting down the computer
        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        profile -- contains information related to the user (e.g., phone
                   number)
    """
    messages = ["Dave... My mind is going.", "Daisy, daisy, give me your answer do...", "Goodbye, Dave"]
    message = random.choice(messages)
    mic.say(message)

    command = "/usr/bin/sudo /sbin/shutdown -f now"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]


def isValid(text):
    """
        Returns True if the input is related to the shutdown module
        Arguments:
        text -- user-input, typically transcribed speech
    """
return bool(re.search(r'\b(SHUTDOWN|SHUT DOWN)\b', text, re.IGNORECASE))
