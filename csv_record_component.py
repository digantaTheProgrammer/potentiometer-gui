from csv_record import CSVRecord
from gui_states import GuiStates

class CSVRecordComponent:
    
    def __init__(self, frame) :
        self.csv_record = CSVRecord(frame)
    
    def can_change_state(self, next_state, present_state):
        if next_state is GuiStates.ERROR:
            return True
        if present_state is GuiStates.CONNECTED:
            return self.csv_record.can_set_no_action()
        return True

    def on_new_state(self, next_state, present_state):
        if next_state is GuiStates.CONNECTED:
            self.csv_record.set_action()
        else:
            self.csv_record.set_no_action()
    
    def pack(self, **kwargs):
        return self.csv_record.pack(**kwargs)

    def on_cancel_change(self, present_state):
        pass

    def on_data(self, data_time, input, response):
        return self.csv_record.on_data(data_time, input, response)

    def on_half_loop(self):
        pass

    def on_full_loop(self):
        return self.csv_record.on_full_loop()

