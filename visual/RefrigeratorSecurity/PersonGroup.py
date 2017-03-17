# 
#	PersonGroup.py
#	Created by Dmitry Chulkov
#	This file provides a set of functions that allow to work with Person Groups in Face API
#

import http.client, urllib.request, urllib.parse, urllib.error, base64
import json

global KEY
KEY = '2f697c6db2264743b36b561859a28824'

# create person Group
# !!! If succsessfull - return empty object
def create(name, personGroupID):
    global KEY
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': KEY,
    }

    params = urllib.parse.urlencode({
    })

    body = { "name" : name }

    try:
        conn = http.client.HTTPSConnection('api.projectoxford.ai')
        conn.request("PUT", "/face/v1.0/persongroups/" + personGroupID + "?%s" % params, json.dumps(body), headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return data
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))


def getPersonGroup(groupID):
    global KEY
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': KEY,
    }

    params = urllib.parse.urlencode({
    })

    try:
        conn = http.client.HTTPSConnection('api.projectoxford.ai')
        conn.request("GET", "/face/v1.0/persongroups/" + groupID + "?%s" % params, "{body}", headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        data = data.decode('ascii')
        data = json.loads(data)
        return data
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))


def listPersonGroup():
    global KEY

    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': KEY,
    }

    params = urllib.parse.urlencode({
        # Request parameters
        #'start': '{string}',
        #'top': '1000',
    })

    try:
        conn = http.client.HTTPSConnection('api.projectoxford.ai')
        conn.request("GET", "/face/v1.0/persongroups?%s" % params, "{body}", headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        data = data.decode('ascii')
        data = json.loads(data)
        return data
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

		
# !!! If succsessfull - return empty object
def trainPersonGroup(personGroupID):
    global KEY

    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': KEY,
    }

    params = urllib.parse.urlencode({
    })

    try:
        conn = http.client.HTTPSConnection('api.projectoxford.ai')
        conn.request("POST", "/face/v1.0/persongroups/" + personGroupID + "/train?%s" % params, "{body}", headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return data
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))


def getPersonGroupTrainingStatus(personGroupID):
    global KEY

    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': KEY,
    }

    params = urllib.parse.urlencode({
    })

    try:
        conn = http.client.HTTPSConnection('api.projectoxford.ai')
        conn.request("GET", "/face/v1.0/persongroups/" + personGroupID + "/training?%s" % params, "{body}", headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        data = data.decode('ascii')
        data = json.loads(data)
        return data
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))
        return





