import sys
sys.path.append('../../libs')

from datetime import datetime
import picamera

camera = picamera.PiCamera()

dt = datetime.now()
now = dt.strftime('%Y%m%d-%H%M%S')
name = now + '.jpg'
print(name)

camera.capture(name)
