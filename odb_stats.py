import obd
import time
import sys
from datetime import datetime

debug = False

class Main:

	def _SetupValues(self, subsect):
			# byte   desc   multiplier  then+  unit   bytelen  int/str
		allData = {	8: ('Tcool', 0.1, -273.1, 'deg C', 2, 'i'),
			   14: ('Throttle', 0.01, 0, '%', 2, 'i'),
			   16: ('Voltage', 0.02, 0, 'v', 2, 'i'),
			   10: ('MAF', 1, 0, 'mg/stroke', 2, 'i'),
			   26: ('RPM', 1, 0, 'rpm', 2, 'i'),
			   68: ('AirTemp', 0.1, -273.1, 'deg C', 2, 'i'),
			   12: ('FuelTemp', 0.1, -273.1, 'deg C', 2, 'i'),
			   42: ('DesIdle', 1, 0, 'deg C', 2, 'i'),
			   28: ('EGRCmd', 0.1, 1, 'mg/stroke', 2, 'i'),
			   22: ('BoostPress', 1, 1, 'mBar', 2, 'i'),
			   32: ('BoostCmd', 1, 1, 'mBar', 2, 'i'),
			   70: ('Air Pressure', 1, 1, 'mBar', 2, 'i'),
			   34: ('DesIdle', 1, 1, 'RPM', 2, 'i'),
			   48: ('StDel', 0.01, 1, 'degCA', 2, 'i'),
			   56: ('PulRatio', 0.01, 1, '%', 2, 'i'),
			   44: ('InjQua', 0.01, 1, 'mg/stroke', 2, 'i'),
			   46: ('DesInj', 0.01, 1, 'mg/stroke', 2, 'i'),
			   64: ('PressValve', 0.01, 1, '%', 2, 'i'),
			   50: ('InjSt', 0.01, 1, 'degCA', 2, 'i'),
			   38: ('Speed', 0.01, 1, 'km/h', 2, 'i')
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
		elif subsect == 'vehdetails':
			pidDict = {'1A80': ecuID}
		else: #return everything!
			pidDict = {'2101': allData, '1A80': ecuID}
		
		return pidDict

	def _process_pids(self, pid, dict):
		if debug and pid == '2101':
			resp = 'C0 F1 11 4C 61 01 02 16 13 AA 16 14 AA 00 0D 45 02 0B 0C EF 15 46 02 AC 00 00 15 73 04 B2 00 00 08 84 14 84 03 E6 06 66 03 84 15 58 05 96 00 00 03 89 09 7C 08 D6 0A 2A 04 60 0C 0C A0 00 00 46 00 00 A8 00 01 30 19 64 02 20 0B CE 03 E6 00 02 83'
		elif debug and pid == '1A80':
			resp = '80 F1 11 5F 5A 80 57 30 4C 30 54 47 46 37 35 32 32 31 36 34 33 34 34 32 34 34 31 37 31 36 39 20 50 44 42 4F 53 20 20 30 31 30 35 30 35 FF 4B 4D 37 4D 33 30 34 30 5F 53 00 06 42 30 31 30 31 35 59 32 30 44 54 48 20 44 33 FF FF FF FF FF FF FF FF FF FF FF FF FF FF 05 48 30 32 38 31 30 31 30 32 36 38 8A'
		else:
			resp = obdcomms.get_response(pid)
		#print resp
		if resp and (not 'F1 11 7F' in resp) and (not 'NO DATA' in resp) and (not 'ERROR' in resp):
			try:
				arrResp = resp.split(' ')[6:]
			except:
				print "response fail"
			
			pids = []
			i = 0
			while i < len(arrResp):
				if i in dict:
					ilen = dict[i][4]
					if dict[i][5] == 'i':
						hexval = ''.join(byt for byt in arrResp[i:i+ilen])
						calcval = str(int(hexval, 16)*dict[i][1]+int(dict[i][2]))+' '+dict[i][3]
					else:
						calcval = ''.join(chr(int(byt, 16)) for byt in arrResp[i:i+ilen])
					print "OBD-"+dict[i][0]+'----'+calcval
					#self.window.setProperty("OBD-"+dict[ind][0],calcval)
					i+=ilen
				else:
					i+=1
					
					
	def __init__(self):				

		obdcomms = obd.obd()
		pidDict = self._SetupValues('all')

		while obdcomms.port:				
			for (pid, dict) in pidDict.iteritems():
				try:
					self._process_pids(pid, dict)
				except:
					print 'None'
			time.sleep(2)
					
Main()
			

		
		
	
