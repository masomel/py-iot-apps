from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import sys
import time
import json
import os
import RPi.GPIO as GPIO


# These are my AWS IoT login and certificates
host = "**********.iot.us-east-1.amazonaws.com"
cert_path = os.path.realpath(__file__).rstrip(os.path.basename(__file__)) + "cert/"
rootCAPath = cert_path + "root-CA.crt"
certificatePath = cert_path + "**********-certificate.pem.crt"
privateKeyPath = cert_path + "**********-private.pem.key"
shadowClient = "CoffeeMachine_RaspberryPi"


# Parameters CoffeeMachine
CoffeeChoice = ["", "LATTE", "MACCHIATO", "CAPPUCCINO", "REGULAR"]
CoffeeChoice_Selected = CoffeeChoice.index("")

RegularStrength = ["", "DARK", "MEDIUM", "MILD"]
RegularStrength_Selected = RegularStrength.index("")

NumberOfCups = ["", "ONE", "TWO"]
NumberOfCups_Selected = NumberOfCups.index("")

Base_LED_One_Status = ["READY", "OFF"]
Base_LED_One_StatusSelected = Base_LED_One_Status.index("OFF")

Power_Status = ["OFF", "ON"]
Power_StatusSelected = Power_Status.index("OFF")

Base_LED_Power_Status = ["OFF", "ERROR", "BUSY", "READY"]
Base_LED_Power_StatusSelected = Base_LED_Power_Status.index("OFF")
Base_LED_Power_StatusSelected_last = Base_LED_Power_Status.index("OFF")

Base_LED_Two_Status = ["READY", "OFF"]
Base_LED_Two_StatusSelected = Base_LED_One_Status.index("OFF")

Lid_Status = ["CLOSED", "OPEN"]
Lid_StatusSelected = Lid_Status.index("CLOSED")




def IoT_to_Raspberry_Change_Power(ShadowPayload):
    global Power_StatusSelected, CoffeeChoice_Selected, RegularStrength_Selected, NumberOfCups_Selected
    # Desired = POWER change
    if (ShadowPayload == "ON" and Power_Status[Power_StatusSelected] == "OFF"): #Check if machine is indeed OFF
        GPIO.output(Base_BUT_Power, True) #Button press imitation send to the optocoupler
        time.sleep(0.1)
        GPIO.output(Base_BUT_Power, False)
        time.sleep(0.1)
        CoffeeChoice_Selected_LED() #as the machine is powering ON now, one of the LEDs will turn on, find the status
        RegularStrength_Selected_LED() #as the machine is powering ON now, one of the LEDs will turn on, find the status
        JSONPayload = '{ "state" : {'+\
                            '"reported": {'+\
                                '"Power": "' + Power_Status[Power_StatusSelected] + '", '+\
                                '"Start": "NO", '+\
                                '"CoffeeChoice": "' + CoffeeChoice[CoffeeChoice_Selected] + '", '+\
                                '"RegularStrength": "' + RegularStrength[RegularStrength_Selected] + '", '+\
                                '"NumberOfCups": "' + NumberOfCups[NumberOfCups_Selected] + '" '+\
                            '} '+\
                        '} '+\
                    '}'
        myDeviceShadow.shadowUpdate(JSONPayload, IoTShadowCallback_Update, 5) #Send the new status as REPORTED values

    elif (ShadowPayload == "OFF" and Power_Status[Power_StatusSelected] == "ON"): #Check if machine is indeed ON
        GPIO.output(Base_BUT_Power, True) #Button press imitation send to the optocoupler
        time.sleep(0.1)
        GPIO.output(Base_BUT_Power, False)
        Power_StatusSelected = Power_Status.index("OFF")
        CoffeeChoice_Selected = CoffeeChoice.index("") #LEDs will now be off
        RegularStrength_Selected = RegularStrength.index("") #LEDs will now be off
        NumberOfCups_Selected = NumberOfCups.index("")
        JSONPayload = '{ "state" : {'+\
                            '"reported": {'+\
                                '"Power": "' + Power_Status[Power_StatusSelected] + '", '+\
                                '"Start": "NO", '+\
                                '"CoffeeChoice": "' + CoffeeChoice[CoffeeChoice_Selected] + '", '+\
                                '"RegularStrength": "' + RegularStrength[RegularStrength_Selected] + '", '+\
                                '"NumberOfCups": "' + NumberOfCups[NumberOfCups_Selected] + '" '+\
                            '}, '+\
                            '"desired": {'+\
                                '"Power": "' + Power_Status[Power_StatusSelected] + '", '+\
                                '"Start": "NO", '+\
                                '"CoffeeChoice": "' + CoffeeChoice[CoffeeChoice_Selected] + '", '+\
                                '"RegularStrength": "' + RegularStrength[RegularStrength_Selected] + '", '+\
                                '"NumberOfCups": "' + NumberOfCups[NumberOfCups_Selected] + '" '+\
                            '} '+\
                        '} '+\
                    '}'
        myDeviceShadow.shadowUpdate(JSONPayload, IoTShadowCallback_Update, 5) #Send the new status as REPORTED values

        
    
