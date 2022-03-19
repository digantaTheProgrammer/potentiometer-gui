from tkinter import Button, Label, Frame, messagebox
from enum import Enum
import threading

class ScanRateStates(Enum):
	INIT	=0
	NOINFO	=1
	NOACTION=2
	ACTION	=3

def disabled_button_color():
	return None

def disabled_label_color():
	return 'light gray'

def rate_val_color():
	return 'white'

def action_button_color():
	return 'light green'

class ScanRate:

	def __init__(self, connect_callback, control_frame):
		self.connect_callback = connect_callback
		self.control_frame = control_frame
		self.widget_frame = Frame(control_frame)
		self.state = ScanRateStates.INIT
		self.scan_rate = (0, 0, 0)
		self.selected_multiple = 0
		self.selecting_multiple = 0
		self.state_lock = threading.Lock()

	def pack(self, **kwargs):
		assert(self.state is ScanRateStates.INIT)

		self.rate_label = Label(master=self.widget_frame,
			text="scan rate: ", font=('Helvetica', 14, 'bold'), anchor='w')
		self.rate_label.pack(side='left',  padx=(0, 10))

		self.inc = Button(master =self.widget_frame, text='-', command= lambda : self.inc_dec_action(1), repeatdelay=500, repeatinterval=100)
		self.inc.pack(side='left')
		self.DEFAULT_BUTTON_COLOR = self.inc['bg']

		self.rate_val = Label(master=self.widget_frame, text="", width=10)
		self.rate_val.pack(side='left')

		self.dec = Button(master =self.widget_frame, text='+', command= lambda : self.inc_dec_action(-1), repeatdelay=500, repeatinterval=100)
		self.dec.pack(side='left')

		self.unit_label = Label(master=self.widget_frame, text="mV/s")
		self.unit_label.pack(side='left',  padx=(0, 10))

		self.action_button = Button(master=self.widget_frame, command=self.connect_callback)
		self.action_button.pack(side='left')

		self.widget_frame.pack(kwargs)

		with self.state_lock:
			self.state = ScanRateStates.NOINFO
			self.apply_state()


	def inc_dec_state(self):
		if self.state is ScanRateStates.NOINFO or self.state is ScanRateStates.NOACTION:
			return ('disabled', disabled_button_color())
		return ('normal', None)

	def action_button_state(self):
		if self.state is ScanRateStates.NOACTION or (self.state  is  ScanRateStates.ACTION and self.selected_multiple  is  self.selecting_multiple):
			return ('disabled', disabled_button_color())
		return ('normal', action_button_color())

	def action_button_text(self):
		if self.state  is  ScanRateStates.NOINFO:
			return 'connect'
		if self.state  is  ScanRateStates.NOACTION:
			return self.action_button['text']
		if self.state  is  ScanRateStates.ACTION:
			if self.selected_multiple  is  self.selecting_multiple:
				return 'applied'
			return 'apply'

	def rate_val_color(self):
		if self.state  is  ScanRateStates.NOINFO or self.state  is   ScanRateStates.NOACTION:
			return disabled_label_color()
		return rate_val_color()
	
	def apply_state(self):
		assert(self.state!=ScanRateStates.INIT)
		
		(state, color) = self.inc_dec_state()
		self.inc['state'] = self.dec['state'] = state
		self.inc['bg'] = self.dec['bg'] = color if color is not None else self.DEFAULT_BUTTON_COLOR
		
		(state, color) = self.action_button_state()
		self.action_button['state'] = state
		self.action_button['bg'] = color if color is not None else self.DEFAULT_BUTTON_COLOR

		self.action_button["text"] = self.action_button_text()

		self.rate_val["bg"] = self.rate_val_color()
	
	def has_value(self):
		return self.selecting_multiple != 0
	
	def get_value(self):
		return self.selecting_multiple

	def selecting_in_range(self):
		return self.selecting_multiple <= self.scan_rate[2] and self.selecting_multiple >= self.scan_rate[1]

	def update_rate_val_text(self):
		self.rate_val["text"] = round((self.scan_rate[0])/self.selecting_multiple, 2)

	def set_action(self, scan_rate, sel=None):
		with self.state_lock:
			self.scan_rate = scan_rate
			if sel:
				self.selected_multiple = self.selecting_multiple = sel
			else:
				self.selected_multiple = 0
				if not self.selecting_in_range():
					self.selecting_multiple = self.scan_rate[1]
			self.update_rate_val_text()
			self.state = ScanRateStates.ACTION
			self.apply_state()
	
	def set_no_action(self):
		with self.state_lock:
			self.state = ScanRateStates.NOACTION
			self.apply_state()
	
	def set_no_info(self):
		with self.state_lock :
			self.rate_val["text"] = ""
			self.state = ScanRateStates.NOINFO
			self.apply_state()

	def inc_dec_action(self, val):
		with self.state_lock:
			if self.state != ScanRateStates.ACTION:
				return
			self.selecting_multiple+=val
			if not self.selecting_in_range():
				self.selecting_multiple-=val
				messagebox.showerror("Scan Rate", "selected value out of range")
			else:
				self.update_rate_val_text()
			self.apply_state()


	