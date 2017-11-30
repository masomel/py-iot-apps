#LED Use
#By Tyler Spadgenske

import time
import RPi.GPIO as GPIO

def write(task):
    LED_file = open('/home/pi/ANDY/src/temp/LED.txt', 'w')
    if task == 'error':
        LED_file.write('True\n')
        LED_file.write('True\n')
        LED_file.write('False\n')
    if task == 'back':
        LED_file.write('True\n')
        LED_file.write('False\n')
        LED_file.write('True\n')
    if task == 'load':
        LED_file.write('False\n')
        LED_file.write('True\n')
        LED_file.write('True\n')
    if task == None:
        LED_file.write('True\n')
        LED_file.write('True\n')
        LED_file.write('True\n')
    LED_file.close()
    
class LED():
    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)

        self.right = 12
        self.center = 16
        self.left = 22

        self.wait = .25

        GPIO.setup(self.left, GPIO.OUT)
        GPIO.setup(self.center, GPIO.OUT)
        GPIO.setup(self.right, GPIO.OUT)
        self.stop_load = True
        self.stop_error = True
        self.stop_back = True

    def read_file(self):
        LED_file = open('/home/pi/ANDY/src/temp/LED.txt', 'r')
        self.stop_load = LED_file.readline().rstrip()
        self.stop_back = LED_file.readline().rstrip()
        self.stop_error = LED_file.readline().rstrip()
        LED_file.close()
        
        if self.stop_load == 'False':
            self.stop_load = False
        else:
            self.stop_load = True
        if self.stop_error == 'False':
            self.stop_error = False
        else:
            self.stop_error = True
        if self.stop_back == 'False':
            self.stop_back = False
        else:
            self.stop_back = True
            
    def load(self):
        while self.stop_load == False:
            LEDS.read_file()
            GPIO.output(self.left, True)
            time.sleep(self.wait)
            GPIO.output(self.left, False)

            GPIO.output(self.center, True)
            time.sleep(self.wait)
            GPIO.output(self.center, False)

            GPIO.output(self.right, True)
            time.sleep(self.wait)
            GPIO.output(self.right, False)
        self.shutoff()
            
    def background_load(self):
        while self.stop_back == False:
            LEDS.read_file()
            GPIO.output(self.left, True)
            time.sleep(self.wait)
            GPIO.output(self.left, False)
            GPIO.output(self.right, True)
            time.sleep(self.wait)
            GPIO.output(self.right, False)
        self.shutoff()

    def error(self):
        while self.stop_error == False:
            LEDS.read_file()
            GPIO.output(self.left, True)
            GPIO.output(self.right, True)
            GPIO.output(self.center, True)
            time.sleep(1)
            GPIO.output(self.left, False)
            GPIO.output(self.right, False)
            GPIO.output(self.center, False)
            time.sleep(1)
        self.shutoff()

    def shutoff(self):
        GPIO.output(self.left, False)
        GPIO.output(self.right, False)
        GPIO.output(self.center, False)
        
if __name__ == '__main__':
    LEDS = LED()
    while True:
        LEDS.read_file()
        LEDS.load()
        LEDS.error()
        LEDS.background_load()
