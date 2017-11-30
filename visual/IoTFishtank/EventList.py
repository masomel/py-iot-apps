from Event import PictureEvent, LightEvent, FeedEvent
import datetime

names = ['Feed','Light','Take picture']

events = []
enabled = True
idcounter = 0
today = datetime.datetime.today().date()
	
def createEvent(type):
	if type == 0:
		return FeedEvent()
	elif type == 1:
		return LightEvent()
	elif type == 2:
		return PictureEvent()
	return None
	
def load(ini):
	global idcounter, enabled, events

	section = 'events'
	if not ini.has_section(section):
		raise Exception("Broken state.ini file")
	idcounter = ini.getint(section,'idcounter')
	enabled = ini.getboolean(section,'enabled')
	count = ini.getint(section,'count')
	events = []
	for i in range(count):
		event = createEvent(ini.getint('event' + str(i),'type'))
		event.readFromIni(ini, 'event' + str(i))
		events.append(event)

def save(ini):
	section = 'events'
	if not ini.has_section(section):
		ini.add_section(section)
	ini.set(section,'idcounter',str(idcounter))
	ini.set(section,'enabled',str(enabled))
	ini.set(section,'count',str(len(events)))
	i = 0
	for event in events:
		event.writeToIni(ini, 'event' + str(i))
		i += 1

def getSerializeable():
	return [event.getSerializeable() for event in events]

def update(params):
	global idcounter

	id = int(params['event'])
	type = int(params['type'])
	
	event = createEvent(type)
	event.setDayInt(int(params['day']))
	event.hour = int(params['hour'])
	event.minute = int(params['minute'])
	event.executed = event.timePassed()
	
	if type == 0:
		event.setFoodInt(int(params['food']))
		event.maxSaturation = float(params['maxsaturation'])
		event.minAmount = float(params['minamount'])
		event.maxAmount = float(params['maxamount'])
	elif type == 1:
		event.value = params['value'] == 'true'
	
	if id == -1:
		event.id = idcounter
		idcounter += 1
		events.append(event)
	else:
		event.id = id
		for i in range(len(events)):
			if events[i].id == id:
				events[i] = event
	return event

def getEvent(id):
	for event in events:
		if event.id == id:
			return event
	return None
	
def tick():
	global today
	
	if today != datetime.datetime.today().date():
		today = datetime.datetime.today().date()
		for event in events:
			event.executed = event.timePassed()
	if enabled:
		for event in events:
			event.tick()