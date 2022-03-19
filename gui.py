from tkinter import * 
from tkinter import messagebox
from threading import Lock
from os import abort

import status
import scanrate_connection
import csv_record_component
import data_mapper
import data_processor
import data_aquisition_component
import callback_fanout
import plot_component
from gui_states import GuiStates

class Gui:

    def __init__(self):
        self.components=[]
        self.state                 = GuiStates.INIT
        self.state_lock            = Lock()
        

    def run_gui(self):
        self.window = Tk()
        self.window.title('Potentiostat Data Aquisition and Plotting')
        self.width=self.window.winfo_screenwidth()
        self.height=self.window.winfo_screenheight()
        self.window.geometry("%dx%d" % (self.width, self.height))
        
        self.plot_frame = Frame(self.window)
        self.plot_frame.place(in_=self.window, relx=0.5, rely=0, anchor='n', relwidth=1, relheight=0.95)
        self.controls_frame = Frame(self.window)
        self.controls_frame.place(in_=self.window, anchor='s', relx=0.5, rely=1, relwidth=1, relheight=0.05)

        self.status = status.StatusComponent(self.controls_frame)
        self.status.pack(side='left')
        
        self.scanrate = scanrate_connection.ScanrateConnection(self.state_update, self.controls_frame)
        self.scanrate.pack(side='left', expand=True)

        self.csv_record = csv_record_component.CSVRecordComponent(self.controls_frame)
        self.csv_record.pack(side='left', expand=True)

        self.plot = plot_component.PlotComponent(self.plot_frame)
        self.plot.pack()

        self.data_mapper = data_mapper.DataMapper()
        self.data_processor = data_processor.DataProcessor([self.csv_record, self.plot], self.data_mapper)
        self.data_aquisition = data_aquisition_component.DataAquisitionGui(self.state_update, self.data_processor.processor)

        self.conn_callback = callback_fanout.CallbackFanout()
        self.conn_callback.add_callback(self.data_aquisition.conn_callback)
        self.conn_callback.add_callback(self.plot.conn_callback)
        self.data_processor.set_connection_callback(self.conn_callback.callback)

        self.components = [self.status, self.data_aquisition, self.scanrate, self.plot, self.csv_record]
        self.apply_ready()
        self.window.mainloop()

    def apply_ready(self):
        for component in self.components:
            assert(component.can_change_state(GuiStates(GuiStates.READY), GuiStates.INIT))
        
        for component in self.components:
            component.on_new_state(GuiStates.READY, GuiStates.INIT)
        
        self.state = GuiStates.READY

    def state_update(self, updater):
        assert(self.state is not GuiStates.INIT)
        with self.state_lock:
            updater(self.state, self.change_state)

    def change_state(self, next_state):
        last_component = None
        try :
            change = True
            for component in self.components:
                last_component = component
                if not component.can_change_state(next_state, self.state) :
                    change = False
                    break
            if change:
                for component in self.components:
                    last_component = component
                    component.on_new_state(next_state, self.state)
                self.state = next_state
            else:
                end_component = last_component 
                for component in self.components:
                    last_component = component
                    component.on_cancel_change(self.state)
                    if component == end_component:
                        break
            return change
        except Exception as err:
            print(f'Target state : {next_state}, Present state : {self.state}')
            print(f'Component where exception ocurred : {last_component}')
            print(f'Exception : {err}')
            messagebox.showerror("Error", "unknown error ocurred while updating UI. exiting")
            abort()

if __name__ == '__main__':
    Gui().run_gui()
