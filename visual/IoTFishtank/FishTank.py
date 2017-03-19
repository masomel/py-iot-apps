import configparser
import datetime
import sys
import time

import FoodStore
import EventList
import Camera
import FishFeeder
import Lights
import Log

version = 0
saturation = 0
saturationchanged = datetime.datetime.now()
status = 'Ready'

inifilename = 'state.ini'
	
FishFeeder.position = FishFeeder.getPosition()

def save():
	status = configparser.ConfigParser()
	status.read(inifilename)
	
	section = 'status'
	if not status.has_section(section):
		status.add_section(section)
	
	status.set(section, 'saturation', str(saturation))
	status.set(section, 'saturationchanged', str(saturationchanged))
	status.set(section, 'version', str(version))
	status.set(section, 'Cameracounter', str(Camera.counter))
	
	FoodStore.save(status)
	EventList.save(status)
	Lights.save(status)
	
	with open(inifilename, 'w') as configfile:
		status.write(configfile)
		
def load():
	global version, saturation, saturationchanged

	status = configparser.ConfigParser()
	status.read(inifilename)
	
	FoodStore.load(status)
	EventList.load(status)
	Lights.load(status)
	
	section = 'status'
	if not status.has_section(section):
		raise Exception("Broken state.ini file")
	saturation = float(status.get(section, 'saturation'))
	saturationchanged = datetime.datetime.strptime(status.get(section, 'saturationchanged'), "%Y-%m-%d %H:%M:%S.%f")
	version = status.getint(section, 'version') + 1
	Camera.counter = status.getint(section,'Cameracounter')

def getSerializeable():
	nextEvent = getNextEvent()
	
	return {
		'container': FoodStore.getSerializeable(),
		'event': EventList.getSerializeable(),
		'version': version,
		'saturation': saturation,
		'saturationchanged': time.mktime(saturationchanged.timetuple()),
		'log': Log.getRecentEntries(15),
		'imagecount': Camera.counter,
		'status': status,
		'feeder': FishFeeder.getSerializeable(),
		'foodamount': getFoodAmount(),
		'autofeedamount': getAutoFeedAmount(),
		'nexteventtype': nextEvent.type if nextEvent is not None else None,
		'nexteventtime': time.mktime(nextEvent.getNextExecution().timetuple()) if nextEvent is not None else None,
		'nextlighteventtime': time.mktime(getNextLightEvent().getNextExecution().timetuple()) if getNextLightEvent() is not None else None,
		'lights': Lights.value,
		'scheduling': EventList.enabled
	}
	
def onFishFeederUpdate(oldstatus, newstatus):
	global status

	if (newstatus == FishFeeder.FishFeederStatus.CALIBRATING):
		Log.write(message = 'Calibrating fish feeder.', level = 1, startedby = 'FishFeeder')
	status = FishFeeder.FishFeederStatus.getMessage(newstatus)
	increaseVersion()

FishFeeder.setOnChangeStatusListener(onFishFeederUpdate)
	
def getSaturation():
	days = (datetime.datetime.now() - saturationchanged).total_seconds() / (60.0 * 60.0 * 24.0)
	return max(0, saturation - days)

def setSaturation(value):
	global saturation, saturationchanged
	
	saturation = value
	saturationchanged = datetime.datetime.now()
	increaseVersion()
	
def getFoodAmount():
	amount = 0
	for container in FoodStore.container:
		if container.food != 0:
			amount += container.amount
	return amount

def getAutoFeedAmount():
	candidates = set()
	for event in EventList.events:
		if event.type == 0:
			candidates = candidates.union(set(event.getContainerCandidates()))
	amount = 0
	for container in list(candidates):
		amount += container.amount
	return amount
		
def getNextEvent():
	time = None
	result = None
	for event in EventList.events:
		if time == None:
			result = event
			time = event.getNextExecution()
		else:
			if (event.getNextExecution() < time):
				result = event
				time = event.getNextExecution()
	return result
	
def getNextLightEvent():
	time = None
	result = None
	for event in EventList.events:
		if event.type == 1 and event.value != Lights.value:
			if time == None:
				result = event
				time = event.getNextExecution()
			else:
				if (event.getNextExecution() < time):
					result = event
					time = event.getNextExecution()
	return result
	
def increaseVersion():
	global version
	
	version += 1
	
def updateStatus(newStatus):
	global status
	
	status = newStatus
	increaseVersion()
	
def tick():
	EventList.tick()
	
load()