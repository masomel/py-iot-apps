from Tkinter import *
import MySQLdb
import numpy as np
import matplotlib.pyplot as plt

def Pressed():
        #function
        db = MySQLdb.connect('localhost','root', '', '')
        cursor = db.cursor()

        com = 'SELECT VALUE FROM EDISONLIGHT'
        cursor.execute(com)
        op = cursor.fetchall()
        a = np.array(op)
        x = np.arange(0,a.size,1)
        y = a
        plt.plot(x,y)
        plt.show()

        db.commit()
        db.close()

def TPressed():
        #function
        db = MySQLdb.connect('localhost','root','9okm8ijn76','TESTDB')
        cursor = db.cursor()

        com = 'SELECT VALUE FROM EDISONTEMP'
        cursor.execute(com)
        op = cursor.fetchall()
        a = np.array(op)
        x = np.arange(0,a.size,1)
        y = a
        plt.plot(x,y)
        plt.show()

        db.commit()
        db.close()


root = Tk()                             #main window
root.title("Satya's IoT Platform")

org = PanedWindow(root,orient=VERTICAL)
org.pack(fill=BOTH,expand=1)

m1 = PanedWindow(org,orient=HORIZONTAL)
m2 = PanedWindow(org,orient=HORIZONTAL)
m3 = PanedWindow(org,orient=HORIZONTAL)
org.add(m1)
org.add(m2)
org.add(m3)

temp = Label(m1,width=15)
mois = Label(m1,width=15)
light = Label(m1,width=15)
m1.add(temp)
m1.add(mois)
m1.add(light)

tempval = Label(m2)
moisval = Label(m2)
ligval = Label(m2)
m2.add(tempval)
m2.add(moisval)
m2.add(ligval)

tempplot = Label(m3)
moisplot = Label(m3)
ligplot = Label(m3)
m3.add(tempplot)
m3.add(moisplot)
m3.add(ligplot)

this = Text(temp, bg = 'Light Grey', height=1, width = 15,relief=FLAT)
yay = 'Temperature'
this.insert(INSERT,yay)
this.pack()

this = Text(mois, bg = 'Light Grey', height=1, width = 15,relief=FLAT)
yay = 'Moisture'
this.insert(INSERT,yay)
this.pack()

this = Text(light, bg = 'Light Grey', height=1, width = 15,relief=FLAT)
yay = 'Light'
this.insert(INSERT,yay)
this.pack()

this = Text(tempval, bg = 'White', height=1, width = 15)
yay = 'Loading...'
this.insert(INSERT,yay)
this.pack()

moisv = Text(moisval, bg = 'White', height=1, width = 15)
yay = 'Loading...'
moisv.insert(INSERT,yay)
moisv.pack()

lightv = Text(ligval, bg = 'White', height=1, width = 15)
yay = 'Loading...'
lightv.insert(INSERT,yay)
lightv.pack()

button = Button(tempplot, text = 'Plot T', command = TPressed, height=1, width = 10)
button.pack(padx = 2)

button = Button(moisplot, text = 'Plot M', command = Pressed, height=1, width = 10)
button.pack(padx = 2)

button = Button(ligplot, text = 'Plot L', command = Pressed, height=1, width = 10)
button.pack(padx = 2)

def task():
        db = MySQLdb.connect('localhost','root', '', '')
        cursor = db.cursor()

        com = 'SELECT VALUE FROM SENSORDATA WHERE SOURCE = "Edison" AND TYPE ="Temperature"'
        cursor.execute(com)
        why = cursor.fetchone()
        why = str(why[0])
        this.delete('1.0','2.0')
        this.insert(INSERT,why)

        com = 'SELECT VALUE FROM SENSORDATA WHERE SOURCE = "Edison" AND TYPE ="Moisture"'
        cursor.execute(com)
        why = cursor.fetchone()
        why = str(why[0])
        moisv.delete('1.0','2.0')
        moisv.insert(INSERT,why)

        com = 'SELECT VALUE FROM SENSORDATA WHERE SOURCE = "Edison" AND TYPE ="Light"'
        cursor.execute(com)
        why = cursor.fetchone()
        why = str(why[0])
        lightv.delete('1.0','2.0')
        lightv.insert(INSERT,why)

        db.commit()
        db.close()
        root.after(2000,task)

root.after(10000,task)
root.mainloop()
