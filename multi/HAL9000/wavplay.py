# -*- coding: utf-8-*-
# vim: set expandtab:ts=4:sw=4:ft=python
import random
import re
import os
import glob
import subprocess
from os.path import expanduser

WORDS = ["SAY", "SOMETHING", "DAVE", "WAVE"]

PRIORITY = 4


def handle(text, mic, profile):
    """
        Responds to user-input, typically speech text, by playing a
        random wav file from a pre-determined directory.
        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        profile -- contains information related to the user (e.g., phone
                   number)
    """
    home = expanduser("~")
    target_directory = home
    if 'wavplay' in profile and 'path' in profile['wavplay']:
        if os.path.isdir(profile['wavplay']['path']):
            target_directory = profile['wavplay']['path']

    os.chdir(target_directory)
    wavs = glob.glob("*.wav")
    if len(wavs) == 0:
        return mic.say('I could not find any wav files')

    wav = random.choice(wavs)
    subprocess.Popen(['aplay', wav])


def isValid(text):
    """
        Returns True if the input is related to the meaning of life.
        Arguments:
        text -- user-input, typically transcribed speech
    """
    regex = "(say something|dave|quote|wave)"
return bool(re.search(regex, text, re.IGNORECASE))
