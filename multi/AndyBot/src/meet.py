#Meet Command
#By Tyler Spadgenske

from tts import say
from database import Database
from getcmd import *

class Meet():
    def __init__(self, cmd, DEBUG):
        cmd.pop(0)
        if len(cmd) >= 1:
            meet = 'Hello ' + str(cmd[0]) + '... It is nice to meet you.'
            say(meet)
            Database().add_person(cmd[0])
            say('How old are you?')
            self.age(cmd[0])
            say('What is your favorite color?')
            self.color(cmd[0])
            say('What is your favorite ice cream?')
            self.ice_cream(cmd[0])

    def age(self, name): #Gets persons age and adds it to database
        self.person_age = get_age()
        Database().add_person_data(name, self.person_age, 'age')

    def color(self, name):#Gets persons favorite color and adds it to database
        self.person_color = get_fav_color()
        Database().add_person_data(name, self.person_color, 'favorite_color')

    def ice_cream(self, name): #Gets persons favorite ice cream and adds it to database
        self.person_cream = get_fav_ice_cream()
        Database().add_person_data(name, self.person_cream, 'favorite_ice_cream')
