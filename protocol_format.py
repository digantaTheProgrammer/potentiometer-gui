from enum import Enum

class ControlChar(Enum):
	TRANSACTION_BEGIN 			= 0
	STEPS_FINALIZED 			= 1
	STEP_READING 				= 2
	STEP_READING_NOT_AVAILABLE	= 3
	INVERSION					= 4

def get_data(byte1, byte2):
	return ((byte1&0xFF)<<8)+(byte2&0xFF)

class ProtocolFormat:
	
	def __init__(self):
		self.transaction_id = None

	def inc_transaction_id(self):
		self.transaction_id = (self.transaction_id + 1) & 0xFF

	def deserialize(self, buff):
		assert(len(buff)==4)
		tid = buff[0]
		c_char = None
		try:
			c_char = ControlChar(buff[1])
		except ValueError:
			print(f'invalid control character {buff[1]}')
			return None

		if self.transaction_id == None:
			if c_char != ControlChar.TRANSACTION_BEGIN:
				print('expected TRANSACTION_BEGIN')
				return None
			self.transaction_id = tid
		elif self.transaction_id != tid:
			print(f'transaction id mismatch {tid} vs {self.transaction_id}')
			return None
		
		self.inc_transaction_id()
		if c_char==ControlChar.STEP_READING_NOT_AVAILABLE or c_char==ControlChar.TRANSACTION_BEGIN:
			return (c_char, 0)
		return (c_char, get_data(buff[2], buff[3]))

