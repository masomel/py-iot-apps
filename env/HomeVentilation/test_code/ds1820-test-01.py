from w1thermsensor import W1ThermSensor

T1id = '0008006b3137'
T2id = '0008006b2e67'


print "list all"
for s in W1ThermSensor.get_available_sensors():
    print (s.id, s.get_temperature())

#print "find T2"
#T2 = W1ThermSensor(16,T2id)

#print "finfd T1"
#T1 = W1ThermSensor(16,T1id)