def IoT_to_Raspberry_Change_CoffeeChoice(ShadowPayload):
    global CoffeeChoice_Selected, RegularStrength_Selected
    # Desired = COFFEE CHOICE change
    CoffeeChoice_Selected_LED() #Double check LED status
    if (ShadowPayload != "" and CoffeeChoice[CoffeeChoice_Selected] != "" and Power_Status[Power_StatusSelected] == "ON"): #check if status or desired is not an empty value
        while (CoffeeChoice.index(ShadowPayload.upper()) > CoffeeChoice_Selected): #current setting does not match desired (needs to tab down)
            GPIO.output(CoffeeChoice_BUT_Down, True) #Button press imitation send to the optocoupler
            time.sleep(0.1)
            GPIO.output(CoffeeChoice_BUT_Down, False)
            time.sleep(0.1)
            CoffeeChoice_Selected_LED()

        while (CoffeeChoice.index(ShadowPayload.upper()) < CoffeeChoice_Selected): #current setting does not match desired (needs to tab up)
            GPIO.output(CoffeeChoice_BUT_Up, True) #Button press imitation send to the optocoupler
            time.sleep(0.1)
            GPIO.output(CoffeeChoice_BUT_Up, False)
            time.sleep(0.1)
            CoffeeChoice_Selected_LED()

        RegularStrength_Selected_LED() #Double check LED status
        JSONPayload = '{ "state" : {'+\
                            '"reported": {'+\
                                '"CoffeeChoice": "' + CoffeeChoice[CoffeeChoice_Selected] + '", '+\
                                '"RegularStrength": "' + RegularStrength[RegularStrength_Selected] + '" '+\
                            '} '+\
                        '} '+\
                    '}'
        myDeviceShadow.shadowUpdate(JSONPayload, IoTShadowCallback_Update, 5) #Send the new status as REPORTED values
    

def IoT_to_Raspberry_Change_RegularStrength(ShadowPayload):
    global CoffeeChoice_Selected, RegularStrength_Selected
    # Desired = REGULAR STRENGTH change
    CoffeeChoice_Selected_LED() #Double check LED status
    RegularStrength_Selected_LED() #Double check LED status

    if (ShadowPayload != "" and RegularStrength[RegularStrength_Selected] != "" and Power_Status[Power_StatusSelected] == "ON"): #check if status or desired is not an empty value
        if (CoffeeChoice.index("REGULAR") == CoffeeChoice_Selected): # Only possible if current selection is Regular
            while (RegularStrength.index(ShadowPayload.upper()) > RegularStrength_Selected): #current setting does not match desired (needs to tab down)
                GPIO.output(RegularStrength_BUT_Down, True) #Button press imitation send to the optocoupler
                time.sleep(0.1)
                GPIO.output(RegularStrength_BUT_Down, False)
                time.sleep(0.1)
                RegularStrength_Selected_LED()
                
            while (RegularStrength.index(ShadowPayload.upper()) < RegularStrength_Selected): #current setting does not match desired (needs to tab up)
                GPIO.output(RegularStrength_BUT_Up, True) #Button press imitation send to the optocoupler
                time.sleep(0.1)
                GPIO.output(RegularStrength_BUT_Up, False)
                time.sleep(0.1)
                RegularStrength_Selected_LED()

            JSONPayload = '{ "state" : {'+\
                                '"reported": {'+\
                                    '"RegularStrength": "' + RegularStrength[RegularStrength_Selected] + '" '+\
                                '} '+\
                            '} '+\
                        '}'
            myDeviceShadow.shadowUpdate(JSONPayload, IoTShadowCallback_Update, 5) #Send the new status as REPORTED values



