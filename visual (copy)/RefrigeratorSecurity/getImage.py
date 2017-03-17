#
#   getImage.py
#   Created by Dmitry Chulkov
#   Provides function to take images from ip camera
#

import http.client, urllib.request, urllib.parse, urllib.error, base64

#   Parameters:
#       path - where to save image (example\\example\\example\\)
#       host - host of your ip camera
def fromIpCam(path, host):

    try:
        # request image from ip camera
        conn = http.client.HTTPConnection(host)
        conn.request("GET", "/photoaf.jpg")
        response = conn.getresponse()
        data = response.read()
        conn.close()
        # save image
        img = open(path + "image.jpg", "wb")
        img.write(data)
        img.close()        
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

    return

