import time, datetime
import serial
from _thread import start_new_thread

class FishFeederStatus:
	READY = 0
	ERROR = 1
	BUSY = 2
	ROTATING = 3
	DUMPING = 4
	CALIBRATING = 5
	
	@staticmethod
	def getMessage(status):
		if (status == FishFeederStatus.READY):
			return "Ready"
		if (status == FishFeederStatus.ERROR):
			return "Error"
		if (status == FishFeederStatus.BUSY):
			return "Busy"
		if (status == FishFeederStatus.ROTATING):
			return "Rotating"
		if (status == FishFeederStatus.DUMPING):
			return "Dumping"
		if (status == FishFeederStatus.CALIBRATING):
			return "Calibrating"

status = FishFeederStatus.READY
position = 0
start = 0
currentposition = 0
duration = 0
speed = 0.325919
timeleft = 0
progress = 0
moving = False
maxprogress = 0
onChangeStatus = None
onChangeProgress = None
ser = serial.Serial("/dev/ttyAMA0", 9600)
ser.open();

def _wait(timeout = 180):
	global status
	start = datetime.datetime.now()
	while (status != FishFeederStatus.READY and status != FishFeederStatus.ERROR and (datetime.datetime.now() - start).seconds < timeout):
		time.sleep(0.01)
		
	if (datetime.datetime.now() - start).seconds > timeout:
		status = FishFeederStatus.ERROR

def flash(r, g, b, duration):
	global status

	status = FishFeederStatus.BUSY
	ser.write(chr(105))
	ser.write(chr(r))
	ser.write(chr(g))
	ser.write(chr(b))
	ser.write(chr(int(duration * 10.0)))
	ser.write(chr(13))
	_wait()

def flashHex(hex, duration = 1):
	_NUMERALS = '0123456789abcdefABCDEF'
	_HEXDEC = {v: int(v, 16) for v in (x+y for x in _NUMERALS for y in _NUMERALS)}
	LOWERCASE, UPPERCASE = 'x', 'X'

	if (hex[0] == '#'):
		hex = hex[1:7]
	flash(_HEXDEC[hex[0:2]], _HEXDEC[hex[2:4]], _HEXDEC[hex[4:6]], duration);
	
def initializeMove(dest):
	global startt, moving, start, position, currentposition, timeleft

	dest = dest % 27
	if (dest < position):
		dest += 27
	startt = time.time()
	moving = True
	start = position
	currentposition = position
	position = dest
	timeleft = (position - start) / speed
	
def moveTo(dest):
	global status
	
	initializeMove(dest)
	status = FishFeederStatus.BUSY
	ser.write(chr(100))
	ser.write(chr(dest))
	ser.write(chr(13))
	_wait()
	
def move(amount):
	global status

	initializeMove(position + amount)
	status = FishFeederStatus.BUSY
	ser.write(chr(101))
	ser.write(chr(amount))
	ser.write(chr(13))
	_wait()

def dump():
	global status

	status = FishFeederStatus.BUSY
	ser.write(chr(102))
	ser.write(chr(13))
	_wait()

def moveToAndDump(dest):
	global status

	initializeMove(dest)
	status = FishFeederStatus.BUSY
	ser.write(chr(103))
	ser.write(chr(dest))
	ser.write(chr(13))
	_wait()

def calibrate():
	global status

	status = FishFeederStatus.BUSY
	ser.write(chr(104))
	ser.write(chr(13))
	_wait()

def getBrightness():
	global status

	ser.write(chr(106))
	ser.write(chr(13))
	result = ord(ser.read())
	status = FishFeederStatus.BUSY
	_wait()
	return result
	
def getPosition():
	global status
	
	ser.write(chr(107))
	ser.write(chr(13))
	result = ord(ser.read())
	status = FishFeederStatus.BUSY
	_wait(2)
	return result
	
#TODO getping

def getCalibrated():
	global status

	ser.write(chr(109))
	ser.write(chr(13))
	result = ord(ser.read())
	status = FishFeederStatus.BUSY
	_wait()
	return result == 1

def setCalibrated(value):
	global status
	
	status = FishFeederStatus.BUSY
	ser.write(chr(110))
	ser.write(chr((0,1)[value]))
	ser.write(chr(13))
	_wait()
	
def getErrorState():
	global status
	
	while (status != FishFeederStatus.READY):
		time.sleep(0.05)
	ser.write(chr(111))
	ser.write(chr(13))
	result = ord(ser.read())
	status = FishFeederStatus.BUSY
	_wait()
	return result == 1
	
def resetErrorState():
	global status
	
	status = FishFeederStatus.BUSY
	ser.write(chr(112))
	ser.write(chr(13))
	_wait()
	
def setOnChangeStatusListener(callback):
	global onChangeStatus
	onChangeStatus = callback

def setOnChangeProgressListener(callback):
	global onChangeProgress
	onChangeProgress = callback
	
def _setStatus(newstatus):
	global moving, status

	if (newstatus == FishFeederStatus.READY):
		moving = False
	if (status == newstatus):
		return
	if (not (status == FishFeederStatus.BUSY and newstatus == FishFeederStatus.READY)):
		if (not onChangeStatus is None):
			oldstatus = status
			status = newstatus
			onChangeStatus(oldstatus, newstatus)
	status = newstatus
		
def _setProgress(newprogress):
	global currentposition, timeleft, progress
	if (maxprogress != 0):
		currentposition = start + (position - start) * newprogress / maxprogress
		timeleft = (position - start) * (1.0 - newprogress) / speed
	progress = newprogress
	if (not onChangeProgress is None):
		onChangeProgress(newprogress)
	
def _seriallistener():
	global maxprogress, moving

	while (True):
		if (status != FishFeederStatus.READY):
			byte = ord(ser.read())
			if (byte == 1):
				_setStatus(FishFeederStatus.ERROR)
			elif (byte == 13):
				_setStatus(FishFeederStatus.READY)
			elif (byte == 14):
				_setStatus(FishFeederStatus.ROTATING)
			elif (byte == 15):
				_setStatus(FishFeederStatus.DUMPING)
			elif (byte == 16):
				_setStatus(FishFeederStatus.CALIBRATING)
			elif (byte >= 20):
				byte -= 20
				if (maxprogress == 0):
					maxprogress = byte
				if (maxprogress != 0):
					p = 1.0 * (maxprogress - byte) / maxprogress
					if (byte == 0):
						maxprogress = 0
						moving = False
						end = time.time()
					_setProgress(p)
					
def getSerializeable():
	result = {}
	result['position'] = position
	result['currentposition'] = currentposition
	result['start'] = start
	result['timeleft'] = timeleft
	result['moving'] = moving
	
	return result

start_new_thread(_seriallistener, ())