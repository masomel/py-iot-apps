from _thread import *
from flask import *
import json
import string
import datetime
import time
import configparser
from flask_login import *
from flask.ext.login import (LoginManager, UserMixin, login_required, login_user, logout_user, current_user)
import hashlib
import flask.ext.login

import Config
import EventList
import Log
import FishTank
import FoodStore
import Camera
import Lights
import FishFeeder

class User(UserMixin):
    def __init__(self, username, hash):
        self.name = username
        self.hash = hash

    @property
    def id(self):
        return self.name

def loadUsers():
	ini = configparser.ConfigParser()
	ini.read('users.ini')

	usernames = ini.sections()
	users = [User(username, ini.get(username,'hash')) for username in usernames]

	return users

users = loadUsers()

login_manager = LoginManager()
app = Flask(__name__, static_folder='../', static_url_path='')
app.secret_key = Config.secretKey
login_manager.init_app(app)

#Enable this only in development mode
#start_new_thread(app.run, ("0.0.0.0",), {"threaded": True})
	# 0.0.0.0 - visible for outside network
	# threaded: handle multiple requests at once
app.config.update(PROPAGATE_EXCEPTIONS = True)

@login_manager.user_loader
def load_user(userid):
	for user in users:
		if user.name == userid:
			return user
	return None

@app.route('/')
def root():
	return app.send_static_file('index.html')

@app.route("/api/status")
def getStatus():
	data = FishTank.getSerializeable()
	data['user'] = current_user.name if current_user.is_authenticated() else None
	return Response(json.dumps(data), mimetype='application/json')

@app.route("/api/log")
def getLog():
	data = Log.getRecentEntries(count = int(request.args.get('entries')), minlevel = int(request.args.get('minlevel')), page = int(request.args.get('page')))
	return Response(json.dumps(data), mimetype='application/json')

@app.route("/api/note", methods=['POST'])
@login_required
def addLogNote():
	Log.write('Note: ' + request.form['note'], level = int(request.form['level']), image = 0, startedby = current_user.id, title = 'Note');
	return 'ok'

@app.route("/api/updatecontainers", methods=['POST'])
@login_required
def updateContainers():
	containers = string.split(request.form['containers'], ',')
	food = int(request.form['food'])
	amount = float(request.form['amount'])
	priority = int(request.form['priority'])
	
	now = datetime.datetime.now()
	for c in containers:
		if (c == ''):
			continue
		if (food != -1):
			FoodStore.container[int(c)].food = food
		if (amount != -1):
			FoodStore.container[int(c)].amount = amount
		if (priority != -1):
			FoodStore.container[int(c)].priority = priority
		if (food != -1 and amount != -1):
			FoodStore.container[int(c)].filled = now

	Log.write(message = 'Updated containers (' + str(len(containers)-1) + ' containers set)', startedby = current_user.id);
	return 'ok'

@app.route("/api/updateevent", methods=['POST'])
@login_required
def updateEvent():
	try:
		event = EventList.update(request.form)
		Log.write(message = ('Updated' if request.form['event'] != '-1' else 'Created') + ' event (' + EventList.names[event.type] + ' at ' + str(event.hour) + ':' + ('0' if event.minute < 10 else '') + str(event.minute) + ')', startedby = current_user.id)
	except:
		return 'Invalid event data.', 400
	return 'ok'

@app.route("/api/deleteevent", methods=['POST'])
@login_required
def deleteEvent():
	event = EventList.getEvent(int(request.form['id']))
	if event == None:
		return 'Event not found', 404
	EventList.events.remove(event)
	Log.write(message = 'Deleted event (' + EventList.names[event.type] + ' at ' + str(event.hour) + ':' + ('0' if event.minute < 10 else '') + str(event.minute) + ')', startedby = current_user.id)
	return 'ok'

@app.route("/api/takepicture", methods=['POST'])
def takePicture():
	if not current_user.is_authenticated() and not Lights.value:
		return 'Can&#039;t take a picture while the lights are off.', 400
		
	if not current_user.is_authenticated() and datetime.datetime.now() - Camera.lastPictureTaken < datetime.timedelta(minutes = 5):
		return 'Taking too many pictures, please wait ' + str(int((Camera.lastPictureTaken + datetime.timedelta(minutes = 5) - datetime.datetime.now()).seconds / 60) + 1) + str(' minutes.'), 400
	
	try:
		id = Camera.takePicture();
		username = 'guest'
		if current_user.is_authenticated():
			username = current_user.id
		Log.write(message = 'Took picture', level = 1, image = id, startedby = username)
	except Camera.NoCameraException:
		return 'Can''t take a picture: No camera found.', 500
	except:
		return 'Error while trying to take a picture', 500
	return 'ok'

