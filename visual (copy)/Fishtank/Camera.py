import pygame.camera
import pygame.image
import pygame.transform
import datetime

import Config
import FishTank
import Log

counter = 0

class NoCameraException(Exception):
	pass

pygame.camera.init()
try:
	cam = pygame.camera.Camera(pygame.camera.list_cameras()[0], (1280, 720))
except:
	cam = None
	print("No camera found")
	
lastPictureTaken = datetime.datetime.fromtimestamp(0)
		
def takePicture():
	global counter, lastPictureTaken

	if cam == None:
		raise NoCameraException('To take a picture, a camera must be connected to a USB port!')
	
	FishTank.updateStatus('Taking picture...')
	lastPictureTaken = datetime.datetime.now()
	
	counter += 1
	
	cam.start()
	img = cam.get_image()
	cam.stop()
	
	FishTank.updateStatus('Saving picture...')
	pygame.image.save(img, getPictureFilename(counter))
	pygame.image.save(pygame.transform.scale(img, (int(Config.pictureSizeSmall), int(int(Config.pictureSizeSmall) * 720 / 1280))), getPictureFilenameSmall(counter))
	
	FishTank.updateStatus('Ready')
	return counter
	
def tryTakePicture():
	try:
		return takePicture()
	except:
		Log.write(message = 'Failed to take a picture. No camera found.', level = 4)
		return 0

def getPictureFilename(index):
	return Config.path + Config.pictureFolder + Config.pictureFilename.format(str(index))
	
	
def getPictureFilenameSmall(index):
	return Config.path + Config.pictureFolder + Config.pictureFilenameSmall.format(str(index))