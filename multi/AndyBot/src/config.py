#Configuration Reader
#By Tyler Spadgenske

class Configure():
    def __init__(self):
        self.main_config_file = open('/home/pi/ANDY/configure/system.conf', 'r')
        self.server_config_file = open('/home/pi/ANDY/configure/server.conf', 'r')

    def read(self):
        invalid = False
        #Read system.conf file for main settings
        for i in self.main_config_file.readlines():
            if i[0] == '#':
                pass #Hashtags are commented lines

            #Start Andy on boot?
            if 'start-andy-on-boot' in i:
                if 'True' in i:
                    start_andy_on_boot = True
                elif 'False' in i:
                    start_andy_on_boot = False
                else:
                    invalid = True

            #Auto detect people and start conversation?
            if 'social-mode' in i:
                if 'True' in i:
                    social_mode = True
                elif 'False' in i:
                    social_mode = False
                else:
                    invalid = True

            #Have .01% chance of rebelling?
            if 'rebel-mode' in i:
                if 'True' in i:
                    rebel_mode = True
                elif 'False' in i:
                    rebel_mode = False
                else:
                    invalid = True

            #Wander around if no command is given?
            if 'wander-mode' in i:
                if 'True' in i:
                    wander_mode = True
                elif 'False' in i:
                    wander_mode = False
                else:
                    invalid = True

        if invalid:
            return [None, None, None, None]
        else:
            return [start_andy_on_boot, social_mode, rebel_mode, wander_mode]

    def read_server(self):
        server_name = ''
        client_ip = ''
        server_pass = ''
        invalid = False
        #Read server.conf file for server settings
        for i in self.server_config_file.readlines():
            if i[0] == '#':
                pass #Hashtags are commented lines

            #Start Andy Server on boot?
            if 'start-server' in i:
                if 'True' in i:
                    start_server = True
                elif 'False' in i:
                    start_server = False
                else:
                    invalid = True

            #IP address of client
            start = False
            if 'client-ip' in i:
                for letter in i:
                    if start:
                        if letter == '"':
                            start = False
                    if start:
                        client_ip = client_ip + letter
                    if letter == '"':
                        start = True
                client_ip = client_ip.rstrip()

            #Network Name
            start = False
            if 'server-name' in i:
                for letter in i:
                    if start:
                        if letter == '"':
                            start = False
                    if start:
                        server_name = server_name + letter
                    if letter == '"':
                        start = True
                server_name = server_name.rstrip()

            #Local Network Password
                start = False
            if 'server-pass' in i:
                for letter in i:
                    if start:
                        if letter == '"':
                            start = False
                    if start:
                        server_pass = server_pass + letter
                    if letter == '"':
                        start = True
                server_pass = server_pass.rstrip()

        if invalid:
            return [None, None, None, None]
        else:
            return [start_server, client_ip, server_name, server_pass]
        
if __name__ == '__main__':
    i = Configure()
    w = i.read_server()
    print(w)
