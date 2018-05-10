#Database
#By Tyler Spadgenske

import mysql.connector
import time, cmds

class Database():
        def __init__(self):
                self.conn = mysql.connector.connect(user='root', password='raspberry', database='ANDY') #Ha ha. You know my password
                self.cursor = self.conn.cursor()
                self.objects = [None]
                self.scripts = [None]
                self.images = [None]
                self.color = None
                self.iceCream = None
                self.currentAge = None
                self.image = None
                self.seen = None
                self.bestie = None
                
        def get_object_data(self,target):
                query = ('SELECT id, object_name, script_path, image_path FROM objects')
                self.cursor.execute(query)

                for empid, object_name, image_path, file_path in self.cursor:
                        self.objects.append(str(object_name))
                        self.scripts.append(str(file_path))
                        self.images.append(str(image_path))

                self.num = 0
                for i in self.objects:
                        if i == target:
                                break
                        else:
                                self.num += 1
                                
                self.cursor.close()
                self.conn.close()

                return self.scripts[self.num], self.images[self.num]

        def get_people_data(self, target, data):
                #Get data from database
                query = ('SELECT id, first_name, favorite_color, favorite_ice_cream, age, image_path, last_seen, favorite_food FROM people')
                self.cursor.execute(query)
                for id, first_name, favorite_color, favorite_ice_cream, age, image_path, last_seen, favorite_food in self.cursor:

                        #Setup data
                        self.name = str(first_name)
                        if self.name == target:
                                self.color = str(favorite_color)
                                self.iceCream = str(favorite_ice_cream)
                                self.currentAge = str(age)
                                self.image = str(image_path)
                                self.seen = str(last_seen)
                                self.food = str(favorite_food)
                                break

                #Return data wanted
                if self.name == target:
                        if data == 'first_name':
                                return self.name
                        elif data == 'favorite_color':
                                return self.color
                        elif data == 'favorite_ice_cream':
                                return self.iceCream
                        elif data == 'age':
                                return self.currentAge
                        elif data == 'image_path':
                                return self.image
                        elif data == 'last_seen':
                                return self.seen
                        elif data == 'favorite_food':
                                return self.food
                        else:
                                return 'None'

        def add_person(self, name):
                cmds.Take(['', 'picture'])
                pic_num = open('/home/pi/ANDY/src/temp/pic.txt', 'r')
                pic = pic_num.readline().rstrip()
                pic = str(int(pic) - 1)
                time.sleep(5)
                
                name = name.lower().capitalize()
                seen = time.strftime("%Y%m%d") 
                new_person = ("INSERT INTO people (first_name, last_seen, image_path) VALUES ('" + name + "', " + seen + ", '/home/pi/ANDY/pictures/" + str(pic) + ".jpg')")
                time.sleep(5)

                self.cursor.execute(new_person)
                self.conn.commit()

        def add_person_data(self, name, data, target):
                new_data = ("UPDATE people SET " + target + "='" + str(data) + "' WHERE first_name='" + name + "'")
                self.cursor.execute(new_data)
                self.conn.commit()

                        
if __name__ == '__main__':   
        t = Database()
        test = t.get_people_data('Tyler','age')
        print(test)