def IoT_to_Raspberry_Change_NumberOfCups(ShadowPayload):
    global NumberOfCups_Selected
    # Desired = number of cups selecction
    # no action required, will be used with Start option
    NumberOfCups_Selected = NumberOfCups.index(ShadowPayload)
    JSONPayload = '{ "state" : {'+\
                        '"reported": {'+\
                            '"NumberOfCups": "' + NumberOfCups[NumberOfCups_Selected] + '" '+\
                        '} '+\
                    '} '+\
                '}'
    myDeviceShadow.shadowUpdate(JSONPayload, IoTShadowCallback_Update, 5) #Send the new status as REPORTED values



def IoT_to_Raspberry_Change_Start(ShadowPayload):
    global Power_StatusSelected, CoffeeChoice_Selected, RegularStrength_Selected, NumberOfCups_Selected
    # Desired = Start
    if (ShadowPayload == "YES"):
        time.sleep (5)
        while (Base_LED_Power_Status[Base_LED_Power_StatusSelected] != "READY"): #Only goes through if the machine is in READY state, otherwise it loops waiting for becoming ready
            time.sleep (1)
        else:
            time.sleep (1)
            if (NumberOfCups[NumberOfCups_Selected] == "ONE" and Base_LED_One_Status[Base_LED_One_StatusSelected] == "READY"): #Only goes trhough if the machine is in READY state for 1 cup
                print("Ready for one cup")
                GPIO.output(Base_BUT_One, True) #Button press imitation send to the optocoupler
                time.sleep(0.1)
                GPIO.output(Base_BUT_One, False)
                time.sleep(0.1)
                JSONPayload = '{ "state" : {'+\
                                    '"reported": {'+\
                                        '"Start":"YES" '+\
                                    '} '+\
                                '} '+\
                            '}'
                myDeviceShadow.shadowUpdate(JSONPayload, IoTShadowCallback_Update, 5) #Send the new status as REPORTED values
            elif (NumberOfCups[NumberOfCups_Selected] == "TWO" and Base_LED_Two_Status[Base_LED_Two_StatusSelected] == "READY"): #Only goes trhough if the machine is in READY state for 2 cups
                print("Ready for two cups")
                GPIO.output(Base_BUT_Two, True) #Button press imitation send to the optocoupler
                time.sleep(0.1)
                GPIO.output(Base_BUT_Two, False)
                time.sleep(0.1)
                JSONPayload = '{ "state" : {'+\
                                    '"reported": {'+\
                                        '"Start":"YES" '+\
                                    '} '+\
                                '} '+\
                            '}'
                myDeviceShadow.shadowUpdate(JSONPayload, IoTShadowCallback_Update, 5) #Send the new status as REPORTED values
            # Coffee is made, now wait 30 seconds and power off
            time.sleep (60)
            GPIO.output(Base_BUT_Power, True) #Button press imitation send to the optocoupler
            time.sleep(0.1)
            GPIO.output(Base_BUT_Power, False)
            Power_StatusSelected = Power_Status.index("OFF")
            CoffeeChoice_Selected = CoffeeChoice.index("") #LEDs will now be off
            RegularStrength_Selected = RegularStrength.index("") #LEDs will now be off
            NumberOfCups_Selected = NumberOfCups.index("")
            JSONPayload = '{ "state" : {'+\
                                '"reported": {'+\
                                    '"Power": "' + Power_Status[Power_StatusSelected] + '", '+\
                                    '"Start": "NO", '+\
                                    '"CoffeeChoice": "' + CoffeeChoice[CoffeeChoice_Selected] + '", '+\
                                    '"RegularStrength": "' + RegularStrength[RegularStrength_Selected] + '", '+\
                                    '"NumberOfCups": "' + NumberOfCups[NumberOfCups_Selected] + '" '+\
                                '}, '+\
                                '"desired": {'+\
                                    '"Power": "' + Power_Status[Power_StatusSelected] + '", '+\
                                    '"Start": "NO", '+\
                                    '"CoffeeChoice": "' + CoffeeChoice[CoffeeChoice_Selected] + '", '+\
                                    '"RegularStrength": "' + RegularStrength[RegularStrength_Selected] + '", '+\
                                    '"NumberOfCups": "' + NumberOfCups[NumberOfCups_Selected] + '" '+\
                                '} '+\
                            '} '+\
                        '}'
            myDeviceShadow.shadowUpdate(JSONPayload, IoTShadowCallback_Update, 5) #Send the new status as REPORTED values




