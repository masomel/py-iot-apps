import wiringpi2 as wiringpi  
import time  
  
pin_base = 65       # lowest available starting number is 65  
i2c_addr = 0x20     # A0, A1, A2 pins all wired to GND  
  
wiringpi.wiringPiSetup()                    # initialise wiringpi  
wiringpi.mcp23017Setup(pin_base,i2c_addr)   # set up the pins and i2c address  
  
wiringpi.pinMode(68, 1)         # sets GPA0 to output
wiringpi.pinMode(66, 1)
wiringpi.pinMode(67, 1)
wiringpi.digitalWrite(68, 0)    # sets GPA0 to 0 (0V, off)
wiringpi.digitalWrite(66, 0)
wiringpi.digitalWrite(67, 0)
  
# Note: MCP23017 has no internal pull-down, so I used pull-up and inverted  
# the button reading logic with a "not"  
while True:  
	wiringpi.digitalWrite(68, 1) # sets port GPA0 to 1 (3V3, on)
	wiringpi.digitalWrite(66, 1)
	time.sleep(3)
	wiringpi.digitalWrite(68, 0)
	wiringpi.digitalWrite(66, 0)
	time.sleep(3)
