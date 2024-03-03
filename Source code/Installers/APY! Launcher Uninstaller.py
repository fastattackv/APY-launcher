"""
This file contains the app to uninstall the launcher
"""

import customtkinter as ctk
import os
import shutil
import subprocess
from custom_ctk_toplevels import get_resource_path, askdir, showwarning, askyesno


_version = "1.0.0"


def is_path_a_launcher_path(path_to_check: str) -> bool:
    """ Checks if the given path is a correct path where the launcher is installed (checks if the given directory is "APY! Launcher" and if there is "APY! Launcher.exe" in it) """
    if os.path.exists(os.path.join(path_to_check, "APY! Launcher.exe")) and path_to_check.endswith("APY! Launcher"):
        return True
    else:
        return False


def hide_all():
    step_1.hide()
    step_2.hide()


class Step1:
    """ Start """
    def __init__(self):
        self.title_label = ctk.CTkLabel(win, text="Welcome to the APY! launcher uninstaller", font=subhead_font)
        self.version_label = ctk.CTkLabel(win, text=f"Uninstaller version: {_version}")
        self.start_button = ctk.CTkButton(win, text="Start", command=show_step_2)

    def show(self):
        hide_all()
        self.title_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        self.version_label.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        self.start_button.grid(row=2, column=0, columnspan=2, padx=5, pady=100)

    def hide(self):
        self.title_label.grid_forget()
        self.version_label.grid_forget()
        self.start_button.grid_forget()


class Step2:
    """ Confirming """
    def __init__(self):
        self.title_label = ctk.CTkLabel(win, text="Is the path below the correct path to uninstall ?", font=bold_font)
        self.path_frame = ctk.CTkScrollableFrame(win, width=350, height=30, orientation="horizontal")
        self.path_label = ctk.CTkLabel(self.path_frame, text=path)
        self.path_label.pack()
        self.yes_button = ctk.CTkButton(win, text="Yes", command=show_step_3)
        self.no_button = ctk.CTkButton(win, text="No", command=self.ask_new_path)

    def show(self):
        hide_all()
        self.title_label.grid(row=0, column=0, columnspan=2, pady=5)
        self.path_frame.grid(row=1, column=0, columnspan=2, pady=15)
        self.yes_button.grid(row=2, column=0, pady=5)
        self.no_button.grid(row=2, column=1, pady=5)

    def hide(self):
        self.title_label.grid_forget()
        self.path_frame.grid_forget()
        self.yes_button.grid_forget()
        self.no_button.grid_forget()

    def ask_new_path(self):
        global path
        resp = askdir("Select a path to uninstall the launcher from")
        if resp is not None:  # not cancelled
            if is_path_a_launcher_path(path):
                path = resp
                self.path_label.configure(text=path)
            else:
                showwarning("Selecting path", "The selected path does not contain a launcher installation")


def show_step_1():
    step_1.show()


def show_step_2():
    global path
    if not is_path_a_launcher_path(path):
        path = askdir("Select a path to uninstall the launcher from", allow_cancel=False)
        while True:
            if path is None:  # cancelled
                path = os.getcwd()
                break
            elif not is_path_a_launcher_path(path):
                showwarning("Selecting path", "The selected path does not contain a launcher installation")
                path = askdir("Select a path to uninstall the launcher from", allow_cancel=False)
            else:  # valid path
                step_2.show()
                break
    else:
        step_2.show()


def show_step_3():
    if askyesno("Confirmation", "Do you really want to uninstall the APY! launcher ?"):
        if os.path.dirname(path).split("\\")[-1].split("/")[-1] == "APY!" and os.listdir(os.path.dirname(path)) == ["APY! Launcher"]:  # no other APY! apps installed
            shutil.copy2("APY!_Launcher_Uninstaller.bat", os.path.dirname(os.path.dirname(path)))
            subprocess.Popen([os.path.join(os.path.dirname(os.path.dirname(path)), "APY!_Launcher_Uninstaller.bat"), os.path.dirname(path)])
            win.destroy()
        else:
            shutil.copy2("APY!_Launcher_Uninstaller.bat", os.path.dirname(path))
            subprocess.Popen([os.path.join(os.path.dirname(path), "APY!_Launcher_Uninstaller.bat"), path])
            win.destroy()


# defining window
win = ctk.CTk()
win.geometry("400x500")
win.iconbitmap(get_resource_path("launcher data/launcher_icon.ico"))
win.title("APY! Launcher Uninstaller")
win.resizable(False, False)
win.grid_columnconfigure(0, weight=1)
win.grid_columnconfigure(1, weight=1)

# defining ctk variables
subhead_font = ctk.CTkFont(size=19, weight="bold")
bold_font = ctk.CTkFont(size=13, weight="bold")

path = os.getcwd()

step_1 = Step1()
step_2 = Step2()

# starting
step_1.show()
win.mainloop()
