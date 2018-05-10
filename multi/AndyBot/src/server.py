#Andy server test
#By Tyler Spadgenske

import socket, os, time, sys
from tts import say
from config import Configure

class Server():
    def __init__(self):
        self.config = Configure()
        self.start_server, self.client_ip, self.server_name, self.server_pass = self.config.read_server()
        if self.start_server == False:
            sys.exit()
        say('Starting Server')
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = ''
        self.port = 5150
        self.server.bind((self.host, self.port))
        self.server.listen(5)
        print('Listing for a client...')
        self.client, self.addr = self.server.accept()
        print('Accepted connection from ', self.addr)
        self.client.send(str.encode('Connection made with Andy'))

    def get_cmd(self):
        try:
            self.data = self.client.recv(1024)
        except:
            print('Lost Connection with ', self.addr)
            return None
        print('Recieved data from client: ', bytes.decode(self.data))

        return bytes.decode(self.data)

    def end(self):
        print('Closing connection...')
        self.client.close()
        
def start():
    serv = Server()
    while True:
        files = open('/home/pi/ANDY/src/temp/cmd.txt', 'w+')
        os.system('sudo chmod 777 /home/pi/ANDY/src/temp/cmd.txt')
        cmd = serv.get_cmd()
        if cmd == None:
            break
        files.write(cmd)
        files.close()
        while True:
            if os.path.isfile('/home/pi/ANDY/src/temp/cmd.txt') == False:
                break
        
    serv.end()      

if __name__ == '__main__':
    while True:
        try:
            start()
        except:
            say('Server Already Running')
            sys.exit()
            
