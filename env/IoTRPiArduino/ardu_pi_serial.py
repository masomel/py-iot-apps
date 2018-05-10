import serial

ser = serial.Serial('/dev/ttyAMA0', 9600)

while True:
    command = input("Enter command: l - toggle LED, r - read A0 ")
    if command == 'l':
        ser.write('l')
    elif command =='r':
        ser.write('r')
        print((ser.readline()))
