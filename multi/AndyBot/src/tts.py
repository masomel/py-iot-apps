#Text to speech
#By Tyler Spadgenske

import os, json
 
# main() function
def say(message='Sorry...... I do not understand.'):
  OPTIONS = " -vdefault+m3 -p 40 -s 160 --stdout > say.wav"
  os.system("espeak " + json.dumps(message) + OPTIONS)
  os.system("aplay -D hw:1 say.wav")
 
# call main
if __name__ == '__main__':
  say(raw_input("Text:" ))
