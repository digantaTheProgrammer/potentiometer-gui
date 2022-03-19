import serial
import threading
from enum import Enum
import protocol_format
import traceback
from protocol_format import ControlChar

class DeviceStates(Enum):
	RESET=0
	BEGIN=1
	CONNECTED=2

def get_steps(step):
	if step&0x8000 :
		return (step&0x7FFF, True)
	return (step, False)

class DataAquisition :

	def __init__(self, data_callback, error_callback, device='/dev/ttyUSB0', baud=115200, timeout=None):
		self.device = device
		self.baud = baud
		self.timeout = timeout
		self.data_callback = data_callback
		self.error_callback = error_callback
		self.stop_flag = False
		self.io_loop_thread = None
		self.state = DeviceStates.RESET


	def process_packet(self, packet):
		c_char 	= packet[0]
		data 	= packet[1]
		if c_char == protocol_format.ControlChar.TRANSACTION_BEGIN:
			return True
		if self.state is DeviceStates.BEGIN:
			if c_char is ControlChar.STEPS_FINALIZED:
					(self.steps, self.dir) = get_steps(data)
					self.step_number = 0
					self.state = DeviceStates.CONNECTED
					self.data_callback((self.dir, self.steps))
					return True
		elif self.state is DeviceStates.CONNECTED:
			if c_char is ControlChar.INVERSION:
				(n_steps, n_dir) = get_steps(data)  
				if self.steps != n_steps :
					self.error_callback('invalid response from aquisition device, possible bug')
				elif self.step_number != n_steps or self.dir == n_dir:
					self.error_callback('aquisition device went out of sync. Serial port too slow?')
				else :
					self.dir = n_dir
					self.step_number = 0
					self.data_callback((self.dir,))
					return True
			elif c_char is ControlChar.STEP_READING_NOT_AVAILABLE:
				self.error_callback('reading not available. Filter length too high?')
			elif c_char is ControlChar.STEP_READING:
				self.step_number+=1
				if self.step_number > self.steps:
					self.error_callback('invalid response from aquisition device, possible bug')
				else:
					self.data_callback((data, self.step_number, self.steps, self.dir))
					return True
		self.error_callback('aquisition device response not understood')
		return False

	def io_loop(self):
		try:
			with serial.Serial(self.device, self.baud, timeout=self.timeout) as dev:
				protocolFormat = protocol_format.ProtocolFormat()
				while( not self.stop_flag):
					packet = protocolFormat.deserialize(dev.read(4))
					if packet==None:
						self.error_callback('aquisition device response not understood')
						return
					if not self.process_packet(packet):
						return
		except serial.serialutil.SerialException as err:
			print(err)
			self.error_callback('could not connect with the aquisition device. ensure that the device is connected')
		except Exception as err:
			print(err)
			traceback.print_exc()
			self.error_callback('unknown error ocurred in communication with aquisition device')

	def start(self):
		assert(self.state is DeviceStates.RESET)
		self.stop_flag = False
		self.io_loop_thread = threading.Thread(target=self.io_loop)
		self.state = DeviceStates.BEGIN
		self.io_loop_thread.start()

	def is_running(self):
		return self.state is DeviceStates.BEGIN or self.state is DeviceStates.CONNECTED

	def stop(self):
		assert(self.is_running)
		self.stop_flag = True
		self.io_loop_thread.join()
		self.state = DeviceStates.RESET