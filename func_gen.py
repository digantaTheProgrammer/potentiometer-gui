import serial

def decode_line(line):
	return line.decode("utf-8")[:-1]

def get_scan_tuple_from_lineBytes(line) :
	vals = line.split(" ")
	if len(vals) != 3:
		return None
	try:
		sub_multiple = int(vals[0])
		sub_min = int(vals[1])
		sub_max = int(vals[2])
		return (sub_multiple, sub_min, sub_max)
	except ValueError:
		return None

def is_valid_scan_rate(line, scan_rate) :
	try:
		int(line)
	except ValueError:
		try:
			rate = float(line)
			return rate if round(rate) == scan_rate else 'scan rate mismatch. unknown bug'
		except ValueError:
			pass
	return 'device response not understood'

class FuncGen :

	def set_scan_rate(self, rate):
		if rate==None:
			self.scan_rate = (0, 0, 0)
			self.selected_multiple = 0
			self.selected_scan_rate = 0
		else:
			self.scan_rate = rate

	def __init__(self, device='/dev/ttyACM0', baud=9600, timeout=None):
		self.device		= device
		self.baud		= baud
		self.timeout	= timeout
		self.set_scan_rate(None)

	def start_new(self) :
		try:
			with serial.Serial(self.device, self.baud, timeout=self.timeout) as dev:
				dev.flushInput()
				rate = self.read_scan_rate(dev)
				if rate==self.scan_rate and self.selected_multiple:
					return self.write_scan_rate(dev)
				self.set_scan_rate(rate)
				if rate==None:
					return 'device response not understood'
				return self.scan_rate
		except serial.serialutil.SerialException as err:
			print(err)
			return 'could not connect with the device. ensure that the device is connected'
		except Exception as err:
			print(err)
			return 'unknown error ocurred'

	def read_scan_rate(self, dev):
		line = decode_line(dev.readline())
		rate = get_scan_tuple_from_lineBytes(line)
		return rate

	def write_scan_rate(self, dev):
		dev.write(bytes(f'{self.selected_scan_rate}\n', "utf-8"))
		dev.flush()
		line = decode_line(dev.readline())
		return is_valid_scan_rate(line, self.selected_scan_rate)

	def select_scan_rate(self, sel=None):
		if sel == None:
			sel = self.selected_multiple
		min_multiple = self.scan_rate[1]
		max_multiple = self.scan_rate[2]
		sub_multiple = self.scan_rate[0]

		assert(sel <= max_multiple and sel >= min_multiple and sel)
		self.selected_multiple = sel
		self.selected_scan_rate = round(sub_multiple/sel)
	
	def drop_selected_scan_rate(self):
		self.selected_multiple = 0
