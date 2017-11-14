import time
from datetime import datetime
import cam_lib

dt = datetime.now()
now = dt.strftime('%Y%m%d-%H%M%S')
name = '/tmp/'+ now + '.jpg'
print(name)

cam_lib.take_pic(name)
cam_lib.take_pic_def()
