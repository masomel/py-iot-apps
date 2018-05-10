import ouimeaux
from ouimeaux.environment import Environment
from time import sleep

print("env")
wemo = Environment()
print("start")
wemo.start()
print("discover")
wemo.discover(5)
print(wemo.list_switches())
wemoFan = wemo.get_switch('wemoFan02')

print("on")
wemoFan.on()
sleep (5)
print("off")
wemoFan.off()
sleep (5)
print("toggle")
wemoFan.toggle()






