#!/usr/bin/python
#OBD Script

import os, time, datetime
import sys
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import time


__addon__		= xbmcaddon.Addon()
__addonid__	  = __addon__.getAddonInfo('id')
__addonversion__ = __addon__.getAddonInfo('version')
__language__	 = __addon__.getLocalizedString

AdditionalParams = []
Window = 10000
debug = 0
lastTime = time.time()
tripKm = 0
tripL = 0
ppL = 139

def log(txt):
    if isinstance(txt, str):
        txt = txt.decode("utf-8")
    message = u'%s: %s' % (__addonid__, txt)
    xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)

def passHomeDataToSkin(data, debug = True):
	wnd = xbmcgui.Window(Window)
	if data != None:
		for (key,value) in data.iteritems():
			wnd.setProperty('%s' % (str(key)), unicode(value))
			if debug:
				log('%s' % (str(key)) + unicode(value))
			   
def passDataToSkin(name, data, prefix="",debug = False):
	wnd = xbmcgui.Window(Window)
	if data != None:
		log( "%s%s.Count = %s" % (prefix, name, str(len(data)) ) )
		for (count, result) in enumerate(data):
			if debug:
				log( "%s%s.%i = %s" % (prefix, name, count + 1, str(result) ) )
			for (key,value) in result.iteritems():
				wnd.setProperty('%s%s.%i.%s' % (prefix, name, count + 1, str(key)), unicode(value))
				if debug:
					log('%s%s.%i.%s --> ' % (prefix, name, count + 1, str(key)) + unicode(value))
		wnd.setProperty('%s%s.Count' % (prefix, name), str(len(data)))
	else:
		wnd.setProperty('%s%s.Count' % (prefix, name), '0')
		log( "%s%s.Count = None" % (prefix, name ) )
		
