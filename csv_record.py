import csv
from datetime import datetime
import threading
from distutils.log import ERROR
from enum import Enum
import math

from tkinter import Label, Button, Frame, messagebox
from tkinter.filedialog import asksaveasfilename
from os.path import exists, basename
from warnings import showwarning

class SaveStates(Enum):
    INIT            = 0
    NOACTION        = 1
    ACTION          = 2
    FILE_CHOSEN     = 3
    ERROR           = 4

def num_digs(n):
    return 1 + math.floor(math.log10(n))

def int_str(num, w):
    assert(num>=0)
    if num < pow(10, w):
        return str(num)
    exp_digs = num_digs(num_digs(num)-1)
    if exp_digs is not 1:
        exp_digs-=1
    width = w-5-exp_digs
    assert(width>0)
    return f'{num:.{width}E}'

def get_default_filename():
    return datetime.now().strftime('data_%d-%b-%H:%M:%S')

class CSVRecord:

    def __init__(self, frame):
        self.state = SaveStates.INIT
        self.widget_frame = Frame(frame)
        self.state_lock = threading.Lock()
        self.loop_write_lock = threading.Lock()
        self.csv_writer = None
        self.file_start_loop_count = None
        self.file_end_loop_count = None
        self.loop_count = 0
        self.recording = None

    def pack(self, **kwargs):
        assert(self.state is SaveStates.INIT)
        self.rec_label = Label(master=self.widget_frame, font=('Helvetica', 10, 'bold'), text="", width=12, anchor='e')
        self.rec_label.pack(side='left',  padx=(0, 10))

        self.loop_count_label = Label(master=self.widget_frame, width=7)
        self.loop_count_label.pack(side='left')

        self.record_button = Button(master=self.widget_frame, command=self.record, text="")
        self.record_button.pack(side='left')
        self.DEFAULT_BUTTON_COLOR = self.record_button['bg']

        self.widget_frame.pack(**kwargs)
        with self.state_lock:
            self.state = SaveStates.NOACTION
            self.applyState()            
    
    def get_record_button_state(self) :
        if self.state is SaveStates.FILE_CHOSEN:
            return ("stop", "red")
        if self.state is SaveStates.ERROR:
            return ("err!", "red4")
        if self.state is SaveStates.ACTION:
            return ("rec", "light green")
        return ("rec", self.DEFAULT_BUTTON_COLOR)

    def is_record_button_disabled(self):
        return self.state is SaveStates.NOACTION

    def get_rec_label_state(self):
        if self.state is SaveStates.FILE_CHOSEN:
            return ("REC|Loop# :", "light green")
        if self.state is SaveStates.ACTION or self.state is SaveStates.ERROR:
            return ("Loop# :", "yellow")
        if self.state is SaveStates.NOACTION:
            return ("Loop# :", "light gray")

    def update_loop_count_label_text(self):
        self.loop_count_label["text"] = int_str(self.loop_count, 7)

    def get_loop_count_label_color(self):
        if self.state is SaveStates.NOACTION:
            return "light gray"
        return "white"

    def applyState(self):
        assert(self.state is not SaveStates.INIT)
        (text, color) = self.get_record_button_state()
        self.record_button['text'] = text
        self.record_button['bg'] = color
        if self.is_record_button_disabled():
            self.record_button['state'] = 'disabled'
        else:
            self.record_button['state'] = 'normal'

        (text, color) = self.get_rec_label_state()
        self.rec_label['text'] = text
        self.rec_label['bg'] = color

        self.loop_count_label['bg'] = self.get_loop_count_label_color()
        self.update_loop_count_label_text()

    def set_get_recording_loop_count(self, recording_file):
        with self.loop_write_lock:
            prev_recording_file = self.recording
            self.recording = recording_file
            if recording_file:
                self.csv_writer = csv.writer(recording_file, dialect='excel')
            else:
                self.csv_writer = None
            return (self.loop_count, prev_recording_file)

    def create_new_recording(self):
        filename = asksaveasfilename(initialfile=get_default_filename(), title='Create new recording', filetypes=(('Comma Separated Values', '*.csv'),))
        if not filename:
            return
        try:
            recording_file = open(filename, 'w')
            (self.file_start_loop_count, _) = self.set_get_recording_loop_count(recording_file)
            self.file_start_loop_count += 1
            return True
        except Exception as err:
            print(err)
            messagebox.showerror("File create error", f'could not create {filename} for writing')
    
    def end_recording(self):
        (self.file_end_loop_count, recording_file) = self.set_get_recording_loop_count(None)
        num_loops_recorded = self.file_end_loop_count - self.file_start_loop_count + 1
        try :
            recording_file.close()
        except Exception as err:
            self.state = SaveStates.ERROR
            self.applyState()
            print(err)
            messagebox.showerror("Recording save error", f'{num_loops_recorded} loops recorded in {recording_file.name}')
            self.state = SaveStates.FILE_CHOSEN
            return
        messagebox.showinfo("Recording saved", f'{num_loops_recorded} loops recorded in {recording_file.name}')



    def record(self):
        with self.state_lock:
            if self.state is SaveStates.ACTION and self.create_new_recording():
                self.state = SaveStates.FILE_CHOSEN
                self.applyState()
            elif self.state is SaveStates.FILE_CHOSEN:
                self.state = SaveStates.ACTION
                self.applyState()
                self.end_recording()

    def set_action(self):
        with self.state_lock:
            self.state = SaveStates.ACTION
        self.applyState()
    
    def confirm_record_stop(self):
        (count, file) = self.set_get_recording_loop_count(self.recording)
        return messagebox.askyesno("Stop recording?", f'recording of {basename(file.name)} will be stopped ({count - self.file_start_loop_count + 1} loops recorded). continue?')

    def can_set_no_action(self):
        with self.state_lock:
            if self.state is SaveStates.FILE_CHOSEN:
                return self.confirm_record_stop()
            return True

    def set_no_action(self):
        with self.state_lock:
            prev_state = self.state
            self.state = SaveStates.NOACTION
            self.applyState()
            if prev_state is SaveStates.FILE_CHOSEN:
                self.end_recording()
            self.loop_count = 0
            self.applyState()

    def on_data(self, data_time, input, response):
        try :
            with self.loop_write_lock:
                if self.state is not SaveStates.ERROR and self.csv_writer and (self.file_start_loop_count <= self.loop_count):
                    self.csv_writer.writerow([self.loop_count, data_time, input, response])
        except Exception as err:
            threading.Thread(target=self.data_record_error, args=(err,)).start()

    def data_record_error(self, err):
        print(err)
        with self.state_lock :
            if self.state is SaveStates.FILE_CHOSEN:
                self.state = SaveStates.ERROR
                self.applyState()
                messagebox.showerror('Recording error', f'Error occured while recording to {basename(self.recording.name)}. Recording has been stopped')
                self.end_recording()
                self.state = SaveStates.ACTION
                self.applyState()

    def on_full_loop(self):
        with self.loop_write_lock:
            self.loop_count+=1
            self.update_loop_count_label_text()
