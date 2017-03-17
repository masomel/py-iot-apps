#!/bin/sh
# humidity_monitor.sh
# run the humidity monitor program


# to install do:
# chmod 755 humidity_monitor.sh
# mkdir logs
# sudo crontab -e
# and enter the following line
# @reboot sh /home/pi/humidity-monitor/humidity_monitor.sh >/home/pi/logs/cronlog 2>&1
cd /home/pi/humidity-monitor
sudo python /home/pi/humidity-monitor/humidity_monitor.py
