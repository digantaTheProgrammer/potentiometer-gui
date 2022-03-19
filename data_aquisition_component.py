from tkinter import messagebox
import threading
import data_aquisition
from gui_states import GuiStates

class DataAquisitionGui:

    def __init__(self, state_updater, data_callback):
        self.data_aquisition = data_aquisition.DataAquisition(data_callback=data_callback, error_callback=self.error_callback)
        self.state_updater = state_updater
        self.err_msg = None
    
    def can_change_state(self, next_state, present_state):
        return True
    
    def on_cancel_change(self, present_state):
        pass

    def error_callback(self, msg):
        threading.Thread(target=self.error_handler, args=(msg,)).start()

    def error_handler(self, msg):
        self.err_msg = msg
        self.state_updater(lambda present_state, updater : updater(GuiStates.ERROR))

    def on_new_state(self, next_state, present_state):
        if next_state is GuiStates.ERROR or (next_state is not GuiStates.CONNECTED and next_state is not GuiStates.CONNECTING):
            if self.data_aquisition.is_running():
                if self.err_msg:
                    messagebox.showerror("Data Aquisition device", self.err_msg)
                self.data_aquisition.stop()
            self.err_msg = None
        elif next_state is GuiStates.CONNECTING:
            self.data_aquisition.start()

    def conn_callback(self, steps):
        threading.Thread(target=self.conn_handler).start()

    def conn_handler(self):
        self.state_updater(lambda present_state, updater : updater(GuiStates.CONNECTED) if present_state is GuiStates.CONNECTING else None)
