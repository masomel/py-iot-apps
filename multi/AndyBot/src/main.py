#main.py
#By Tyler Spadgenske
DEBUG = True

#Import modules
import cmds, traceback, subprocess, sys, time
from getcmd import Get_cmd
from tts import say
from config import Configure
from meet import Meet
from LED import write

def main(DEBUG=False):
    #Start LEDs
    write('load')
    subprocess.Popen(['python', 'LED.py'])
    #Read from configuration files and apply settings.
    config = Configure()
    start_andy_on_boot, social_mode, rebel_mode, wander_mode = config.read()
    if start_andy_on_boot == False:
        sys.exit()

    #Say start up slogan and check for command.
    say('Hello. My name is Andy. Please wait while my system starts up.')
    getit = Get_cmd()
    #Start server process 
    subprocess.Popen(['python', 'server.py'])
    write(None)
    #Enter main loop
    while True:
        print
        #Get the command and convert it to a list
        cmd = getit.get().split()
        write('load')
        if DEBUG: print 'COMMAND:', cmd

        #Remove unused words from command
        num = 0
        for word in cmd:
            cmd[num] = word.lower()
            num += 1
        if len(cmd) == 0:
            cmd.append('')
        #Determin master command
        if cmd[0] == 'what':
            cmds.What(cmd, DEBUG)
        elif cmd[0] == 'walk' or cmd[0] == 'turn':
            cmds.Walk(cmd, DEBUG)
        elif cmd[0] == 'stop':
            cmds.Walk(cmd, DEBUG).stop()
        elif cmd[0] == 'pickup' or cmd[0] == 'pick' and cmd[1] == 'up':
            cmds.Arm(cmd, DEBUG).pickup()
        elif cmd[0] == 'set' and cmd[1] == 'down':
            cmds.Arm(cmd, DEBUG).setdown()
        elif cmd[0] == 'where':
            cmds.Where(cmd, DEBUG)
        elif cmd[0] == 'take':
            cmds.Take(cmd, DEBUG)
        elif cmd[0] == 'set':
            pass #TODO
        elif cmd[0] == 'tell':
            cmds.Tell(cmd, DEBUG)
        elif cmd[0] == 'who':
            cmds.Who(cmd, DEBUG)
        elif cmd[0] == 'shutdown':
            cmds.shutdown()
        elif cmd[0] == 'sleep':
            cmds.sleep()
        elif cmd[0] == 'meet':
            Meet(cmd, DEBUG)
        else:
            say('Not valid command')
        write(None)
        time.sleep(1)
            
if __name__ == '__main__':
    try:
        main(DEBUG=DEBUG)
    except SystemExit:
        pass
    except:
        write('error')
        #If error occurs, save it to file
        error = traceback.format_exc()
        error_log = open('/home/pi/ANDY/src/temp/error.txt', 'w')
        error_log.write(error)
        print 'An error occurred. Please check error.txt for more details.'
        say('An error occurred.. Please check error dot text for more details.')
        time.sleep(4)
        write(None)
