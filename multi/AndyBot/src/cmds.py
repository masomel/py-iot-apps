# -*- coding: utf-8 -*-
#Commands
#By Tyler Spadgenske

import datetime, time, random, sys, os
from tts import say
from database import Database
from getcmd import get_age
import picamera

#Object for the "What" command
class What(object):
    def __init__(self, cmd, DEBUG=False):
        self.DEBUG = DEBUG
        self.cmd = cmd
        #Remove 'what' from command
        self.cmd.pop(0)
        #Run math() if math problem
        if cmd[0] == 'is' and cmd[1] != 'your':
            #Remove 'is' from command
            self.cmd.pop(0)
            self.math()
        #Run time() if time question
        if cmd[0] == 'time' or cmd[0] == 'day':
            self.time()
        #Run other simpler commands if question about Andy himself
        if self.cmd[0] == 'is' and self.cmd[1] == 'your':
            self.cmd.pop(0)
            self.cmd.pop(0)
            self.me()

    #Convert month number to month text
    def get_month(self, num, num2):
        if num2 == '1':
            self.day = 'January'
        if num2 == '2':
            self.day = 'February'
        if num2 == '3':
            self.day = 'March'
        if num2 == '4':
            self.day = 'April'
        if num2 == '5':
            self.day = 'May'
        if num2 == '6':
            self.day = 'June'
        if num2 == '7':
            self.day = 'July'
        if num2 == '8':
            self.day = 'August'
        if num2 == '9':
            self.day = 'September'
        if num == '1' and num2 == '0':
            self.day = 'October'
        if num == '1' and num2 == '1':
            self.day = 'November'
        if num == '1' and num2 == '2':
            self.day = 'December'
        return self.day

    #Solve math equation and say answer
    def math(self):
        if self.DEBUG: print('EQUATION:', self.cmd)

        #Check for valid command again
        if len(self.cmd) == 3 or len(self.cmd) == 4:
            pass
        else:
            for i in range(0, 2):
                self.cmd.append(None)
            say('Invalid Command')

        #Solve problem
        self.answer = None
        try:
            if self.cmd[1] == 'plus':
                self.answer = int(self.cmd[0]) + int(self.cmd[2])
            elif self.cmd[1] == 'minus':
                self.answer = int(self.cmd[0]) - int(self.cmd[2])
            elif self.cmd[1] == 'times':
                self.answer = int(self.cmd[0]) * int(self.cmd[2])
            elif self.cmd[1] == 'divided':
                self.answer = int(self.cmd[0]) / int(self.cmd[3])
        except:
            if self.DEBUG: print('Not, math, looking elsewhere...')

        if self.DEBUG: print('ANSWER = ', str(self.answer))

    def time(self):
        #Get current time
        self.raw_time = str(datetime.datetime.now()).split()
        #Say time if selected command
        if self.cmd[0].lower() == 'time':
            time = str(self.raw_time[1])
            say('It is ' + time[0] + time[1] + time[2] + time[3] + time[4] + ' AM.') #TODO: Fix time to say it in 12hr time not 24hr time
        #Say day if selected command
        if self.cmd[0].lower() == 'day':
            time = str(self.raw_time[0])
            month = self.get_month(time[5], time[6])

            say('Today is ' + month + ' ' + time[-2] + time[-1] + ', ' + time[0] + time[1] + time[2] + time[3])

    def me(self):
        if self.cmd[0] == 'name':
            say('My name is Cyclops of course.')
        if self.cmd[0] == 'phone':
            say("I don't think I should tell you that.")
        if self.cmd[0] == 'email':
            say('My email is cyclopsrobot@gmail.com.')
        if self.cmd[0] == 'problem':
            say("Whatever it is, I don't care.")

