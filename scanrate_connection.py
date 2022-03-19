from os import abort
import threading, queue
from tkinter import N, messagebox
from enum import Enum

import func_gen
import scan_rate
from gui_states import GuiStates

class Action(Enum):
	CONNECT = 0

class ScanrateConnection :
	def __init__(self, state_updater, frame):
		self.state_updater = state_updater
		self.daemon_running = False
		self.action_queue = queue.Queue()
		self.scanrate_widget = scan_rate.ScanRate(self.connect_callback, frame)
		self.function_gen = func_gen.FuncGen()
		self.err_msg = None

	def pack(self, **kwargs):
		self.scanrate_widget.pack(**kwargs)

	def process_connect_request(self):
		if self.scanrate_widget.has_value():
			self.function_gen.select_scan_rate(self.scanrate_widget.selecting_multiple)	
		s_rate = self.function_gen.start_new()
		if type(s_rate) == str:
			self.error_callback(s_rate)
		elif type(s_rate) == tuple:
			if self.scanrate_widget.has_value():
				messagebox.showwarning("Function Generator", "function generator device range changed. select scan rate")
			else:
				messagebox.showinfo("Function Generator", "select scan rate")
			self.scanrate_widget.set_action(s_rate)
		else:
			self.state_updater(lambda _, updater: updater(GuiStates.CONNECTING))

	def daemon_loop(self):
		try:
			while True:
				action = Action(self.action_queue.get())
				if action == Action.CONNECT :
					self.process_connect_request()
		except Exception as err:
			print(err)
			messagebox.showerror("Bug", "unknown bug in function generator component. exiting")
			abort()

	def start_daemon(self):
		assert(not self.daemon_running)
		self.daemon_running = True
		threading.Thread(target=self.daemon_loop, daemon=True).start()

	def connect_callback(self):
		if self.daemon_running :
			self.state_updater(self.connect_action)
	
	def ready_state_update(self):
		self.scanrate_widget.set_no_action()
		self.action_queue.put(Action(Action.CONNECT))

	def connect_action(self, present_state, updater):
		if present_state is GuiStates.READY:
			self.ready_state_update()
		elif present_state is GuiStates.CONNECTED or present_state is GuiStates.ERROR:
			updater(GuiStates.READY)

	def error_callback(self, msg):
		self.err_msg = msg
		self.state_updater(self.error_action)
	
	def error_action(self, present_state, updater):
		if self.err_msg:
			updater(GuiStates.ERROR)

	def can_change_state(self, next_state, present_state):
		return True
	
	def on_new_state(self, next_state, present_state):
		if present_state is GuiStates.INIT :
			self.start_daemon()
		elif next_state is GuiStates.READY:
			self.ready_state_update()
		elif next_state is GuiStates.CONNECTED:
			self.scanrate_widget.set_action(self.scanrate_widget.scan_rate, self.scanrate_widget.selecting_multiple)
		elif next_state is GuiStates.ERROR:
			if self.err_msg:
				messagebox.showerror("Function Generator", self.err_msg)
				self.err_msg = None
				self.scanrate_widget.set_no_info()
				self.function_gen.drop_selected_scan_rate()
			if present_state is GuiStates.CONNECTING or present_state is GuiStates.CONNECTED :
				self.scanrate_widget.set_action(self.scanrate_widget.scan_rate)				

	def on_cancel_change(self, present_state):
		pass