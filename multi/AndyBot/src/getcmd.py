#Get Command
#By Tyler Spadgenske
import mic, tts, time, os

class Get_cmd():
    def __init__(self):
        self.microphone = mic.Mic(lmd='models/lm.lm', dictd='models/dic.dic',
                     lmd_persona='models/waitlm.lm', dictd_persona='models/waitdic.dic')

        self.THRESHOLD = self.microphone.fetchThreshold()
        print('Threshold: ' + str(self.THRESHOLD))
        self.run_client = False
        self.client = None
        
    def get(self):
        while True:
            self.run_client = False
            self.client_cmd = self.get_client_cmd()
            if self.client_cmd != None:
                self.cmd = self.client_cmd
                self.run_client = True
                os.system('sudo rm /home/pi/ANDY/src/temp/cmd.txt')
                break
                
            self.word = self.microphone.passiveListen('ANDY')
            if self.word:
                break

        if self.run_client != True:
            self.cmd = self.microphone.activeListen(THRESHOLD=self.THRESHOLD)
                
        print('COMMAND: ', self.cmd)
        return self.cmd

    def get_client_cmd(self):
        self.client = None
        if os.path.isfile('/home/pi/ANDY/src/temp/cmd.txt'):
            self.readit = open('/home/pi/ANDY/src/temp/cmd.txt', 'r')
            self.lines = self.readit.readlines()
            if self.lines != []:
                self.client = self.lines[0]
            self.readit.close()

        return self.client
    
def get_age():
    microphone = mic.Mic(lmd='models/agelm.lm', dictd='models/agedic.dic',
                     lmd_persona='models/waitlm.lm', dictd_persona='models/waitdic.dic')
    while True:
        age = microphone.activeListen()
        if age != '':
            break

    age = age.lower().capitalize()
    return age

def get_fav_color():
    microphone = mic.Mic(lmd='models/colorlm.lm', dictd='models/colordic.dic',
                    lmd_persona='models/waitlm.lm', dictd_persona='models/waitdic.dic')
    while True:
        fav_color = microphone.activeListen()
        if fav_color != '':
            break

    fav_color = fav_color.lower().capitalize()
    return fav_color

def get_fav_ice_cream():
    microphone = mic.Mic(lmd='models/creamlm.lm', dictd='models/creamdic.dic',
                    lmd_persona='models/waitlm.lm', dictd_persona='models/waitdic.dic')
    while True:
        fav_cream = microphone.activeListen()
        if fav_cream != '':
            break

    fav_cream = fav_cream.lower().capitalize()
    return fav_cream

    

    
    
if __name__ == '__main__':
    fav_cream = get_fav_ice_cream()
    print(fav_cream)
        
    
