from pydoc import text
from tkinter import Frame, PhotoImage
import tkinter
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backends._backend_tk import ToolTip
from enum import Enum
import threading
import time

class PlotStates(Enum):
    INIT=0
    NO_PLOT=1
    PLOT=2
    ERROR=3

class PlotModes(Enum):
    YVX = 0
    YVT = 1
    XVT = 2

UPDATE_INTERVAL = 0.1
BLINKING_INTERVAL = 4

UPDATING_COLOR = 'green'
UPDATED_COLOR = 'blue'

ERROR_COLOR = 'red'
BACKGROUND_COLOR = 'white'
FOREGROUND_COLOR = 'black'
DISABLED_COLOR = 'grey'

def list_part_extend(dest_list, source_list):
    dest_list[0].extend(source_list[0])
    dest_list[1].extend(source_list[1])
        
class Plot:
    
    def __init__(self, plot_frame:Frame):
        self.plot_frame = plot_frame
        self.state = PlotStates.INIT
        self.state_lock = threading.Lock()
        self.plot_lock = threading.Lock()
        self.axes_fixed = False
        self.pause_plot = False
        self.plot_mode = PlotModes.YVX
        self.plot_dirty = False
        self.daemon_running = False

    def setup_toolbar_buttons(self):
        #ATTRIBUTION : <a href="https://www.flaticon.com/free-icons/lock" title="lock icons">Lock icons created by Those Icons - Flaticon</a>
        self.lock_icon = PhotoImage(file='lock.png')
        self.lock_icon = self.lock_icon.subsample(20, 20)
        #ATTRIBUTION : <a href="https://www.flaticon.com/free-icons/pause" title="pause icons">Pause icons created by Debi Alpa Nugraha - Flaticon</a>
        self.pause_icon = PhotoImage(file='pause.png')
        self.pause_icon = self.pause_icon.subsample(20, 20)

        self.scale_lock_btn = tkinter.Button(master=self.toolbar, image=self.lock_icon, padx=0, pady=0, command=self.scale_locking)
        self.scale_lock_btn.pack(side='left')
        self.original_button_color = self.scale_lock_btn["bg"]
        ToolTip.createToolTip(self.scale_lock_btn, 'Prevent autoscaling of plot')

        self.pause_btn = tkinter.Button(master=self.toolbar, image=self.pause_icon, padx=0, pady=0, command=self.plot_pausing)
        self.pause_btn.pack(side='left')
        ToolTip.createToolTip(self.pause_btn, 'Pause realtime plot')

        self.plot_mode_btn = tkinter.Button(master=self.toolbar, padx=0, pady=0, command=self.plot_modesel)
        self.plot_mode_btn.pack(side='left')

    def plot_modesel(self):
        with self.state_lock:
            if self.state is PlotStates.PLOT:
                self.plot_mode = PlotModes((self.plot_mode.value+1)%len(PlotModes))
                self.axes_fixed = False
                self.apply_state()
        self.update_plot_canvas()

    def scale_locking(self):
        with self.state_lock:
            if self.state is PlotStates.PLOT:
                self.axes_fixed = not self.axes_fixed
                self.apply_state()
        self.update_plot_canvas()

    def copy_to_pause(self):
        self.pause_inc_buff = [self.inc_buff[0].copy(), self.inc_buff[1].copy()]
        self.pause_dec_buff = [self.dec_buff[0].copy(), self.dec_buff[1].copy()]
        self.pause_step_no  = self.step_no
        self.pause_dir = self.dir

    def plot_pausing(self):
        with self.state_lock:
            if self.state is PlotStates.PLOT:
                self.pause_plot = not self.pause_plot
                if self.pause_plot:
                    with self.plot_lock:
                        self.copy_to_pause()
                self.apply_state()
        self.update_plot_canvas()

    def color_all(self, color):
        self.plot.spines['bottom'].set_color(color)
        self.plot.spines['top'].set_color(color) 
        self.plot.spines['right'].set_color(color)
        self.plot.spines['left'].set_color(color)
        self.plot.tick_params(axis='x', colors=color)
        self.plot.tick_params(axis='y', colors=color)

    def tick_label_visibility(self, vis):
        if not vis:
            self.line1.set_linewidth(0)
            self.line2.set_linewidth(0)
            self.plot.tick_params(axis='x', colors=BACKGROUND_COLOR)
            self.plot.tick_params(axis='y', colors=BACKGROUND_COLOR)  
            self.plot.yaxis.label.set_color(BACKGROUND_COLOR)
        else:
            self.line1.set_linewidth(self.original_line_width)
            self.line2.set_linewidth(self.original_line_width)
            self.plot.tick_params(axis='x', colors=ERROR_COLOR if self.state is PlotStates.ERROR else FOREGROUND_COLOR)
            self.plot.tick_params(axis='y', colors=ERROR_COLOR if self.state is PlotStates.ERROR else FOREGROUND_COLOR)

    def plot_mode_states(self):
        if self.plot_mode is PlotModes.YVX:
            self.line1.set_color(UPDATING_COLOR)
            self.line2.set_color(UPDATED_COLOR)
        else:
            self.line1.set_color(UPDATED_COLOR)
            self.line2.set_color(UPDATING_COLOR)
        if self.plot_mode is PlotModes.YVX:
            self.plot.xaxis.label.set_text("input")
            self.plot.yaxis.label.set_text("output")
        elif self.plot_mode is PlotModes.YVT:
            self.plot.xaxis.label.set_text("time")
            self.plot.yaxis.label.set_text("output")
        elif self.plot_mode is PlotModes.XVT:
            self.plot.xaxis.label.set_text("time")
            self.plot.yaxis.label.set_text("input")
        self.update_plot()

    def toolbar_button_states(self):
        self.scale_lock_btn["bg"] = BACKGROUND_COLOR if self.axes_fixed else self.original_button_color
        self.pause_btn["bg"] = BACKGROUND_COLOR if self.pause_plot else self.original_button_color
        if self.plot_mode is PlotModes.YVX:
            self.plot_mode_btn["text"] = "YvX"
        elif self.plot_mode is PlotModes.YVT:
            self.plot_mode_btn["text"] = "Yvt"
        elif self.plot_mode is PlotModes.XVT:
            self.plot_mode_btn["text"] = "Xvt"

    def apply_state(self):
        assert(self.state is not PlotStates.INIT)
        if self.state is PlotStates.PLOT:
            self.color_all(FOREGROUND_COLOR)
            self.plot.xaxis.label.set_color(UPDATING_COLOR)
            self.plot.yaxis.label.set_color(UPDATING_COLOR)
            self.tick_label_visibility(True)
            self.plot_mode_states()
        elif self.state is PlotStates.ERROR:
            self.color_all(ERROR_COLOR)
            self.line1.set_color(ERROR_COLOR)
            self.line2.set_color(ERROR_COLOR)
            self.plot.xaxis.label.set_color(ERROR_COLOR)
            self.plot.xaxis.label.set_text("Error")
            self.tick_label_visibility(self.err_show)
            self.plot_dirty = True
        elif self.state is PlotStates.NO_PLOT:
            self.color_all(DISABLED_COLOR)
            self.plot.xaxis.label.set_color(DISABLED_COLOR)
            self.plot.xaxis.label.set_text("No data to plot")
            self.tick_label_visibility(False)
            self.plot_dirty = True
        self.toolbar_button_states()

    def pack(self, dpi=100, **kwargs):
        assert(self.state is PlotStates.INIT)
        w_aspect = self.plot_frame.winfo_screenwidth()/dpi
        h_aspect = self.plot_frame.winfo_screenheight()/dpi
        fig = Figure(figsize=(w_aspect, 0.895*h_aspect), dpi=dpi)
        fig.set_tight_layout(True)
        self.plot = fig.add_subplot(111)
        self.line1, = self.plot.plot([], [])
        self.line2, = self.plot.plot([], [])
        self.original_line_width = self.line1.get_linewidth()

        self.plot.set_xlabel('', fontsize=10, labelpad=0)

        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.setup_toolbar_buttons()
        self.toolbar.update()
        self.canvas.get_tk_widget().pack()

        with self.state_lock:
            self.state = PlotStates.NO_PLOT
            self.apply_state()
        self.update_plot_canvas()

    def start_daemon(self):
        assert(not self.daemon_running)
        threading.Thread(target=self.plot_loop, daemon=True).start()
        self.daemon_running = True

    def get_partial_buff(self, buff):
        step_no = self.pause_step_no if self.pause_plot else self.step_no
        part_x1 = buff[0][0:step_no]
        part_x2 = buff[0][step_no:]
        part_y1 = buff[1][0:step_no]
        part_y2 = buff[1][step_no:]
        return ((part_x1, part_y1), (part_x2, part_y2))

    def get_active_inactive_parts(self):
        inc_buff = self.pause_inc_buff if self.pause_plot else self.inc_buff
        dec_buff = self.pause_dec_buff if self.pause_plot else self.dec_buff
        dir = self.pause_dir if self.pause_plot else self.dir
        if not dir:
            active, inactive = self.get_partial_buff(dec_buff)
            inc_copy = [inc_buff[0].copy(), inc_buff[1].copy()]
            list_part_extend(inc_copy, active)
            active = inc_copy
        else :
            active, inactive = self.get_partial_buff(inc_buff)
            list_part_extend(inactive, dec_buff)
        return active, inactive

    def merge_parts(self, part1, part2):
        if len(part1[0]) and len(part2[0]):
            part2[0].insert(0, part1[0][-1])
            part2[1].insert(0, part1[1][-1])
        return part1, part2

    def autoscale(self):
        if self.axes_fixed:
            return
        else:
            self.plot.relim()
            self.plot.autoscale_view()

    def YVX_plot(self):
        return self.get_active_inactive_parts()

    def YVT_plot(self):
        active, inactive = self.get_active_inactive_parts()
        inactive_len = len(inactive[1])
        inactive = (list(range(0, inactive_len)), inactive[1])
        active = (list(range(inactive_len, inactive_len + len(active[1]))), active[1])
        return inactive, active

    def XVT_plot(self):
        active, inactive = self.get_active_inactive_parts()
        inactive_len = len(inactive[0])
        inactive = (list(range(0, inactive_len)), inactive[0])
        active = (list(range(inactive_len, inactive_len + len(active[0]))), active[0])
        return inactive, active

    def update_plot_canvas(self):
        if self.plot_dirty:
            self.canvas.draw()
            self.canvas.flush_events()
            self.plot_dirty = False

    def update_plot(self):
        with self.plot_lock:
            if self.plot_mode is PlotModes.YVX :
                part1, part2 = self.YVX_plot()
            elif self.plot_mode is PlotModes.YVT:
                part1, part2 = self.YVT_plot()
            elif self.plot_mode is PlotModes.XVT:
                part1, part2 = self.XVT_plot()
        (x1, y1), (x2, y2) = self.merge_parts(part1, part2)

        self.line1.set_xdata(x1)
        self.line1.set_ydata(y1)
        self.line2.set_xdata(x2)
        self.line2.set_ydata(y2)
        self.autoscale()
        self.plot_dirty = True

    def plot_loop(self):
        while(True):
            with self.state_lock:
                if self.state is PlotStates.PLOT and not self.pause_plot:
                    self.update_plot()
                elif self.state is PlotStates.ERROR:
                    self.err_cnt += 1
                    if not (self.err_cnt % BLINKING_INTERVAL):
                        self.err_show = not self.err_show
                        self.apply_state()
            self.update_plot_canvas()
            time.sleep(UPDATE_INTERVAL)

    def set_steps(self, steps):
        with self.plot_lock:
            self.steps = steps
            self.step_no = 0
            self.inc_buff = [[], []]
            self.dec_buff = [[], []]
            self.time_buff = []

    def on_half_loop(self):
        with self.plot_lock:
            self.dir = False
            self.step_no = 0

    def on_full_loop(self):
        with self.plot_lock:
            self.dir = True
            self.step_no = 0

    def on_data(self, data_time, input, response):
        with self.plot_lock:
            buff = self.inc_buff if self.dir else self.dec_buff
            if len(buff[0]) == self.steps:
                buff[0][self.step_no] = input
                buff[1][self.step_no] = response
                self.time_buff.pop(0)
            else:
                buff[0].append(input)
                buff[1].append(response)
            self.time_buff.append(data_time)
            self.step_no += 1
    
    def set_error(self):
        with self.state_lock:
            self.state = PlotStates.ERROR
            self.err_cnt = 0
            self.err_show = False
            self.apply_state()
        self.update_plot_canvas()

    def set_no_plot(self):
        with self.state_lock:
            self.state = PlotStates.NO_PLOT
            self.apply_state()
        self.update_plot_canvas()

    def set_plot(self):
        with self.state_lock:
            self.state = PlotStates.PLOT
            self.pause_plot = False
            self.apply_state()
        self.update_plot_canvas()
