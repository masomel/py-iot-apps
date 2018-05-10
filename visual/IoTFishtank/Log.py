import MySQLdb
import time
import sys
import traceback
from _thread import *

from pushbullet import PushBullet

import FishTank
import Camera
import Config

loglevels = ['log','info','event','warning','error','permanenterror']

pushbullet = PushBullet(Config.pbApiKey)
last = {}

def connectToDB():
	return MySQLdb.connect(Config.dbHost, Config.dbUser, Config.dbPassword, Config.dbDatabase)

def getRecentEntries(count = -1, minlevel = 0, page = 1):
	global last

	loglines = None
	db = connectToDB()
	try:
		offset = max(0, count * (page - 1))
		cursor = db.cursor()
		cursor.execute ("SELECT * FROM log WHERE level >= " + str(minlevel) + " ORDER BY time DESC" + (" LIMIT " + str(count) if count != -1 else "") + " OFFSET " + str(offset))
		db.close()
		loglines = list(cursor.fetchall())
	except:
		traceback.print_exec(file = sys.stdout)
		return last

	for i in range(len(loglines)):
		loglines[i] = list(loglines[i])
		loglines[i][1] = time.mktime(loglines[i][1].timetuple())

	last = loglines
	return loglines

def write(message, level = 0, image = 0, startedby = 'server', title = None):
	db = connectToDB()
	try:
		cursor = db.cursor()
		cursor.execute("INSERT INTO log (time, message, level, image, startedby) values (NOW(), '" + message + "', " + str(level) + ", " + str(image) + ", '" + startedby + "')")
		db.commit()
		db.close()
	except:
		traceback.print_exec(file = sys.stdout)
	if level >= Config.pbMinPushLevel:
		for device in Config.pbDevices:
			if (image == 0):
				start_new_thread(pushbullet.pushNote, (device, title if title != None else 'Fishtank (' + loglevels[level] + ')',message))
			else:
				start_new_thread(pushbullet.pushFile, (device, title if title != None else 'Fishtank (' + loglevels[level] + ')', message, open(Camera.getPictureFilename(image), "rb")));
	FishTank.increaseVersion()
	FishTank.save()