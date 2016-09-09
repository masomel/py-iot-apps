# Script that writes the current temperature measured by the DS18B20
import os

base_dir = '/sys/bus/w1/devices/'
temp_sensor_dir = base_dir+'28-031564af7aff'
device_file = temp_sensor_dir+'/w1_slave'

def error(lines):
    print('No temp reading available at this time.')
    print(lines)

def read_temp_raw():
    f = open("apps/pi_therm/dummy-temp.txt", 'r')
    lines = f.readlines()
    f.close()
    return lines
    
def read_temp():
    lines = read_temp_raw()
    if lines[0].strip().endswith('YES'):
        equals_pos = lines[1].strip().find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            temp_f = float(temp_c * 9.0) / 5.0 + 32.0
            return (temp_c, temp_f)
    error(lines)
    return ('', '')
