import MySQLdb
db = MySQLdb.connect('localhost','root','', '')
cursor = db.cursor()
cursor.execute('CREATE TABLE EDISONTEMP (READING INT(50) auto_increment primary key, VALUE INT)')
cursor.execute('CREATE TABLE EDISONLIGHT (READING INT(50) auto_increment primary key, VALUE INT)')
db.commit()
db.close()
