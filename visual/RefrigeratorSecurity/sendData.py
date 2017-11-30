#
#   sendData.py
#   Created by Dmitry Chulkov
#   Provide function for sending data to Node-Red
#

import http.client, urllib.request, urllib.parse, urllib.error, base64
import json


# Parameters:
#   data - dictionary object that will be sent to Node-Red, to /notify url
def toNodeRed(data):

    host = '127.0.0.1:1880'
    
    headers = {
        'Content-Type': 'application/json'
        }
    
    try:
        conn = http.client.HTTPConnection(host)
        conn.request("POST", "/notify", body=json.dumps(data), headers=headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        data = data.decode('ascii')
        #data = json.loads(data)
        #return data
        print(data)
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))
    return







