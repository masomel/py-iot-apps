# 
#	Person.py
#	Created by Dmitry Chulkov
#	This file provides a set of functions that allow to work with a single person in Face API
#

import http.client, urllib.request, urllib.parse, urllib.error, base64
import json

global KEY
KEY = '2f697c6db2264743b36b561859a28824'

def createPerson(personGroupID, name):
    global KEY

    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': KEY,
    }

    params = urllib.parse.urlencode({
    })

    body = {'name': name}

    try:
        conn = http.client.HTTPSConnection('api.projectoxford.ai')
        conn.request("POST", "/face/v1.0/persongroups/" + personGroupID + "/persons?%s" % params, json.dumps(body), headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        data = data.decode('ascii')
        data = json.loads(data)
        return data
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))
    return

    
def getPerson(personGroupID, personID):
    global KEY
    
    headers = {
            # Request headers
            'Ocp-Apim-Subscription-Key': KEY,
    }

    params = urllib.parse.urlencode({
    })

    try:
        conn = http.client.HTTPSConnection('api.projectoxford.ai')
        conn.request("GET", "/face/v1.0/persongroups/" + personGroupID + "/persons/" + personID + "?%s" % params, "{body}", headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        data = data.decode('ascii')
        data = json.loads(data)
        return data
    except Exception as e:
            print("[Errno {0}] {1}".format(e.errno, e.strerror))
    return

    
def listPersonsInPersonGroup(personGroupID):
    global KEY
	
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': KEY,
    }

    params = urllib.parse.urlencode({
    })

    try:
        conn = http.client.HTTPSConnection('api.projectoxford.ai')
        conn.request("GET", "/face/v1.0/persongroups/" + personGroupID + "/persons?%s" % params, "{body}", headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        data = data.decode('ascii')
        data = json.loads(data)
        return data
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror)) 
    return
	
    
def addPersonFace(personGroupID, personID, image, targetFace='{string}'):
    global KEY
    
    headers = {
        # Request headers
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': KEY,
    }

    params = urllib.parse.urlencode({
        # Request parameters
        #'targetFace': targetFace,
    })
    
    body = open(image, 'rb')

    try:
        conn = http.client.HTTPSConnection('api.projectoxford.ai')
        conn.request("POST", "/face/v1.0/persongroups/" + personGroupID + "/persons/" + personID + "/persistedFaces?%s" % params, body, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        data = data.decode('ascii')
        data = json.loads(data)
        return data
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))
    
    return