#Move onto walking functions
class Walk():
    def __init__(self, cmd=['walk','happy'], DEBUG=False):
        self.cmd = cmd
        self.DEBUG = DEBUG
        print(self.cmd)
        self.cmd.pop(0)
        #Get movement command and run function
        if len(self.cmd) != 0:
            if self.cmd[0] == 'forward':
                self.forward()
            if self.cmd[0] == 'backward':
                self.backward()
            if self.cmd[0] == 'left':
                self.left()
            if self.cmd[0] == 'right':
                self.right()

    #define movement functions
    def forward(self):
        #say('Walking Forward')
        say('I cannot walk forward because my motors are burnt out')

    def backward(self):
        #say('Walking Backward')
        say('I cannot walk backward because my motors are burnt out')

    def left(self):
        #say('Turning left')
        say('I cannot turn left because my motors are burnt out')

    def right(self):
        #say('Turning right')
        say('I cannot turn right because my motors are burnt out')

    def stop(self):
        say('Stopping')

#Move onto arm functions
class Arm():
    def __init__(self, cmd, DEBUG=False):
        self.cmd = cmd
        self.DEBUG = DEBUG

    def pickup(self):
        try:
            say('Picking up ' + self.cmd[-1])
        except:
            say('Please name object')

    def setdown(self):
        say('Setting down ' + self.cmd[-1])

#Move onto location functions
class Where():
    def __init__(self, cmd, DEBUG=False):
        self.cmd = cmd
        self.DEBUG = DEBUG
        self.cmd.pop(0)
        if len(self.cmd) != 0:
            if self.cmd[-1].lower() == 'i':
                self.here()
            else:
                self.find()

    def here(self):
        say('GPS location module not added. here() called.')

    def find(self):
        say('GPS location module not added. find() called.')

class Take(): #Commands with camera use
    def __init__(self, cmd, DEBUG=False):
        self.num = 0
        self.cmd = cmd
        self.DEBUG = DEBUG
        self.cmd.pop(0)
        if len(self.cmd) != 0:
            if self.cmd[0].lower() == 'picture':
                self.pic()
            if self.cmd[0].lower() == 'video':
                self.video()

    def pic(self):
        #Speak and open pic.txt file
        say('Taking Picture')
        self.pic_file = open('/home/pi/ANDY/src/temp/pic.txt', 'r')
        self.num = self.pic_file.readline().rstrip()
        self.pic_file.close()

        #Start camera and take picture
        with picamera.PiCamera() as camera:
            camera.resolution = (1024, 768)
            camera.start_preview()
            time.sleep(2)

            #Take pic
            camera.capture('/home/pi/ANDY/pictures/' + str(self.num) + '.jpg')
            camera.stop_preview()
        self.pic_file = open('/home/pi/ANDY/src/temp/pic.txt', 'w')
        self.pic_file.write(str(int(self.num) + 1))
        self.pic_file.close()

        #Upload to Dropbox
        try:
            os.system('/home/pi/Dropbox-Uploader/./dropbox_uploader.sh upload ' +
                      '/home/pi/ANDY/pictures/' + str(self.num) + '.jpg ' + str(self.num) + '.jpg')
        except:
            say('Failed to upload to drop box')#Upload to Dropbox
        try:
            os.system('/home/pi/Dropbox-Uploader/./dropbox_uploader.sh upload ' +
                      '/home/pi/ANDY/pictures/' + str(self.num) + '.jpg ' + str(self.num) + '.jpg')
        except:
            say('Failed to upload to drop box')

    def video(self):
        #Open file and get video number
        self.vid_file = open('/home/pi/ANDY/src/temp/vid.txt', 'r')
        self.vid_num = self.vid_file.readline().rstrip()
        self.vid_file.close()

        say('Recording Video in 3')
        time.sleep(1)
        say('two')
        time.sleep(1)
        say('one')
        time.sleep(1)

        #Record Video
        with picamera.PiCamera() as camera:
            camera.resolution = (640, 480)
            camera.start_preview()
            camera.start_recording('/home/pi/ANDY/videos/' + str(self.vid_num) + '.h264')
            camera.wait_recording(10)
            camera.stop_recording()
            camera.stop_preview()

        self.vid_file = open('/home/pi/ANDY/src/temp/vid.txt', 'w')
        self.vid_file.write(str(int(self.vid_num) + 1))
        self.vid_file.close()