@app.route("/api/switchlights", methods=['POST'])
@login_required
def switchLights():
	Lights.switch()
	Log.write(message = 'Switched lights (' + ('On' if Lights.value else 'Off') + ')', level = 1, startedby = current_user.id)
	return 'ok'

@app.route("/api/flashled", methods=['POST'])
def flashLED():
	FishFeeder.flashHex(request.form['color'],1)
	return 'ok'

@app.route("/api/calibrate", methods=['POST'])
@login_required
def calibrate():
	FishFeeder.calibrate()
	
	if FishFeeder.status == FishFeeder.FishFeederStatus.ERROR:
		Log.write(message = 'Moving feeder failed (mechanical failure).', level = 5, startedby = current_user.id)
		return 'ok'
	
	Log.write(message = 'Calibrated feeder', level = 1, startedby = current_user.id)
	return 'ok'

@app.route("/api/checkforupdate")
def checkForUpdate():
	oldversion = int(request.args['version'])
	timeout = 10
	tstart = time.time()
	while (time.time() < tstart + timeout):
		if (FishTank.version > oldversion):
			return 'true'
		time.sleep(0.1)
	return 'false'

@app.route("/api/move", methods=['POST'])
@login_required
def moveFeeder():
	FishFeeder.moveTo(int(request.form['to']))
	
	if FishFeeder.status == FishFeeder.FishFeederStatus.ERROR:
		Log.write(message = 'Moving feeder failed (mechanical failure).', level = 5, startedby = current_user.id)
		return 'ok'
	
	Log.write(message = 'Moved feeder to position ' + str(int(request.form['to'])+1), level = 1, startedby = current_user.id)
	return 'ok'

@app.route("/api/dump", methods=['POST'])
def dump():
	index = int(request.form['to'])
	if not current_user.is_authenticated():
		if FoodStore.container[index].amount == 0:
			return 'Can''t feed an empty container.', 400
		if not Lights.value:
			return 'Can''t feed while lights are off.', 400
		if FishTank.getSaturation() > 1:
			return 'Can''t feed: Fish are not hungry.', 400
		if FoodStore.container[index].priority >= 2:
			return 'Can''t feed a locked container.', 400
	
	username = 'guest'
	if current_user.is_authenticated():
		username = current_user.id	
	
	container = FoodStore.container[index]
	FishFeeder.moveToAndDump(index)
	if FishFeeder.status == FishFeeder.FishFeederStatus.ERROR:
		Log.write(message = 'Manual feeding failed (mechanical failure).', level = 5, startedby = username)
		return 'ok'
	
	imageId = 0
	if not current_user.is_authenticated():
		FishTank.updateStatus('Waiting...')
		time.sleep(4)
		imageId = Camera.tryTakePicture();
	
	oldsaturation = FishTank.getSaturation()
	if container.amount != 0:
		FishTank.setSaturation(oldsaturation + container.amount)
	Log.write(title = "Fed fish", message = 'Manually fed container ' + str(container.index + 1) + ' (Food ' + str(container.food) + '), Saturation: ' + "{0:.1f}".format(oldsaturation) + ' -> ' + "{0:.1f}".format(oldsaturation + container.amount) + ' (+' + "{0:.1f}".format(container.amount) + ')', image = imageId, level = 2 if container.amount != 0 else 0, startedby = username)
	container.empty()
	FishTank.increaseVersion()
	FishTank.save()
	return 'ok'

@app.route("/api/enableschedule", methods=['POST'])
@login_required
def enableSchedule():
	EventList.enabled = request.values.get('value') == 'true'
	Log.write(title = "Enabled Scheduling" if EventList.enabled else "Disabled Scheduling", message = "Enabled Scheduling" if EventList.enabled else "Disabled Scheduling", level = 0, startedby = current_user.id)
	return 'ok'

@app.route('/api/login', methods=['POST'])
def login():
	user = load_user(request.values.get('username'))
	hashalgorithm = hashlib.sha512()
	hashfailed = False
	try:
		hashalgorithm.update(request.values.get('password'))
	except:
		hashfailed = True
	if not hashfailed and user and user.hash == hashalgorithm.hexdigest():
		login_user(user, remember = True)
		print(('login successful (' + user.name + ')'))
		return 'ok'
	else:
		print(('login failed (' + request.values.get('username') + ')'))
		return 'Login failed', 401

@app.route("/api/logout", methods=['POST'])
@login_required
def logout():
	print(('user logged out (' + current_user.name + ')'))
	logout_user()
	return redirect('/');