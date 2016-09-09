#!/usr/bin/python3
# Basic http client that posts the temperature of Sherrerd 320 to a basic server on cycles
# we send the current time and the temp reading in C and F

import tracer

import requests
import sched
from datetime import datetime, timedelta, timezone

from get_cur_temp import read_temp, error

def get_temp():
    server = 'http://www.cs.princeton.edu/~melara/pi_thermometer/temp_sensing_web_server.php'
    
    # get the current time
    cur_time = datetime.now(timezone(timedelta(hours=-5)))
    cur_time_str = cur_time.strftime("%a %d %b %Y, %I:%M%p")
    
    # get the current temp
    (celcius, fahrenheit) = read_temp()
    if (celcius == '' or fahrenheit == ''):
        error()
        exit()
    
    fahrenheit_str = "%.1f" % fahrenheit
    celcius_str = "%.1f" % celcius
    post_data = {}
    post_data['time'] = cur_time_str
    post_data['fahrenheit'] = fahrenheit_str
    post_data['celcius'] = celcius_str
    
    # need to specify the content type of the post request
    # otherwise, the PHP won't parse it or something
    hdr = {'Content-Type': 'application/x-www-form-urlencoded'}

    # send data to server
    resp = requests.post(server, data=post_data, headers=hdr)

    print(resp.status_code)

tracer.start_tracer(get_temp)
