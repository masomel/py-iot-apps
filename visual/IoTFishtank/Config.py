import configparser

config = configparser.ConfigParser()
config.read('config.ini')

path = config.get('general', 'path')
size = config.getint('general', 'size')
preferOldContainers = config.getboolean('general', 'preferoldcontainers')

pbApiKey = config.get('pushbullet', 'apikey')
pbMinPushLevel = config.getint('pushbullet', 'minpushlevel')
pbDevices = config.get('pushbullet', 'devices').split(',')

dbHost = config.get('database', 'host')
dbUser = config.get('database', 'user')
dbPassword = config.get('database', 'password')
dbDatabase = config.get('database', 'database')

secretKey = config.get('server', 'secretkey')

pictureFolder = config.get('pics', 'folder')
pictureFilename = config.get('pics', 'filename')
pictureFilenameSmall = config.get('pics', 'filenamesmall')
pictureSizeSmall = config.get('pics', 'smallwidth')