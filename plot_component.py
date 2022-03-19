import plot
from gui_states import GuiStates

class PlotComponent:
    
    def __init__(self, frame):
        self.plot = plot.Plot(frame)
    
    def can_change_state(self, next_state, present_state):
        return True

    def on_new_state(self, next_state, present_state):
        if present_state is GuiStates.INIT:
            self.plot.start_daemon()
        elif next_state is GuiStates.CONNECTED:
            self.plot.set_plot()
        elif next_state is GuiStates.ERROR:
            self.plot.set_error()
        else:
            self.plot.set_no_plot()
    
    def pack(self, **kwargs):
        self.plot.pack(**kwargs)

    def on_cancel_change(self, present_state):
        pass

    def conn_callback(self, steps):
        self.plot.set_steps(steps)

    def on_data(self, data_time, input, response):
        return self.plot.on_data(data_time, input, response)
    
    def on_half_loop(self):
        return self.plot.on_half_loop()

    def on_full_loop(self):
        return self.plot.on_full_loop()
