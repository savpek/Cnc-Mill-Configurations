#!/usr/bin/python
import sys
import hal
import serial
import time
import easygui

# S620 servo drive driver and manual tool changer.

###
# Define settings here.
S620_SERIAL_DEVICE = "/dev/ttyS0"
SPDINLE_RPM_LIMIT = 4000
# Spindle may have gearing, tells actual spindle speed
# compared to motor rotatation speed.
RPM_CONVERSION_RATE = 0.9

def error_msg(msg):
	easygui.msgbox(msg=msg, title='VIRHE!', ok_button='OK')

class Spindle:
	last_echo = ""
	def __init__(self, port_device):
		try:
			# Try connect to serialport.
			self.serialHook = serial.Serial(port_device, 9600, timeout=0.2)
		except:
		# show error to user! Theres no serial port available!
			self.__error("VIRHE 1")
		
	# Try send cmd to device. This checks that device truly echoes
	# correct string.
	def __try_send(self, cmd):
		# Flush input, this because we want
		# to check command sended.
		self.serialHook.flushInput()
		# Send new command!
		self.serialHook.write(cmd+"\r\n")
			
		# Spindle driver echoes command, lets check that
		# command was written correctly.
		time.sleep(0.1)
		self.last_echo = self.serialHook.read( self.serialHook.inWaiting() )
		
		#if command send went OK:	
		if cmd+"\r\n" in self.last_echo:
			return True
		
		#Else returns false:
		return False
		
	# This function looks up through received serial string,
	# if it find "ERR" string there is error in
	def is_error(self):
		if "ERR" in self.last_echo:
			print "ERROR: "+self.last_echo
			return True
		else:
			return False
	
	# Enables drive (software enable)
	def enable(self):
		self.send_cmd("EN")
		
	def disable(self):
		self.send_cmd("DIS")
	
	def is_hw_enabled(self):
		self.send_cmd("STATUS")
		
		# In string position 12 there should be 0 or 2,
		# In 0 case, both SW and HW are enabled.
		# In 2 case, only HW is enabled.
		if self.last_echo[12] in "02":
			return True
		else:
			return False
	
	# Send command
	def send_cmd(self, cmd):
		attempts = 0
		for attempts in range(4):
			attempts = attempts +1
			if self.__try_send(cmd):
				return True
		
		# If no successful command operation,
		# Print error message to AXIS GUI.
		error_msg("""SPINDLE ERROR: Incorrect responce from drive.
Got:
"""+self.last_echo+"""
Exepted:
"""+cmd)
		
		return False
		
	def set_speed(self, rpm, rpm_old):
		# If drive HW is currently disabled (safe circuit off)
		# print message!
		if self.is_hw_enabled() != True and rpm != 0:
			easygui.msgbox(msg="""Karamoottorilla ei lupaa olla paalla! Paina turvakytkinta karan kyljesta.""", title=' HUOM!', ok_button='OK')
		
		# If speed is > 0, software enable drive.
		if rpm != 0:
			self.enable()
			time.sleep(0.2)		
		self.send_cmd("J "+'{0:.0f}'.format(rpm*RPM_CONVERSION_RATE))
		
		# If speed is 0, drive doesn't need to be enabled.
		if rpm == 0:
			time.sleep(rpm_old/900+0.2)
			self.disable()
	
	def set_flood_on(self):
		__try_send("O2 1")
		pass
	def set_flood_off(self):
		pass
	
	# This disables drive so that enabling it requires
	# physical button check before drive can be enabled again.
	# Used for example: Manual toolchange.
	def hard_disable(self):
		# This disables digital output 1 from drive.
		# This disables circuit that keep physical enable
		# driven high in drive.
		self.send_cmd("O1 0")
		time.sleep(1)
		# Now set digital out to high again, now you can
		# enable drive from button again.
		self.send_cmd("O1 1")

spindle = Spindle(S620_SERIAL_DEVICE)

# HAL component.
halc = hal.component("spindle-driver")

# Component pins.
halc.newpin("set-speed-rpm", hal.HAL_FLOAT, hal.HAL_IN)
halc.newpin("new-tool-change", hal.HAL_BIT, hal.HAL_IN)
halc.newpin("new-tool-number", hal.HAL_S32, hal.HAL_IN)
halc.newpin("flood", hal.HAL_BIT, hal.HAL_IN)
halc.newpin("tool-changed", hal.HAL_BIT, hal.HAL_OUT)
halc.newpin("drive-ok", hal.HAL_BIT, hal.HAL_OUT)

# Must be called or HAL environment got stuck.
halc.ready()

halc['tool-changed'] = False

current_speed_set = 0

# Coldstart spindle:
spindle.send_cmd("COLDSTART")
# Wait coldstart done:
time.sleep(5)

# Set initial values.
spindle.set_speed(0, 0)
spindle.hard_disable()


while True:
	# IF speed have changed, set new speed.		
	if current_speed_set != halc['set-speed-rpm']:
		spindle.set_speed(halc['set-speed-rpm'], current_speed_set)
		current_speed_set = halc['set-speed-rpm']
	
	if halc['new-tool-change'] == True:
		spindle.set_speed(0,current_speed_set)
		spindle.hard_disable()	
		
		# Stay here until drive has permision to
		# run again.			
		while spindle.is_hw_enabled() != True:
			easygui.msgbox(msg="""Vaihta tyokalu ja paina karan kyljessa olevaa nappia! """, title=' HUOM!', ok_button='OK')
		
		# Keep tool change mark up briefly (axis should notice this).
		halc['tool-changed'] = True
		time.sleep(0.5)
		halc['tool-changed'] = False
		
		
	time.sleep(0.5)

spindle.serialHook.close()
