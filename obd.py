import serial
import time
import sys
import string

debug = 0

def log(txt):
	#if isinstance(txt, str):
	#	txt = txt.decode("utf-8")
	print txt

class obd:
	def __init__(self):
		global debug
		self.port = None
		#log("OBD script starting...")
		if debug:
			self.port = True
			return None
		#while not self.port:
		try:
			self.port = serial.Serial('/dev/rfcomm99', 115200, timeout=1)
		except:
			return None
			#log("OBD Serial not connected.")
			#time.sleep(10)

		if self.port:
			log("OBD Serial connected OK!")
			self.port.writeTimeout = 2
			self.port.readTimeout = 3
			self.get_response('ATZ')	#reset
			self.get_response('ATE0') 	#echo off
			#self.get_response('ATL0')	#linefeeds off
			self.get_response('ATAL')	#allow long
			self.get_response('ATIB10') #10400 baud
			self.get_response('ATSP5')	#Proto 5
			self.get_response('ATH1')	#headers on
			self.get_response('ATST32') #timeout
			self.get_response('ATSH8111F1')
			self.get_response('ATW00')
			print self.get_response('ATFI')
			
			
			#self.get_response('ATSPA')
			self.get_response('ATL1')
			#print "Voltage: "+self.get_response('ATRV')
			#print 'Searching proto'
			#self.get_response('0100')
			#time.sleep(3)
			
			###params = dict( arg.split("=") for arg in sys.argv[1].split("&"))
			
		#while self.port.isOpen():
		#	print "Voltage: "+self.get_response('ATRV')
		#	time.sleep(1)
		#	print "Proto: "+self.get_response('ATDP')
		#	time.sleep(1)
	
		
	def get_response(self, cmd):
		if self.send_command(cmd):
			#log('DEBUG: Sending '+cmd)
			inp = self.read_until_string('>')
			#return inp
			#log('DEBUG: Receive '+inp)
			if not inp: return ''
			val = inp.split('\r\n')
			try:
				return val[1].rstrip()
			except:
				return val[0].rstrip()
			#return inp
	
	def send_command(self, cmd):
		if self.port:
			time.sleep(0.02)
			try:
				self.port.flushOutput()
				self.port.flushInput()
				self.port.flush()
			except:
				log('OBD: Problem flushing. Continuing anyway')
			 #for c in cmd:
			#	 self.port.write(c)
			try:
				self.port.write(cmd)
				self.port.write("\r")
			except:
				try:
					log('OBD: Problem writing '+cmd+'. Trying again')
					time.sleep(0.1)
					self.port.write(cmd)
					self.port.write("\r")
				except:
					log('OBD: Problem writing '+cmd+'. Assume lost connection')
					self.port = None
					return False
			 #log("Send command:" + cmd.rstrip())
		return True
			 
	def read_until_string(self, stri):
		buffer = ''
		#wait = self.port.inWaiting()
		#if not wait>0: return False
		#print "(reading "+str(wait)+" chars)"
		lines = 0
		# self.port.readline()
		while lines < 3:
			if lines == 2:
				c = self.port.read(1)
				if c == stri:
					break
			c = self.port.readline()
			if lines == 0:
				answer = c
			buffer += c
			##print 'got '+c
			if c.endswith(stri):
				break
			elif 'NO DATA' in c:
				print 'fail'
				break
			lines += 1
		#print '.....'+buffer+'.......'
		if buffer: return buffer.rstrip()
		
			
			 
if ( __name__ == "__main__" ):
		obd = obd()
		if obd.port and (len(sys.argv) > 1):
			resp = obd.get_response(sys.argv[1])
			print "Response "+sys.argv[1]+': '+resp
			arrResp = resp.split(' ')
			try:
				print "ASCII: "+''.join(chr(int(i, 16)) for i in arrResp)
			except:
				print 'Hex unavail.'
			#try:
			print "Decimal: "+' '.join(str(int(i, 16)) for i in arrResp)
			#except:
			#	print "Dec unavail"
		else:
			while obd.port:
				#print "Voltage: "+obd.get_response('ATRV')
				for (ind,decval) in enumerate(obd.process_pids('2101')):
					log('%i: %s' % (ind, decval)) 
				time.sleep(1)