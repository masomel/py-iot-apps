#
#   checkAccess.py
#   Created by: Dmitry Chulkov
#

import datetime

# make our access list
global trustedPeople
trustedPeople = { 'dmitry' : '08:25 - 22:00', 
                      'anastasia' : 'full'
                    }

# function checks access permission to refrigerator for person
# this function returns dictionaty with status of access in the form
# status = { 'trustedPerson': True/False,
#            'access' : True/False }
def check(personName):
    global trustedPeople

    # create dictionaty to return
    status = {}
    
    # return false immediately if person not in our list
    if personName not in trustedPeople:
        status['trustedPerson'] = False
        status['access'] = False
        return status
    else:
        status['trustedPerson'] = True

    # get access status for person
    access = trustedPeople[personName]

    # if person has full access return true immediately
    if access == 'full':
        status['access'] = True
        return status

    # get current time
    now = datetime.datetime.now()
    # create objects for comparin with current time
    start = now.replace(hour=int(access[0:2]), minute=int(access[3:5]))
    end = now.replace(hour=int(access[8:10]), minute=int(access[11:]))

    if now > start and now < end:
        status['access'] = True
        return status
    else:
        status['access'] = False
        return status
    
       
    
