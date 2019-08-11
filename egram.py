"""
Support for graphing egrams using matplotlib and tkinter.
Displaying VENT_SIGNAL (m_vraw) and ATR_SIGNAL (m_araw)

Use PACEMAKER Section 4.7 for a guideline.
    - we are supporting printing egrams indirectly by writing the data points to
      a file
    - checkboxes to show atrial/ventricular/both egrams
    - serial module should update the data points
    - auto scroll?
    - 0.5x 1x 2x gain applied to both channels

Idea:
    - click button on main GUI to start egram
    - transmit egram request to the Pacemaker
    - open egram window
        - contains:
            - plot window (matplotlib)
            - gain selector (radio button)
            - signal selector (checkbox)
            - pause/resume button
    - receive egram data
        - get data from serial thread
        - periodic fetches using the animation update function

https://pythonprogramming.net/how-to-embed-matplotlib-graph-tkinter-gui/
https://matplotlib.org/faq/usage_faq.html
    - notes on what tkAgg is
https://learn.sparkfun.com/tutorials/graph-sensor-data-with-python-and-matplotlib/speeding-up-the-plot-animation
    - how to do fast plot updates
https://stackoverflow.com/questions/457246/what-is-the-best-real-time-plotting-widget-for-wxpython
    - this is really cool but we didn't use it... :P
"""

import time
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style

import tkinter as tk

import comms