# Shadow callback for when a DELTA is received (this happens when Lamda does set a DESIRED value in IoT)
def IoTShadowCallback_Delta(payload, responseStatus, token):
#    global Power_StatusSelected, CoffeeChoice_Selected, RegularStrength_Selected, NumberOfCups_Selected
    print(responseStatus)
    payloadDict = json.loads(payload)
    print(("++DELTA++ version: " + str(payloadDict["version"])))

    # Desired = POWER change
    if ("Power" in payloadDict["state"]):
        print(("Power: " + str(payloadDict["state"]["Power"])))
        IoT_to_Raspberry_Change_Power(str(payloadDict["state"]["Power"]))

    # Desired = COFFEE CHOICE change
    if ("CoffeeChoice" in payloadDict["state"]):
        print(("CoffeeChoice: " + str(payloadDict["state"]["CoffeeChoice"])))
        IoT_to_Raspberry_Change_CoffeeChoice(str(payloadDict["state"]["CoffeeChoice"]))

    # Desired = REGULAR STRENGTH change
    if ("RegularStrength" in payloadDict["state"]):
        print(("RegularStrength: " + str(payloadDict["state"]["RegularStrength"])))
        IoT_to_Raspberry_Change_RegularStrength(str(payloadDict["state"]["RegularStrength"]))

    # Desired = number of cups selecction
    if ("NumberOfCups" in payloadDict["state"]):
        print(("NumberOfCups: " + str(payloadDict["state"]["NumberOfCups"])))
        IoT_to_Raspberry_Change_NumberOfCups(str(payloadDict["state"]["NumberOfCups"]))

    # Desired = Start
    if ("Start" in payloadDict["state"]):
        print(("Start: " + str(payloadDict["state"]["Start"])))
        IoT_to_Raspberry_Change_Start(str(payloadDict["state"]["Start"]))
            



# Shadow callback GET for setting initial status
def IoTShadowCallback_Get(payload, responseStatus, token):
    print(responseStatus)
    payloadDict = json.loads(payload)
    print(("++GET++ version: " + str(payloadDict["version"])))
    if ("Power" in payloadDict["state"]["desired"]):
        if(str(payloadDict["state"]["reported"]["Power"]).upper() != str(payloadDict["state"]["desired"]["Power"]).upper()):
            print(("Power: " + str(payloadDict["state"]["desired"]["Power"])))
            IoT_to_Raspberry_Change_Power(str(payloadDict["state"]["desired"]["Power"]))
            
    if ("CoffeeChoice" in payloadDict["state"]["desired"]):
        if(str(payloadDict["state"]["reported"]["CoffeeChoice"]).upper() != str(payloadDict["state"]["desired"]["CoffeeChoice"]).upper()):
            print(("CoffeeChoice: " + str(payloadDict["state"]["desired"]["CoffeeChoice"])))
            IoT_to_Raspberry_Change_CoffeeChoice(str(payloadDict["state"]["desired"]["CoffeeChoice"]))
            
    if ("RegularStrength" in payloadDict["state"]["desired"]):
        if(str(payloadDict["state"]["reported"]["RegularStrength"]).upper() != str(payloadDict["state"]["desired"]["RegularStrength"]).upper()):
            print(("RegularStrength: " + str(payloadDict["state"]["desired"]["RegularStrength"])))
            IoT_to_Raspberry_Change_RegularStrength(str(payloadDict["state"]["desired"]["RegularStrength"]))
            
    if ("NumberOfCups" in payloadDict["state"]["desired"]):
        if(str(payloadDict["state"]["reported"]["NumberOfCups"]).upper() != str(payloadDict["state"]["desired"]["NumberOfCups"]).upper()):
            print(("NumberOfCups: " + str(payloadDict["state"]["desired"]["NumberOfCups"])))
            IoT_to_Raspberry_Change_NumberOfCups(str(payloadDict["state"]["desired"]["NumberOfCups"]))
            
    if ("Start" in payloadDict["state"]["desired"]):
        if(str(payloadDict["state"]["reported"]["Start"]).upper() != str(payloadDict["state"]["desired"]["Start"]).upper()):
            print(("Start: " + str(payloadDict["state"]["desired"]["Start"])))
            IoT_to_Raspberry_Change_Start(str(payloadDict["state"]["desired"]["Start"]))




