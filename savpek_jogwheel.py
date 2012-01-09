#!/usr/bin/python
import sys
import hal
import serial, time
import glob

# Luodaan HAL komponentti.
halc = hal.component("savpek-jogwheel")

# Joysticcien pinnit.
halc.newpin("jog.x.plus", hal.HAL_BIT, hal.HAL_OUT)
halc.newpin("jog.x.minus", hal.HAL_BIT, hal.HAL_OUT)
halc.newpin("jog.y.plus", hal.HAL_BIT, hal.HAL_OUT)
halc.newpin("jog.y.minus", hal.HAL_BIT, hal.HAL_OUT)
halc.newpin("jog.z.plus", hal.HAL_BIT, hal.HAL_OUT)
halc.newpin("jog.z.minus", hal.HAL_BIT, hal.HAL_OUT)
halc.newpin("jog.x.home", hal.HAL_BIT, hal.HAL_OUT)
halc.newpin("jog.y.home", hal.HAL_BIT, hal.HAL_OUT)
halc.newpin("jog.z.home", hal.HAL_BIT, hal.HAL_OUT)

# Nopeus potikan sisaantulo.
halc.newpin("jog.speed", hal.HAL_FLOAT, hal.HAL_OUT)

# ESTOP pinnit
halc.newpin("jog.estop.activate", hal.HAL_BIT, hal.HAL_OUT)
halc.newpin("jog.estop.reset", hal.HAL_BIT, hal.HAL_OUT)

# MACHINE ON PIN
halc.newpin("jog.machine-on", hal.HAL_BIT, hal.HAL_OUT)

# Tama pitaa kutsua, tai EMC2 jaa loputtomiin jumiin tahan.
halc.ready()

serialPortList = glob.glob("/dev/ttyUSB*");
serialHook = serial.Serial(serialPortList[0], 38400)
serialHook.write('U')

while 1:
	serialStr = serialHook.readline()

	if "X+ ON" in serialStr:	#X+ Suunta.
		print "X+ ON"
		halc['jog.x.plus'] = 1
	elif "X+ OFF" in serialStr:
		print "X+ OFF"
		halc['jog.x.plus'] = 0
		
	if "X- ON" in serialStr:	#X- Suunta.
		print "X- ON"
		halc['jog.x.minus'] = 1
	elif "X- OFF" in serialStr:
		print "X- OFF"
		halc['jog.x.minus'] = 0
		
	if "Y+ ON" in serialStr:	#Y+ Suunta.
		halc['jog.y.plus'] = 1
	elif "Y+ OFF" in serialStr:
		halc['jog.y.plus'] = 0
		
	if "Y- ON" in serialStr:	#Y- Suunta.
		halc['jog.y.minus'] = 1
	elif "Y- OFF" in serialStr:
		halc['jog.y.minus'] = 0
		
	if "Z- ON" in serialStr:	#Z- Suunta.
		halc['jog.z.minus'] = 1
	elif "Z- OFF" in serialStr:
		halc['jog.z.minus'] = 0
		
	if "Z+ ON" in serialStr:	#Z+ Suunta.
		halc['jog.z.plus'] = 1
	elif "Z+ OFF" in serialStr:
		halc['jog.z.plus'] = 0
	
	if "ZERO_POINT_X" in serialStr:
		halc['jog.x.home'] = 1
	else:
		halc['jog.x.home'] = 0
		
	if "ZERO_POINT_Y" in serialStr:
		halc['jog.y.home'] = 1
	else:
		halc['jog.y.home'] = 0
	
	if "ZERO_POINT_Z" in serialStr:
		halc['jog.z.home'] = 1
	else:
		halc['jog.z.home'] = 0
		
	if "NEWSPEED" in serialStr:	#Haetaan nopeus.
		newSpeedValue = float(serialStr.rpartition(' ')[2])
		
		#Asetetaan nopeuden skaalaus potikalta sopivaksi.
		halc['jog.speed'] = float(newSpeedValue/256*3000+5)
	
	# Laitetaan hataseis paalle.
	if "EMERGENCY_STOP_ON" in serialStr:
		halc['jog.estop.reset'] = 0
		halc['jog.estop.activate'] = 1
		#halc['jog.machine-on'] = 0
	
	# Ja hataseis pois paalta.
	if "EMERGENCY_STOP_OFF" in serialStr:
		# Vaihto HALUIssa tapahtuu aina kun signaali vaihtuu
		# ylos. Nain ollen signaalit pitaa aina nollata.
		halc['jog.estop.activate'] = 0
		halc['jog.estop.reset'] = 1
		#time.sleep(1)
		#halc['jog.machine-on'] = 1