""" Egram plot widget """
class EgramPlot(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.create_matplotlib_figure()

        self.create_plot()

        self.animation_period = 10 # milliseconds

        self.initialize_egram()

    """ Create the figure and tkinter canvas that display the plot in the frame
    """
    def create_matplotlib_figure(self):
        # matplotlib figure for the tkinter canvas
        style.use("seaborn-darkgrid")
        self.figure = Figure(figsize=(10,5), dpi=100)

        # make color same as background
        self.figure.set_facecolor(self["bg"])
    
        self.canvas = FigureCanvasTkAgg(self.figure, self)

        self.tk_canvas = self.canvas.get_tk_widget() 
        self.tk_canvas.pack()

    """ Create plot objects, relevant parameters and lines."""
    def create_plot(self):
        self.subplot = self.figure.add_subplot(1,1,1)
        self.subplot.set_facecolor(self["bg"])

        self.x_len = 1000
        self.y_range = [0,5000]
        self.xs = list(range(0, self.x_len))
        self.y_vraw = [0] * self.x_len
        self.y_araw = [0] * self.x_len
        self.subplot.set_ylim(self.y_range)

        self.line1, = self.subplot.plot(self.xs,self.y_vraw)
        self.line2, = self.subplot.plot(self.xs,self.y_araw)

        self.subplot.set_title("Electrogram")
        self.subplot.set_xlabel("ms")
        self.subplot.set_ylabel("mV")

    """
    Create and launch the serial read thread, send the egram request to the
    Pacemaker, and start the plot animation.
    """
    def initialize_egram(self):
        success = comms.request_egram() # ask Pacemaker for an egram
        self.egram_reader = comms.EgramThread(self.animation_period + 2)
        self.egram_reader.start()
        self.animation = animation.FuncAnimation(self.figure, 
                                             self.update_egram, 
                                             interval=self.animation_period,
                                             blit=True) # efficient draw

    """ Update the plot lines """
    def update_egram(self, *args):
        egram_data = self.egram_reader.get_data()    # get all available samples
        self.y_vraw = self.y_vraw + egram_data["m_vraw"]
        self.y_vraw = self.y_vraw[-self.x_len:]
        self.y_araw = self.y_araw + egram_data["m_araw"]
        self.y_araw = self.y_araw[-self.x_len:]
        self.line1.set_ydata(self.y_vraw)
        self.line2.set_ydata(self.y_araw)
        return [self.line1, self.line2]

    """ Change the plot y range """
    def update_y_range(self, y_range):
        ax = self.canvas.figure.axes[0]
        ax.set_ylim(y_range)
        self.canvas.draw()

    """ Pause the reader thread loop """
    def pause_egram(self): 
        self.egram_reader.quit()

    """ Resume the reader thread loop after a pause """
    def resume_egram(self): 
        # ensure that it was stopped
        self.egram_reader.quit()
        # this may conflict with the plot animation
        self.egram_reader = comms.EgramThread(self.animation_period + 2)
        self.egram_reader.start()

    def set_visible(self, visibility):
        self.line1.set_visible(visibility[0])
        self.line2.set_visible(visibility[1])

    """ Stop the serial read thread and send stop signal to the Pacemaker """
    def stop_egram(self):
        self.egram_reader.quit()
        comms.stop_egram() # if connected to Pacemaker, stop egram

    """ Override destroy to ensure that the serial read thread is stopped """
    def destroy(self):
        self.stop_egram()
        super().destroy()

class EgramPauseButton(tk.Button):
    def __init__(self, master=None, actions={"on_pause":None,"on_resume":None}):
        self.tk_text = tk.StringVar()
        self.button = super().__init__(master=master, textvariable=self.tk_text, 
                                                            command=self.toggle)
        self.tk_text.set("Pause")
        self.actions = actions

    def toggle(self):
        if self.tk_text.get() == "Resume":
            if self.actions["on_resume"]:
                self.actions["on_resume"]()
            self.tk_text.set("Pause")

        elif self.tk_text.get() == "Pause":
            if self.actions["on_pause"]:
                self.actions["on_pause"]()
            self.tk_text.set("Resume")

""" Encapsulates the gain selector radio buttons """
class EgramGainSelector(tk.Frame):
    def __init__(self, master=None, cmd=None):
        super().__init__(master)
        self.update_plot_gain = cmd
        self.create_widgets()

    """ Create gain selector radio buttons and the tkinter variable """
    def create_widgets(self):
        self.tk_gain_var = tk.StringVar()
        self.tk_gain_var.set("1x")

        # add callback for when tk_gain_var gets written by radio-button event
        self.tk_gain_var.trace_add("write", self.update_plot_y_range)
        values = ["0.5x", "1x", "2x"]
        for v in values:
            b = tk.Radiobutton(master=self, text=v, variable=self.tk_gain_var, value=v)
            b.pack(anchor="w")

    """ Update the egram plot y range (called when radio button clicked) """
    def update_plot_y_range(self, *args):
        y_range = None
        if self.tk_gain_var.get() == "0.5x":
            y_range = [0,10000]
        elif self.tk_gain_var.get() == "1x":
            y_range = [0,5000]
        elif self.tk_gain_var.get() == "2x":
            y_range = [0,2500]
        self.update_plot_gain(y_range)

""" Encapsulates the line visibility selector checkboxes """
class EgramLineSelector(tk.Frame):
    def __init__(self, master=None, cmd=None):
        super().__init__(master)
        self.update_line_visibility = cmd
        self.create_widgets()
        self.call_update_cmd()

    def create_widgets(self):
        self.tk_line_1_visible = tk.IntVar()
        self.tk_line_2_visible = tk.IntVar()
        self.tk_line_1_visible.set(1)
        self.tk_line_2_visible.set(1)

        self.tk_line_1_visible.trace_add("write", self.call_update_cmd)
        self.tk_line_2_visible.trace_add("write", self.call_update_cmd)

        self.line_1_checkbox = tk.Checkbutton(  master=self, 
                                                text="m_vraw",
                                                variable=self.tk_line_1_visible)
        self.line_2_checkbox = tk.Checkbutton(  master=self, 
                                                text="m_araw",
                                                variable=self.tk_line_2_visible)
        self.line_1_checkbox.pack(anchor="w")
        self.line_2_checkbox.pack(anchor="w")

    def call_update_cmd(self, *args):
        visibility = [
                        self.tk_line_1_visible.get(),
                        self.tk_line_2_visible.get(),
                     ]
        self.update_line_visibility(visibility)

""" Supports creating the egram monitor in a separate window. """
class EgramWin(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.create_widgets()

    """ Create the plot and button widgets """
    def create_widgets(self):
        self.egram_plot = EgramPlot(master=self)
        self.gain_selector = EgramGainSelector(master=self, 
                                             cmd=self.egram_plot.update_y_range)


        self.line_selector = EgramLineSelector(master=self,
                                                cmd=self.egram_plot.set_visible)

        actions = {
                    "on_pause":self.egram_plot.pause_egram,
                    "on_resume":self.egram_plot.resume_egram,
                  }
        self.tk_button = EgramPauseButton(master=self, actions=actions)

        self.gain_selector.pack(side="left")
        self.tk_button.pack(side="bottom", anchor="n")
        self.egram_plot.pack(side="left")
        self.line_selector.pack(side="left")