# Shadow callback for updating the AWS IoT
def IoTShadowCallback_Update(payload, responseStatus, token):
    if responseStatus == "timeout":
        print(("++UPDATE++ request " + token + " timed out!"))
    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
        print(("++UPDATE++ request with token: " + token + " accepted!"))
        if ("desired" in payloadDict["state"]):
            print(("Desired: " + str(payloadDict["state"]["desired"])))
        if ("reported" in payloadDict["state"]):
            print(("Reported: " + str(payloadDict["state"]["reported"])))
    if responseStatus == "rejected":
        print(("++UPDATE++ request " + token + " rejected!"))






# Init AWSIoTMQTTShadowClient
myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(shadowClient)
myAWSIoTMQTTShadowClient.configureEndpoint(host, 8883)
myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTShadowClient configuration
myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect to AWS IoT
myAWSIoTMQTTShadowClient.connect()

# Create a deviceShadow with persistent subscription
myDeviceShadow = myAWSIoTMQTTShadowClient.createShadowHandlerWithName("CoffeeMachine", True)





 

#Now start setting up all GPIO required things like the PINs, and the interrupts
GPIO.setmode(GPIO.BCM)


# Coffee Choice LEDs at the lid
CoffeeChoice_LED_Latte = 7
GPIO.setup(CoffeeChoice_LED_Latte, GPIO.IN, pull_up_down=GPIO.PUD_UP)

CoffeeChoice_LED_Macchiato = 1
GPIO.setup(CoffeeChoice_LED_Macchiato, GPIO.IN, pull_up_down=GPIO.PUD_UP)

CoffeeChoice_LED_Cappuccino = 12
GPIO.setup(CoffeeChoice_LED_Cappuccino, GPIO.IN, pull_up_down=GPIO.PUD_UP)