class Tell():
    def __init__(self, cmd, DEBUG=False):
        self.cmd = cmd
        self.DEBUG = DEBUG
        self.cmd.pop(0)
        self.cmd.pop(0)
        self.cmd.pop(0)
        if len(self.cmd) != 0:
            if self.cmd[0].lower() == 'joke':
                self.joke()
            if self.cmd[0].lower() == 'riddle':
                self.riddle()

    def joke(self):
        a = ['Canoe.', 'Canoe help me with my homework?']
        b = ['Anee.', 'Anee one you like!']
        c = ['Arfur.', 'Arfur got!']
        d = ['Nana.', 'Nana your business.']
        e = ['Ya.', 'Wow. You sure are excited to see me!']
        f = ['Cows go', 'Cows don’t go who, they go moo!']
        g = ['Etch.', 'Bless you!']

        jokes = [a, b, c, d, e, f, g]
        joke = random.choice(jokes)

        #say('Knock Knock.')
        #time.sleep(4)
        #say(joke[0])
        #time.sleep(4)
        #say(joke[1])
        say('Why cant your nose be 12 inches long?')
        time.sleep(3)
        say('Because then it would be a foot!')

    def riddle(self):
        a = 'What gets wetter and wetter the more it dries?'
        b = 'You throw away the outside and cook the inside. Then you eat the outside and throw away the inside. What did you eat?'
        c = 'What goes up and down the stairs without moving?'
        d = 'What can you catch but not throw?'
        e = 'I can run but not walk. Wherever I go, thought follows close behind. What am I?'
        f = "What's black and white and red all over?"
        g = 'What goes around the world but stays in a corner?'

        riddles = [a, b, c, d, e, f, g]
        riddle = random.choice(riddles)
        say(riddle)

class Who():
    def __init__(self, cmd, DEBUG=False):
        self.cmd = cmd
        self.database = Database()
        if len(self.cmd) > 2:
            self.cmd.pop(0)
            self.cmd.pop(0)
            self.get_info(self.cmd[0])
        else:
            say("I am sorry. I do not know who you are talking about.")

    def get_info(self, name):
        name = name.lower()
        name = name.capitalize()
        self.color = Database().get_people_data(name, 'favorite_color')
        self.iceCream = Database().get_people_data(name, 'favorite_ice_cream')
        self.age = Database().get_people_data(name, 'age')
        self.food = Database().get_people_data(name, 'favorite_food')

        if self.age != None:
            if self.age == 'None':
                self.age_string = 'I do not know how old ' + name + ' is. '
            else:
                self.age_string = name + ' is ' + self.age + ' years old. '

            if self.color == 'None':
                self.color_string = 'I do not know ' + name + 's favorite color. '
            else:
                self.color_string = name + 's favorite color is ' + self.color

            if self.iceCream == 'None':
                self.cream_string = 'I do not know ' + name + 's favorite ice cream.'
            else:
                self.cream_string = name + 's favorite ice cream is ' + self.iceCream

            if self.food == 'None':
                self.food_string = 'I do not know ' + name + 's favorite food.'
            else:
                self.food_string = name + 's favorite food is ' + self.food

            say(self.age_string)
            say(self.color_string)
            say(self.cream_string)
            say(self.food_string)
        else:
            string = 'I do not know ' + name
            say(string)

def shutdown():
    say("Sutting down... Please Wait.")
    time.sleep(5)
    os.system("sudo halt")
    sys.exit(0)

def sleep():
    say("Going to sleep... Good Night.")
    time.sleep(5)
    sys.exit(0)
