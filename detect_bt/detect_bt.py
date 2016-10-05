import tracer

import bluetooth

def detect_bluetooth():
    search_time = 30
    addr = None
    
    print("Welcome to the Bluetooth Detection Demo! \nMake sure your desired Bluetooth-capable device is turned on and discoverable.")

    if addr == None:
        try:
            input("When you are ready to begin, press the Enter key to continue...")
        except SyntaxError:
            pass
            
        print("Searching for devices...")

        nearby_devices = bluetooth.discover_devices(duration=search_time, flush_cache=True, lookup_names=True)

        if len(nearby_devices) > 0:
            print("Found %d devices!" % len(nearby_devices))
        else:
            print("No devices found! Please check your Bluetooth device and restart the demo!")
            exit(0)

        i = 0 # Just an incrementer for labeling the list entries
        # Print out a list of all the discovered Bluetooth Devices
        for addr, name in nearby_devices:
            print("%s. %s - %s" % (i, addr, name))
            i =+ 1

        device_num = input("Please specify the number of the device you want to track: ")

        # extract out the useful info on the desired device for use later
        addr, name = nearby_devices[int(device_num)][0], nearby_devices[int(device_num)][1]

        print("The script will now scan for the device %s." % (addr))

        # Try to gather information from the desired device.
        # We're using two different metrics (readable name and data services)
        # to reduce false negatives.
        state = bluetooth.lookup_name(addr, timeout=20)
        services = bluetooth.find_service(address=addr)
        
        if state == None and services == []:
            print("No device detected in range...")
        else:
            print("Device detected!")

tracer.start_tracer(detect_bluetooth)
