# 
#	recognition.py
#	Created by Dmitry Chulkov
#	This file provides set of functions that allow to detect faces on multiple images at one time,
#       add multiple faces to person and get name of person on image.
#

import Person
import PersonGroup
import Face

import os
import json

# this function addes faces to specified person in specified group.
# to do this you have to provide folder with images of person that you want to add,
# all images have to have only one face and this face have to be face of specified person.
# It's better to prepare special folder with such images and then proceed with this function.
def addFacesToPerson(folderWithImages, personID, personGroupID):

    files = os.listdir(folderWithImages)
    
    for i in range(len(files)):
        img_addr = folderWithImages + files[i]
        result = Person.addPersonFace(personGroupID, personID, img_addr)
        if "error" in result:
            print((json.dumps(result, indent=2)))
        else:
            print(("Added " + str(i+1) + " faces... "))
    print("Done adding faces!")
    return

# Function prints out json in readable format        
def printResJson(result):
    print((json.dumps(result, indent=2)))
    return

# using module 'Face' and function 'detect' print out result of detecting faces on
# on images in specified directory
def detectFaceOnImages(path):
    files = os.listdir(path)
    for i in range(len(files)):
        img_addr = path + files[i]
        result = Face.detect(img_addr)
        print("*************")
        print(("image: " + img_addr))
        printResJson(result)
    return


# params: path to image example\\example\\
def checkPerson(image, personGroupID):
    
    # detect face 
    result = Face.detect(image)
    if len(result) > 0 and 'faceId' in result[0]:
        data = Face.identify([result[0]['faceId']], personGroupID)
        # get person name
        
        if len(data[0]["candidates"]) > 0:
            persID = data[0]["candidates"][0]["personId"]
            res = Person.getPerson(personGroupID, persID)
            name = res["name"]
        else:
            name = "stranger"
        return name
    else:
        print("No face detected")
    return "noface"



