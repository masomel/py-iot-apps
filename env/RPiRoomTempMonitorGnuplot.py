# msm: source - http://www.instructables.com/id/Raspberry-Pi-controlled-room-temperature-monitorin/?ALLSTEPS

from time import *
import time
import serial
import smtplib
import Gnuplot
import os
import sys

from_address = 'custom_email@gamil.com'
to_address1 = 'recipient1.mail.com'

to_address2 = 'recipient2.mail.com'

username = 'custom_email@@gmail.com'

password = 'custom_email_password'

timestamp = strftime("%d%b%Y %H:%M:%S ",localtime())

g = Gnuplot.Gnuplot(debug=debug)

g('cd "' + path + '"' )
g('set xdata time')

g('set timefmt "%d%b%Y %H:%M:%S"')

g('set format x "%H:%M\\n%d%b"')

g('set title " Daily Current Temperature Display"')

g('set key off')

g('set grid')
g('set xlabel "Time\\nDate"')

g('set yrange [15.0:35.0]')

g('set ylabel " Temperature "')

g('set datafile missing "NaN"')

g('set terminal png size 800,400')

g('set output "daily.png"')

g('plot "daily.dat" using 1:($3) with lines')
