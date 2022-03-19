from operator import ne
from tkinter import Label
from turtle import color
from gui_states import GuiStates

class StatusComponent:
    
    def __init__(self, frame):
        self.frame = frame

    def can_change_state(self, next_state, present_state):
        return next_state is GuiStates.READY or next_state is GuiStates.CONNECTED or next_state is GuiStates.CONNECTING or next_state is GuiStates.ERROR

    def on_new_state(self, next_state, present_state):
        if next_state is GuiStates.READY:
            self.status["bg"] = "light yellow"
            self.status["text"] = "READY"
        elif next_state is GuiStates.CONNECTING:
            self.status["bg"] = "yellow"
            self.status["text"] = "CONNECTING"
        elif next_state is GuiStates.CONNECTED:
            self.status["bg"] = "light green"
            self.status["text"] = "CONNECTED"
        elif next_state is GuiStates.ERROR:
            self.status["bg"] = "red"
            self.status["text"] = "ERROR"
    
    def on_cancel_change(self, present_state):
        pass

    def pack(self, **kwargs):
        self.status = Label(master=self.frame, width=12, anchor='w')
        self.status.pack(**kwargs)