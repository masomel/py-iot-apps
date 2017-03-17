import socket
import MySQLdb
db = MySQLdb.connect('localhost','root','', '')
cursor = db.cursor()

TCP_IP = *RASPBERRY PI IP ADDRESS HERE*
TCP_PORT = 5005
BUFFER_SIZE = 25
s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind((TCP_IP,TCP_PORT))

while 1:
    s.listen(2)
    conn,addr = s.accept()
    data = conn.recv(BUFFER_SIZE)
    recdata = str(data)
    typ,val = recdata.split('/')
    print (val)
    val = str(val)
    print (typ)
    typ = str(typ)

    if(typ=='Temperature'):
        com = 'INSERT INTO EDISONTEMP (VALUE) VALUES ('+val+')'
        cursor.execute(com)
        com = 'UPDATE SENSORDATA SET VALUE ='+val+' WHERE SOURCE = "Edison" AND TYPE ="'+typ+'"'
        cursor.execute(com)
        db.commit()

    if(typ=='Light'):
        com = 'INSERT INTO EDISONLIGHT (VALUE) VALUES ('+val+')'
        cursor.execute(com)
        com = 'UPDATE SENSORDATA SET VALUE ='+val+' WHERE SOURCE = "Edison" AND TYPE ="'+typ+'"'
        cursor.execute(com)
        db.commit()