class Main:
	def __init__( self ):
		log("version %s started" % __addonversion__ )
		xbmc.executebuiltin('SetProperty(obd_running,True,home)')
		self._init_vars()
		self._parse_argv()		
		# run in backend if parameter was set

		if self.backend and xbmc.getCondVisibility("IsEmpty(Window(home).Property(obd_backend_running))"):
			log("running OBD backend")
			xbmc.executebuiltin('SetProperty(obd_backend_running,True,home)')
			self.run_backend()
		elif self.backend:
			log("Backend already running")
		#No arguments: Do setup
		#elif not len(sys.argv) >1:
		#	self._selection_dialog()
		xbmc.executebuiltin('ClearProperty(obd_running,home)')
		
	
	
	def run_backend(self):
		import obd		
		self.obdcomms = obd.obd()	
		self._stop = False
		
		while (not self._stop) and (not xbmc.abortRequested):

			if (not self.obdcomms) or (not self.obdcomms.port):
				self.window.setProperty("OBD-Conn","No BT Comms")
				#log("OBD Serial not connected. Waiting 3s...")
				self.obdcomms = None
				xbmc.sleep(2000)
				self.obdcomms = obd.obd()	
			elif xbmc.getCondVisibility("Window.IsActive(home)"):
				#passDataToSkin('Stuff', ['bob', 'fred'], self.prop_prefix)
				
				pidDict = self._SetupValues('home')
				for (pid, dict) in pidDict.iteritems():
					try:
						if self._process_pids(pid, dict) == 0:	#No data, ign off
							if self.window.getProperty("OBD-Speed") != 'Off':
								self.window.setProperty("OBD-Conn","Ignition Off")
								self.window.setProperty("OBD-Speed",'Off')
								self.obdcomms = None
								#xbmc.executebuiltin('PlayerControl(Stop)')
							break
						else:
							self.window.setProperty("OBD-Conn","OK")
					except:
						log('PID process '+pid+' exception')
						xbmc.executebuiltin('Notification(Error,PID process '+pid+' exception,3000)')
				if self.window.getProperty("OBD-Speed") == 'Off':
					#Ignition on but engine off || Completely off
					self.window.setProperty("OBD-SpeedMPH",'0')
					#self.window.setProperty("OBD-Conn","Speed Empty")
					xbmc.sleep(3000)
				else:
				#Special Cases:
					try:
						boostPerc = int(int(self.window.getProperty("OBD-BoostPress"))-int(self.window.getProperty("OBD-BoostPress"))/20)
					#self.window.setProperty("OBD-BoostPercent",str(boostPerc))
						self.window.getControl(669).setPercent(boostPerc)
						speedMPH = round(float(self.window.getProperty("OBD-Speed"))*0.621371, 1)
						self.window.setProperty("OBD-SpeedMPH",str(speedMPH))
						setMPH = round(float(self.window.getProperty("OBD-CCSet"))*0.621371, 1)
						if setMPH>0:
							self.window.setProperty("OBD-SetMPH",str(setMPH))
						else:
							self.window.clearProperty("OBD-SetMPH")
						rpmPerc = int(int(self.window.getProperty("OBD-RPM"))/50)
						self.window.getControl(670).setPercent(rpmPerc)
						throtPerc = int(float(self.window.getProperty("OBD-Throttle")))
						self.window.getControl(671).setPercent(throtPerc)
						self.calcmpg()
					except:
						xbmc.executebuiltin('Notification(Error,Calculating imperial values from OBD data failed,3000)')
						log("Special cases OBD failed")
				#self.window.setProperty("OBD-RPMPercent",str(rpmPerc))
				#if OBDvolt: self.window.setProperty("OBD-V",OBDvolt)
			else: #on some other screen
				pidDict = self._SetupValues('fuelonly')
				for (pid, dict) in pidDict.iteritems():
					try:
						if self._process_pids(pid, dict) == 0:	#No data, ign off
							if self.window.getProperty("OBD-Speed") != 'Off':
								self.window.setProperty("OBD-Conn","Ignition Off")
								self.window.setProperty("OBD-Speed",'Off')
								self.obdcomms = None
							break
						else:
							self.window.setProperty("OBD-Conn","OK")
					except:
						log('PID process '+pid+' failed')
				if self.window.getProperty("OBD-Speed") == 'Off':
					#Ignition on but engine off || Completely off
					self.window.setProperty("OBD-SpeedMPH",'0')
					#self.window.setProperty("OBD-Conn","Speed Empty")
					xbmc.sleep(3000)
				else:
					self.calcmpg()
			if xbmc.getCondVisibility("IsEmpty(Window(home).Property(obd_backend_running))"):
				self._clear_properties()
				self._stop = True
			xbmc.sleep(350)	#Normal time between samples

			
	def _init_vars(self):
		self.window = xbmcgui.Window(10000) # Home Window default
		self.cleared = False
		self.prop_prefix = ""
		self.silent = True
		
	def _parse_argv(self):
		try:
			params = dict( arg.split("=") for arg in sys.argv[1].split("&"))
		except:
			params = {}
		self.backend = params.get("backend", False)
		self.exportsettings = params.get("exportsettings", False)
		self.importsettings = params.get("importsettings", False)
		for arg in sys.argv:
			log("ARGS: "+arg)
			if arg == 'script.GPIO':
				continue
			param = arg.lower()
			if param.startswith('window='):
				Window = int(arg[7:])
			else:
				AdditionalParams.append(param)
	
	def _clear_properties( self ):
		self.cleared = False
		#self.window.clearProperty('Stuff')
		self.cleared = True


	def _SetupValues(self, subsect):
			# byte   desc   multiplier  then+  unit   bytelen  int/str
		allData = {	8: ('WaterTemp', 0.1, -273.1, 'deg C', 2, 'i'),
			   14: ('Throttle', 0.01, 0, '%', 2, 'i'),
			   16: ('Voltage', 0.02, 0, 'v', 2, 'i'),
			   10: ('MAF', 1, 0, 'mg/stroke', 2, 'i'),
			   26: ('RPM', 1, 0, 'rpm', 2, 'i'),
			   68: ('AirTemp', 0.1, -273.1, 'deg C', 2, 'i'),
			   12: ('FuelTemp', 0.1, -273.1, 'deg C', 2, 'i'),
			   42: ('DesIdle', 1, 0, 'rpm', 2, 'i'),
			   28: ('EGRCmd', 0.1, 0, 'mg/stroke', 2, 'i'),
			   22: ('BoostPress', 1, 0, 'mBar', 2, 'i'),
			   32: ('BoostCmd', 1, 0, 'mBar', 2, 'i'),
			   70: ('AirPressure', 1, 0, 'mBar', 2, 'i'),
			   34: ('DesIdle', 1, 0, 'RPM', 2, 'i'),
			   48: ('StDel', 0.01, 0, 'degCA', 2, 'i'),
			   56: ('PulRatio', 0.01, 0, '%', 2, 'i'),
			   46: ('InjQua', 0.01, 0, 'mg/stroke', 2, 'i'),
			   44: ('DesInj', 0.01, 0, 'mg/stroke', 2, 'i'),
			   64: ('PressValve', 0.01, 0, '%', 2, 'i'),
			   50: ('InjSt', 0.01, 0, 'degCA', 2, 'i'),
			   38: ('Speed', 0.01, 0, 'km/h', 2, 'i'),
			   40: ('CCSet', 0.01, 0, 'km/h', 2, 'i')
		}
		
		fuelData = {	
			   26: ('RPM', 1, 0, 'rpm', 2, 'i'),
			   12: ('FuelTemp', 0.1, -273.1, 'deg C', 2, 'i'),
			   44: ('InjQua', 0.01, 0, 'mg/stroke', 2, 'i'),
			   38: ('Speed', 0.01, 0, 'km/h', 2, 'i')
		}

		ecuID = {	0: ('VIN', 0, 0, '', 17, 's'),
					17: ('ECUHW', 0, 0, '', 11, 's'),
					28: ('ECUrev', 0, 0, '', 11, 's'),
					40: ('SuppECU', 0, 0, '', 10, 's'),
					50: ('Exha', 0, 0, '', 8, 's'),
					58: ('Engine', 0, 0, '', 9, 's'),
					82: ('Manufact', 0, 0, '', 11, 's')
				}

		if subsect == 'home':
			pidDict = {'2101': allData}
		elif subsect == 'fuelonly':
			pidDict = {'2101': fuelData}
		elif subsect == 'vehdetails':
			pidDict = {'1A80': ecuID}
		else: #return everything!
			pidDict = {'2101': allData, '1A80': ecuID}
		
		return pidDict

	def _process_pids(self, pid, dict):
		global debug
		if debug and pid == '2101':
			#resp = '80 F1 11 4C 61 01 00 00 00 00 00 00 00 00 0B EF 01 B9 0B AB 03 80 02 B9 00 00 0C EE 03 D2 00 00 03 B1 0F 4D 03 E3 04 41 03 46 F5 56 00 00 00 00 03 89 03 0A 05 52 0A 02 01 D6 0B E9 A0 00 07 86 00 00 A1 00 01 31 19 64 02 15 0B B0 03 E5 00 02 76'
			resp = 'C0 F1 11 4C 61 01 02 16 13 AA 16 14 AA 00 0D 45 02 0B 0C EF 15 46 02 AC 00 00 15 73 04 B2 00 00 08 84 14 84 03 E6 06 66 03 84 15 58 05 96 00 00 03 89 09 7C 08 D6 0A 2A 04 60 0C 0C A0 00 00 46 00 00 A8 00 01 30 19 64 02 20 0B CE 03 E6 00 02 83'
		elif debug and pid == '1A80':
			resp = '80 F1 11 5F 5A 80 57 30 4C 30 54 47 46 37 35 32 32 31 36 34 33 34 34 32 34 34 31 37 31 36 39 20 50 44 42 4F 53 20 20 30 31 30 35 30 35 FF 4B 4D 37 4D 33 30 34 30 5F 53 00 06 42 30 31 30 31 35 59 32 30 44 54 48 20 44 33 FF FF FF FF FF FF FF FF FF FF FF FF FF FF 05 48 30 32 38 31 30 31 30 32 36 38 8A'
		else:
			resp = self.obdcomms.get_response(pid)
		#print resp
		if resp and (not 'F1 11 7F' in resp) and (not 'NO DATA' in resp) and (not 'ERROR' in resp):
			try:
				arrResp = resp.split(' ')[6:]
			except:
				log("response fail")
				return 0
			
			pids = []
			i = 0
			while i < len(arrResp):
				if i in dict:
					ilen = dict[i][4]
					if dict[i][5] == 'i':
						hexval = ''.join(byt for byt in arrResp[i:i+ilen])
						calcval = str(int(hexval, 16)*dict[i][1]+int(dict[i][2]))#+' '+dict[i][3]
					else:
						calcval = ''.join(chr(int(byt, 16)) for byt in arrResp[i:i+ilen])
					#print "OBD-"+dict[i][0]+'----'+calcval
					self.window.setProperty("OBD-"+dict[i][0],calcval)
					#if debug: log("OBD-"+dict[i][0]+'='+calcval)
					i+=ilen
				else:
					i+=1	
			return 1
		if resp and ('ERROR' in resp) or ('NO DATA' in resp):
			return 0
					
	#def _check_ign(self):
		#global debug
		#if debug: return true
		#resp = self.obdcomms.get_response('ATFI')
		#if not 'ERROR' in resp: return true
		#return false

	def calcmpg(self):
		global lastTime, tripKm, tripL, ppL
		#gal/mi = RPM/60x Fuel/1000x SPD/3600 x4.55 x 1/(850-.7FT). x 2 ?!
		if int(time.time()-lastTime) > 20: #time has been adjusted
			lastTime = time.time()
			return 0
		injQua = float(self.window.getProperty("OBD-InjQua")) # mg/strk
		speed = float(self.window.getProperty("OBD-Speed")) #km/h
		rpm = float(self.window.getProperty("OBD-RPM"))
		T = float(self.window.getProperty("OBD-FuelTemp"))
		lps = rpm*injQua/(30000*(850-0.7*T))
		tripL += (time.time()-lastTime) * lps
		tripKm += (time.time()-lastTime)*speed/3600
		lastTime = time.time()
		if tripL > 0: 
			AvMPG = tripKm/tripL*2.82481
			self.window.setProperty("OBD-AvMPG",str(round(AvMPG,1)))
			self.window.setProperty("OBD-TripL",str(round(tripL,1)))
			self.window.setProperty("OBD-TripKm",str(round(tripKm,1)))
			self.window.setProperty("OBD-TripMi",str(round(tripKm*0.621371,1)))
			self.window.setProperty("OBD-TripP",str(round(ppL*tripL/100,2)))
		if injQua == 0:
			self.window.setProperty("OBD-MPG", "OO MPG")
		else:
			if speed <= 5:
				#I like L / h
				lph = 3600*lps
				self.window.setProperty('OBD-MPG', str(round(lph,1))+" L/h")
			else:		#mi/h    /   gal/h
				#mpg = speed*0.621371 / (lps*3600/4.55)
				mpg = speed / (lps*1273.3)
				self.window.setProperty("OBD-MPG", str(round(mpg,1))+" MPG")
		
if ( __name__ == "__main__" ):
	Main()
log('finished')
