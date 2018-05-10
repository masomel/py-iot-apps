# 
#	Face.py
#	Created by Dmitry Chulkov
#	This file provides a set of functions that allow to detect face on image and identify person via Face API
#

import http.client, urllib.request, urllib.parse, urllib.error, base64
import json

global KEY
KEY = '2f697c6db2264743b36b561859a28824'

def detectjsonURL(url):
    global KEY
    
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': KEY,
    }

    params = urllib.parse.urlencode({
        # Request parameters
        'returnFaceId': 'true',
        'returnFaceLandmarks': 'false',
        'returnFaceAttributes': 'age',
    })

    body = { 'url' : url }


    try:
        conn = http.client.HTTPSConnection('api.projectoxford.ai')
        conn.request("POST", "/face/v1.0/detect?%s" % params, json.dumps(body), headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        data = data.decode('ascii')
        data = json.loads(data)
        return data
    except Exception as e:
        print(("[Errno {0}] {1}".format(e.errno, e.strerror)))


def detect(image):
    global KEY
    
    headers = {
        # Request headers
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': KEY,
    }

    params = urllib.parse.urlencode({
        # Request parameters
        'returnFaceId': 'true',
        'returnFaceLandmarks': 'false',
        'returnFaceAttributes': 'age',
    })

    body = open(image, 'rb')

    try:
        conn = http.client.HTTPSConnection('api.projectoxford.ai')
        conn.request("POST", "/face/v1.0/detect?%s" % params, body, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        data = data.decode('ascii')
        data = json.loads(data)
        return data
    except Exception as e:
        print(("[Errno {0}] {1}".format(e.errno, e.strerror)))
    


def identify(faceIDs, personGroupID):
    global KEY
    
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': KEY,
    }

    params = urllib.parse.urlencode({
    })
    
    body = {
                "personGroupId": personGroupID,
                "faceIds": faceIDs,
            }

    try:
        conn = http.client.HTTPSConnection('api.projectoxford.ai')
        conn.request("POST", "/face/v1.0/identify?%s" % params, json.dumps(body), headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        data = data.decode('ascii')
        data = json.loads(data)
        return data
    except Exception as e:
        print(("[Errno {0}] {1}".format(e.errno, e.strerror)))
    return



    
