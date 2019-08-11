#!/usr/bin/env python3
""" The view module manages the GUI """
import tkinter as tk
import tkinter.messagebox
import csv

import params as p
import auth
#import egram
#import comms

class LoginFrame(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        
        self.pack()
        self.master = master
        self.start = auth.auth()

        #Setting up intial login screen
        master.title("3K04 - Group 12 - Heartscape")
        master.geometry("400x400")
        tk.Label(master, text="", font = "none 10").pack()
        tk.Label(master, text="3K04 - Group - 12 - Heartscape", font="none 12 bold").pack()
        tk.Label(master, text="", font = "none 10").pack()

        #setting up login and password entry fields
        tk.Label(master, text="Username:", font="none 12").pack()
        self.usernameBox = tk.Entry(master, width=14)
        self.usernameBox.pack()

        tk.Label(master, text="Password:", font="none 12").pack()
        self.passwordBox = tk.Entry(master, width = 14)
        self.passwordBox.pack()

        #Setting up login and register buttons
        tk.Label(master, text="", font="none 5").pack() 
        tk.Button(master, text="Log In", fg="white", bg="green", font="none 12 bold", command=self.login).pack()
        tk.Label(master, text="", font="none 5").pack() 
        tk.Button(master, text="Register", font="none 12 bold", command=self.register).pack()


    #if login button is pressed
    def login(self):
        self.db_interface = auth.auth()
        username = self.usernameBox.get()
        password = self.passwordBox.get()
        if (self.db_interface.login_auth(username, password) == False):
            tk.Label (self, text="Incorrect Credentials", fg="red", font="none 11").pack()
            username = None
            password = None
        else:
            self.master.withdraw()

            # update the params structure with the user specific values
            user_params = self.db_interface.get_fetch()
            for key in user_params:
                if isinstance(p.params[key], p.NonNumericParam):
                    programmable_strings = p.params[key].get_strings()
                    s = programmable_strings[user_params[key]]
                    p.params[key].set(s)
                else:
                    p.params[key].set(user_params[key])

            win_login = MainWin(master=self.master)
            win_login.title("Pacemaker DCM")

    #if register button is pressed
    def register(self):
        self.master.withdraw()
        win_register = RegisterWin(master=self.master)
        win_register.title("Register User")

    """ On window closure, back up the user parameters to the database """
    def destroy(self):
        # update the params structure with the user specific values
        self.db_interface.up_param()
        super().destroy()

        
class RegisterWin(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)

        self.geometry("400x400")
        tk.Label(self, text="3K04 - Group 12 - Heartscape", font="none 12 bold").pack()
        tk.Label(self, text="~Please fill in the info below~", font="none 12 bold").pack()
        tk.Label(self, text="                     ", font="none 12").pack()

        #Grabbing username
        tk.Label(self, text="Username:", font="none 12").pack()
        self.username = tk.Entry(self, width = 14)
        self.username.pack()
        #Grabbing password
        tk.Label(self, text="Password:", font="none 12").pack()
        self.password = tk.Entry(self, width=14)
        self.password.pack()

        #Grabbing password again to avoid password mismatch
        tk.Label(self, text="Re-Enter Password:=", font="none 12").pack()
        self.password2 = tk.Entry(self, width=14)
        self.password2.pack()
        
        tk.Label(self, text="                     ", font="none 12").pack()

        #Register button
       
        tk.Button(self, text="Register", font="none 12 bold", command=self.RegisterButton).pack()
        tk.Button(self, text="Return", font="none 12 bold", command=self.return_Login).pack()
                  
    def RegisterButton(self):
        NewUser = self.username.get()
        NewPass = self.password.get()
        NewPass2 = self.password2.get()

        self.start = auth.auth()
        if (NewUser == "") or (NewPass == ""):
            tk.Label(self, text="Invalid Input", fg="red", font="none 12 bold").pack()
        elif (NewPass != NewPass2):
            tk.Label(self, text="Passwords do not match", fg="red", font="none 12 bold").pack()
        else:
            if (self.start.reg_auth(NewUser, NewPass) == (True, False, False)):
                tk.Label(self, text="Successful", fg="green", font="none 12 bold").pack()
            elif (self.start.reg_auth(NewUser, NewPass) == (False, False, True)):
                tk.Label(self, text="User Already Exists", fg="red", font="none 12 bold").pack()
            elif (self.start.reg_auth(NewUser, NewPass) == (False, True, False)):
                tk.Label(self, text="Max Users", fg="red", font="none 12 bold").pack()
            elif (self.start.reg_auth(NewUser, NewPass) == (False, True, True)):
                tk.Label(self, text="Max Users", fg="red", font="none 12 bold").pack()

    def destroy(self):
        root.deiconify()
        super().destroy()

    def return_Login(self):
        self.withdraw()
        root.deiconify()
            
class NumericParamFrame(tk.Frame):
    def __init__(self, param, name, master=None):
        super().__init__(master)
        self.pack()

        self.param = param
        self.name = name
        
        self.tk_var = tk.IntVar()
        self.tk_var.set(self.param.get())

        self.create_widgets()

    def create_widgets(self):
        self.tk_incr_button = tk.Button(self, text=">", command=self.incr)
        self.tk_decr_button = tk.Button(self, text="<", command=self.decr)

        if self.name:
            self.tk_name = tk.Label(self, text=self.name)
        else:
            self.tk_name = tk.Label(self, text="param")

        self.tk_value = tk.Label(self, textvariable=self.tk_var)

        self.tk_name.pack(side="left")
        self.tk_decr_button.pack(side="left")
        self.tk_value.pack(side="left")
        self.tk_incr_button.pack(side="left")

    def incr(self):
        self.param.increment()
        self.tk_var.set(self.param.get());

    def decr(self):
        self.param.decrement()
        self.tk_var.set(self.param.get());

"""
Allows user to set non numeric parameter values.
TODO:
    - make it neater
        - consider if this should be replaced with radio button menu instead
        - horizontal or vertical orientation?
    - button to default to nominal value
    -
"""

class NonNumericParamFrame(tk.Frame):
    def __init__(self, param, name, master=None):
        super().__init__(master)
        self.pack()
        self.param = param
        self.name = name
        self.tk_var = tk.StringVar()
        self.tk_var.set(self.param.get_str())
        # add callback for when tk_var gets written by the radio-button events
        self.tk_var.trace_add("write", self.update_param)

        self.create_widgets()

    def create_widgets(self):
        if self.name:
            self.tk_name = tk.Label(self, text=self.name)
        else:
            self.tk_name = tk.Label(self, text="param")
        self.tk_name.pack(side="left")

        for text in self.param.get_strings():
            b = tk.Radiobutton(master=self, text=text, variable=self.tk_var, value=text)
            b.pack(side="left")

    def update_param(self, *args):
        self.param.set(self.tk_var.get())

class NonNumericParamDropDown(NonNumericParamFrame):
    def create_widgets(self):
        if self.name:
            self.tk_name = tk.Label(self, text=self.name)
        else:
            self.tk_name = tk.Label(self, text="param")
        self.tk_name.pack(side="left")

        values = self.param.get_strings()
        self.options = tk.OptionMenu(self, self.tk_var, *values)
        self.options.pack(side="left")

""" Connection Status Light to check if the pacemaker is connected. """
class Light(tk.Label):
    def __init__(self, master=None, period=100):
        self.tk_text = tk.StringVar()
        self.light = super().__init__(master=master, relief="raised", textvariable=self.tk_text)
        self.pack(anchor="e")

        self.period = period

        self.check_status()
        self.cc = 1;
    def check_status(self):
        self.cc = 0;
        if (self.cc):
            self.turn_on()
        else:
            self.turn_off()

        self.after(self.period, self.check_status)

    def turn_on(self):
        self.tk_text.set("Connected")
        self.configure(bg="green")

    def turn_off(self):
        self.tk_text.set("Disconnected")
        self.configure(bg="red")

""" Encapsulates the parameters for the current pacing mode. """
class ParamsFrame(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.master = master
        relevant_params = p.params_by_pacing_mode[p.params["mode"].get_str()]
        for param_name in relevant_params:
            parameter = p.params[param_name]
            if isinstance(parameter, p.NumericParam):
                NumericParamFrame(parameter, name=param_name, master=self)
            else:
                NonNumericParamDropDown(parameter, name=param_name, master=self)

""" 
Main window that contains different frame types.
When switching the main frame, destroy the previous frame.
"""
class MainWin(tk.Toplevel):
    def __init__(self, master=None):
        print(master)
        super().__init__(master)
        self.master = master
        self.geometry("800x800")
        self.light = Light(master=self)

        menubar = tk.Menu(master=self)
        self.config(menu=menubar)

        sub_file = tk.Menu(menubar)

        sub_file.add_command(label="Start Egram", command=self.start_egram)
        sub_file.add_command(label="About",command=self.about)
        #sub_file.add_command(label= "Log-Out",command = self.logout)
        sub_file.add_separator()
        sub_file.add_command(label="Exit", command=self.destroy)

        menubar.add_cascade(label="File", menu=sub_file)

        self.parameters_frame = ParamsFrame(self)

        self.tk_mode = tk.StringVar()
        self.tk_mode.trace_add("write", self.mode_update)
        self.tk_mode.set(p.params["mode"].get_str())

        sub_mode = tk.Menu(menubar)
        for mode in (p.params["mode"].get_strings())[1:]: # skip "Off" case
            sub_mode.add_radiobutton(label=mode, 
                                     variable=self.tk_mode, 
                                     value=mode)

        menubar.add_cascade(label="Mode", menu=sub_mode)

        menubar.add_command(label="Send Params", command=self.send_params)
        
    
    def send_params(self):
        comms.update_pacemaker_params()

    """ Ensure that all windows close (even invisible windows) """
    def destroy(self):
        self.destroy = super().destroy # a fancy trick to prevent recursion
        self.master.destroy()

    def about(self):
        tkinter.messagebox.showinfo('About', '3K04 Final Project\nMade by Group 12 - Heartscape\nJacob Luft\nPierre Tadrus\nRey Pastolero\nSean Stel\nShubham Shukla\nHamza Rahmani\nDevin Jhaveri\nAlex Hollebone')

    def start_egram(self):
        egram.EgramWin(master=self)

    def mode_update(self, *args):
        p.params["mode"].set(self.tk_mode.get())
        self.parameters_frame.destroy()
        self.parameters_frame = ParamsFrame(master=self)

    #def logout(self):
    #    self.master.withdraw()
    #    root.deiconify()
    #    login = LoginFrame(master=root)
    
if __name__ == "__main__":
    root = tk.Tk()
    
    # name and add the login frame to the root window
    login = MainWin(master=root)
    root.mainloop()
    