CoffeeChoice_LED_Regular = 16
GPIO.setup(CoffeeChoice_LED_Regular, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# At start find to which Coffee Choice the machine is set, also of one of these LEDs is ON, the machine is ON
def CoffeeChoice_Selected_LED():
    global Power_StatusSelected, CoffeeChoice_Selected
    if (GPIO.input(CoffeeChoice_LED_Latte) == 0):
        CoffeeChoice_Selected = CoffeeChoice.index("LATTE")
        Power_StatusSelected = Power_Status.index("ON")
    elif (GPIO.input(CoffeeChoice_LED_Macchiato) == 0):
        CoffeeChoice_Selected = CoffeeChoice.index("MACCHIATO")
        Power_StatusSelected = Power_Status.index("ON")
    elif (GPIO.input(CoffeeChoice_LED_Cappuccino) == 0):
        CoffeeChoice_Selected = CoffeeChoice.index("CAPPUCCINO")
        Power_StatusSelected = Power_Status.index("ON")
    elif (GPIO.input(CoffeeChoice_LED_Regular) == 0):
        CoffeeChoice_Selected = CoffeeChoice.index("REGULAR")
        Power_StatusSelected = Power_Status.index("ON")
    else:
        CoffeeChoice_Selected = CoffeeChoice.index("")
        Power_StatusSelected = Power_Status.index("OFF")
CoffeeChoice_Selected_LED()

# Coffee Choice buttons at the lid
CoffeeChoice_BUT_Up = 20
GPIO.setup(CoffeeChoice_BUT_Up, GPIO.OUT)
GPIO.output(CoffeeChoice_BUT_Up, False)

CoffeeChoice_BUT_Down = 21
GPIO.setup(CoffeeChoice_BUT_Down, GPIO.OUT)
GPIO.output(CoffeeChoice_BUT_Down, False)



# Regular Strength LEDs at the lid
RegularStrength_LED_Dark = 18
GPIO.setup(RegularStrength_LED_Dark, GPIO.IN, pull_up_down=GPIO.PUD_UP)

RegularStrength_LED_Medium = 23
GPIO.setup(RegularStrength_LED_Medium, GPIO.IN, pull_up_down=GPIO.PUD_UP)

RegularStrength_LED_Mild = 24
GPIO.setup(RegularStrength_LED_Mild, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# At start find to which Regular Strength the machine is set
def RegularStrength_Selected_LED():
    global RegularStrength_Selected
    if (GPIO.input(RegularStrength_LED_Dark) == 0):
        RegularStrength_Selected = RegularStrength.index("DARK")
    elif (GPIO.input(RegularStrength_LED_Medium) == 0):
        RegularStrength_Selected = RegularStrength.index("MEDIUM")
    elif (GPIO.input(RegularStrength_LED_Mild) == 0):
        RegularStrength_Selected = RegularStrength.index("MILD")
    else:
        RegularStrength_Selected = RegularStrength.index("")
RegularStrength_Selected_LED()

# Regular Strength buttons at the lid
RegularStrength_BUT_Up = 25
GPIO.setup(RegularStrength_BUT_Up, GPIO.OUT)
GPIO.output(RegularStrength_BUT_Up, False)

RegularStrength_BUT_Down = 8
GPIO.setup(RegularStrength_BUT_Down, GPIO.OUT)
GPIO.output(RegularStrength_BUT_Down, False)






# LED in base for ONE cup
Base_LED_One = 5

def LedOne_Interrupt(channel):
    global Base_LED_One_StatusSelected, Base_LED_Power_StatusSelected, Base_LED_Power_StatusSelected_last
    Base_LED_One_StatusSelected = GPIO.input(Base_LED_One)
    if (Base_LED_One_Status[Base_LED_One_StatusSelected] == "READY"):
        Base_LED_Power_StatusSelected = Base_LED_Power_Status.index("READY")
        Base_LED_Power_StatusSelected_last = Base_LED_Power_Status.index("READY")

    JSONPayload = '{ "state" : {'+\
                        '"reported": {'+\
                            '"LedOne":"' + Base_LED_One_Status[Base_LED_One_StatusSelected] + '", '+\
                            '"LedPower":"' + Base_LED_Power_Status[Base_LED_Power_StatusSelected] + '" '+\
                        '} '+\
                    '} '+\
                '}'
    myDeviceShadow.shadowUpdate(JSONPayload, IoTShadowCallback_Update, 5)

GPIO.setup(Base_LED_One, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(Base_LED_One, GPIO.BOTH, callback=LedOne_Interrupt, bouncetime=10)
Base_LED_One_StatusSelected = GPIO.input(Base_LED_One)

# Button in the base for ONE cup
Base_BUT_One = 27
GPIO.setup(Base_BUT_One, GPIO.OUT)
GPIO.output(Base_BUT_One, False)



# LED in base for TWO cups
Base_LED_Two = 9

def LedTwo_Interrupt(channel):
    global Base_LED_Two_StatusSelected, Base_LED_Power_StatusSelected, Base_LED_Power_StatusSelected_last
    Base_LED_Two_StatusSelected = GPIO.input(Base_LED_Two)
    if (Base_LED_Two_Status[Base_LED_Two_StatusSelected] == "READY"):
        Base_LED_Power_StatusSelected = Base_LED_Power_Status.index("READY")
        Base_LED_Power_StatusSelected_last = Base_LED_Power_Status.index("READY")
    JSONPayload = '{ "state" : {'+\
                        '"reported": {'+\
                            '"LedTwo":"' + Base_LED_Two_Status[Base_LED_Two_StatusSelected] + '", '+\
                            '"LedPower":"' + Base_LED_Power_Status[Base_LED_Power_StatusSelected] + '" '+\
                        '} '+\
                    '} '+\
                '}'
    myDeviceShadow.shadowUpdate(JSONPayload, IoTShadowCallback_Update, 5)

GPIO.setup(Base_LED_Two, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(Base_LED_Two, GPIO.BOTH, callback=LedTwo_Interrupt, bouncetime=10)
Base_LED_Two_StatusSelected = GPIO.input(Base_LED_Two)

# Button in the base for TWO cups
Base_BUT_Two = 11
GPIO.setup(Base_BUT_Two, GPIO.OUT)
GPIO.output(Base_BUT_Two, False)






# LED in base for POWER and STATUS
Base_LED_Power_flash_last = time.time()
Base_LED_Power_flash_sec = 0

Base_LED_Power_Pin = 22

def LedPower_Interrupt(channel):
    global Power_StatusSelected, Base_LED_Power_flash_last, Base_LED_Power_flash_sec, Base_LED_Power_StatusSelected_last, Base_LED_Power_StatusSelected
    if (GPIO.input(Base_LED_Power_Pin) == 0):
        Power_StatusSelected = Power_Status.index("ON")
        Base_LED_Power_flash_sec = time.time() - Base_LED_Power_flash_last
        if (Base_LED_Power_flash_sec > 0 and Base_LED_Power_flash_sec < 0.5):
            Base_LED_Power_StatusSelected = Base_LED_Power_Status.index("ERROR")
        elif (Base_LED_Power_flash_sec > 0.5 and Base_LED_Power_flash_sec < 2):
            Base_LED_Power_StatusSelected = Base_LED_Power_Status.index("BUSY")
        elif (Base_LED_Power_flash_sec > 2):
            Base_LED_Power_StatusSelected = Base_LED_Power_Status.index("READY")
            
        if (Base_LED_Power_StatusSelected != Base_LED_Power_StatusSelected_last):
            Base_LED_Power_StatusSelected_last = Base_LED_Power_StatusSelected
            JSONPayload = '{ "state" : {'+\
                                '"reported": {'+\
                                    '"LedPower":"' + Base_LED_Power_Status[Base_LED_Power_StatusSelected] + '", '+\
                                    '"Power":"' + Power_Status[Power_StatusSelected] + '" '+\
                                '} '+\
                            '} '+\
                        '}'
            myDeviceShadow.shadowUpdate(JSONPayload, IoTShadowCallback_Update, 5)

    else:
        Base_LED_Power_flash_last = time.time()

GPIO.setup(Base_LED_Power_Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(Base_LED_Power_Pin, GPIO.BOTH, callback=LedPower_Interrupt, bouncetime=10)


# Button in the base for POWER
Base_BUT_Power = 10
GPIO.setup(Base_BUT_Power, GPIO.OUT)
GPIO.output(Base_BUT_Power, False)



# Sensor for LID open/close
Lid_Pin = 0

def Callback_Lid(channel):
    global Lid_StatusSelected
    Lid_StatusSelected = GPIO.input(Lid_Pin)
    JSONPayload = '{ "state" : {'+\
                        '"reported": {'+\
                            '"Lid":"' + Lid_Status[Lid_StatusSelected] + '" '+\
                        '} '+\
                    '} '+\
                '}'
    myDeviceShadow.shadowUpdate(JSONPayload, IoTShadowCallback_Update, 5)

GPIO.setup(Lid_Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(Lid_Pin, GPIO.BOTH, callback=Callback_Lid, bouncetime=10)
Lid_StatusSelected = GPIO.input(Lid_Pin)




time.sleep(3)
# All pins and defaults initialized, upload all system status parameters
JSONPayload = '{ "state" : {'+\
                    '"reported": {'+\
                        '"Power": "' + Power_Status[Power_StatusSelected] + '", '+\
                        '"Start": "NO", '+\
                        '"CoffeeChoice": "' + CoffeeChoice[CoffeeChoice_Selected] + '", '+\
                        '"RegularStrength": "' + RegularStrength[RegularStrength_Selected] + '", '+\
                        '"NumberOfCups": "' + NumberOfCups[NumberOfCups_Selected] + '", '+\
                        '"LedOne": "' + Base_LED_One_Status[Base_LED_One_StatusSelected] + '", '+\
                        '"LedTwo": "' + Base_LED_Two_Status[Base_LED_Two_StatusSelected] + '", '+\
                        '"Lid": "' + Lid_Status[Lid_StatusSelected] + '"'+\
                    '}, '+\
                    '"desired": {'+\
                        '"Power": "' + Power_Status[Power_StatusSelected] + '", '+\
                        '"Start": "NO" '+\
                    '} '+\
                '} '+\
            '}'
myDeviceShadow.shadowUpdate(JSONPayload, IoTShadowCallback_Update, 5)





# We will loop through the process to see what the Power LED does, as this tells us more about the status.
# Most of it is done in the Interrupt, as that kicks in when the LED starts shining,
# but sometimes the LED stays ON or OFF. This loop does catch that.
def loop():
    global Base_LED_Power_flash_sec, Base_LED_Power_StatusSelected, Base_LED_Power_StatusSelected_last, Base_LED_Power_flash_last, Power_StatusSelected, Power_StatusSelected, CoffeeChoice_Selected, RegularStrength_Selected

    Base_LED_Power_flash_sec = time.time() - Base_LED_Power_flash_last
    if (Base_LED_Power_flash_sec > 5):
        if (GPIO.input(Base_LED_Power_Pin) == 0):
            Base_LED_Power_StatusSelected = Base_LED_Power_Status.index("READY")
            Power_StatusSelected = Power_Status.index("ON")
        else:
            Base_LED_Power_StatusSelected = Base_LED_Power_Status.index("OFF")
            Power_StatusSelected = Power_Status.index("OFF")
            
        if (Base_LED_Power_StatusSelected != Base_LED_Power_StatusSelected_last):
            print(("Base_LED_Power_flash_sec: " + str(Base_LED_Power_flash_sec) + " Base_LED_Power_Status: " + Base_LED_Power_Status[Base_LED_Power_StatusSelected]))
            Base_LED_Power_StatusSelected_last = Base_LED_Power_StatusSelected
            Base_LED_Power_flash_last = time.time()

            if (Power_StatusSelected == Power_Status.index("ON")):
                CoffeeChoice_Selected_LED() #as the machine is powering ON now, one of the LEDs will turn on, find the status
                RegularStrength_Selected_LED() #as the machine is powering ON now, one of the LEDs will turn on, find the status
                JSONPayload = '{ "state" : {'+\
                                    '"reported": {'+\
                                        '"LedPower":"' + Base_LED_Power_Status[Base_LED_Power_StatusSelected] + '", '+\
                                        '"Power": "' + Power_Status[Power_StatusSelected] + '", '+\
                                        '"Start": "NO", '+\
                                        '"CoffeeChoice": "' + CoffeeChoice[CoffeeChoice_Selected] + '", '+\
                                        '"RegularStrength": "' + RegularStrength[RegularStrength_Selected] + '" '+\
                                    '} '+\
                                '} '+\
                            '}'
                myDeviceShadow.shadowUpdate(JSONPayload, IoTShadowCallback_Update, 5) #Send the new status as REPORTED values
            elif (Power_StatusSelected == Power_Status.index("OFF")):
                CoffeeChoice_Selected = CoffeeChoice.index("") #LEDs will now be off
                RegularStrength_Selected = RegularStrength.index("") #LEDs will now be off
                JSONPayload = '{ "state" : {'+\
                                    '"reported": {'+\
                                        '"LedPower":"' + Base_LED_Power_Status[Base_LED_Power_StatusSelected] + '", '+\
                                        '"Power": "' + Power_Status[Power_StatusSelected] + '", '+\
                                        '"Start": "NO", '+\
                                        '"CoffeeChoice": "' + CoffeeChoice[CoffeeChoice_Selected] + '", '+\
                                        '"RegularStrength": "' + RegularStrength[RegularStrength_Selected] + '" '+\
                                    '}, '+\
                                    '"desired": {'+\
                                        '"Power": "' + Power_Status[Power_StatusSelected] + '", '+\
                                        '"Start": "NO" '+\
                                    '} '+\
                                '} '+\
                            '}'
                myDeviceShadow.shadowUpdate(JSONPayload, IoTShadowCallback_Update, 5) #Send the new status as REPORTED values

    time.sleep(3)








# Listen on deltas from the IoT Shadow
myDeviceShadow.shadowGet(IoTShadowCallback_Get, 5)
myDeviceShadow.shadowRegisterDeltaCallback(IoTShadowCallback_Delta)

if __name__ == '__main__':
    try:
        print('CoffeeMachine started, Press Ctrl-C to quit.')
        while True:
            #pass
            loop()
    finally:
        GPIO.cleanup()
        myAWSIoTMQTTShadowClient.shadowUnregisterDeltaCallback()
        myAWSIoTMQTTShadowClient.disconnect()
        print('CoffeeMachine stopped.')

