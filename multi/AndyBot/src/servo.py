#Servo Control
#By Tyler Spadgenske

#import libraries
import time
import RPi.GPIO as GPIO

class Servo():
    def __init__(self):
        self.DEBUG = True
        #Setup GPIO
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(11, GPIO.OUT)
        GPIO.setup(7, GPIO.OUT)
        GPIO.setup(13, GPIO.OUT)
        GPIO.setup(15, GPIO.OUT)
        
        #Setup PWM
        self.frequency = 50#Hertz
        self.left_foot = GPIO.PWM(11, self.frequency)
        self.left_knee = GPIO.PWM(7, self.frequency)
        self.right_knee = GPIO.PWM(13, self.frequency)
        self.right_foot = GPIO.PWM(15, self.frequency)

        #Setup duty cycles
        self.RIGHT = .4
        self.CENTER = 1.5
        self.LEFT = 2.5

        self.foot_left = 2

        self.msPerCycle = 1000 / self.frequency

    def move(self, position, servo):
        self.dutyCyclePercentage = position * 100 / self.msPerCycle
        if self.DEBUG:
            print('Position: ' + str(position))
            print('Duty Cycle: ' + str(self.dutyCyclePercentage) + '%')
            print()

        servo.start(self.dutyCyclePercentage)
        
    def cleanup(self):
        self.left_foot.stop()
        self.left_knee.stop()
        self.right_knee.stop()
        #GPIO.cleanup()

if __name__ == '__main__':
    test = Servo()
    test.move(test.RIGHT, test.left_knee)
    time.sleep(1)
    test.cleanup()
    time.sleep(.5)
    test.move(test.RIGHT, test.right_knee)
    time.sleep(1)
        
    test.cleanup()
    GPIO.cleanup()
