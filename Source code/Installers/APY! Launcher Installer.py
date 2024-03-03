""" This file contains the app to install the launcher """

import customtkinter as ctk
import os
import requests
import zipfile
import shutil
import threading
import pythoncom
from win32com.client import Dispatch

from custom_ctk_toplevels import get_resource_path, FileExplorer, showwarning, askyesno
from APY_launcher_updates import check_versions


_version = "1.0.0"


def on_closing():
    """ Handles the closing event """
    if installing:
        showwarning("Closing", "The launcher is currently being installed, closing is impossible\n(Please don't end the task in the task manager except you are sure it's stuck because it can corrupt the application)")
    else:
        win.destroy()


def hide_all():
    step_1.hide()
    step_2.hide()
    step_3.hide()
    step_4.hide()
    step_5.hide()


class NotLaunchable:
    """ Not launchable installer page """
    def __init__(self, text: str):
        self.title_label = ctk.CTkLabel(win, text=text)
        self.stop_button = ctk.CTkButton(win, text="Exit", command=win.destroy)

    def show(self):
        self.title_label.grid(row=0, column=0, columnspan=2, pady=5)
        self.stop_button.grid(row=1, column=0, columnspan=2, pady=30)


class Step1:
    """ Start """
    def __init__(self):
        self.title_label = ctk.CTkLabel(win, text="Welcome to the APY! launcher installer", font=subhead_font)
        self.version_label = ctk.CTkLabel(win, text=f"Installer version: {_version}")
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
    """ Path selection """
    def __init__(self):
        self.title_label = ctk.CTkLabel(win, text="Select the directory to install the launcher to", font=bold_font)
        if os.path.isdir(os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')):
            self.explorer = FileExplorer(win, "directory", initialdir=os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop'), width=398, height=424)
        else:
            self.explorer = FileExplorer(win, "directory", width=398, height=424)
        self.back_button = ctk.CTkButton(win, text="Back", command=show_step_1)
        self.next_button = ctk.CTkButton(win, text="Ok", command=show_step_3)

    def show(self):
        hide_all()
        self.title_label.grid(row=0, column=0, columnspan=2, pady=5)
        self.explorer.grid(row=1, column=0, columnspan=2)
        self.back_button.grid(row=2, column=0, pady=5)
        self.next_button.grid(row=2, column=1, pady=5)

    def hide(self):
        self.title_label.grid_forget()
        self.explorer.grid_forget()
        self.back_button.grid_forget()
        self.next_button.grid_forget()


class Step3:
    """ Other parameters choice (language, shortcut on desktop...) """
    def __init__(self):
        self.title_label = ctk.CTkLabel(win, text="Select the other parameters", font=bold_font)

        self.language_label = ctk.CTkLabel(win, text="Languages to install:", font=bold_font)
        self.language_frame = ctk.CTkScrollableFrame(win, width=400)
        self.language_checkboxes_list = []
        row = 0
        for language in ["english", "français"]:
            self.language_checkboxes_list.append(ctk.CTkCheckBox(self.language_frame, text=language))
            self.language_checkboxes_list[-1].grid(row=row, column=0, padx=3, pady=8)
            row += 1

        self.shortcut_checkbox = ctk.CTkCheckBox(win, text="Create a shortcut on desktop")

        self.back_button = ctk.CTkButton(win, text="Back", command=show_step_2)
        self.next_button = ctk.CTkButton(win, text="Ok", command=show_step_4)

    def show(self):
        hide_all()
        self.title_label.grid(row=0, column=0, columnspan=2, pady=5)
        self.language_label.grid(row=1, column=0, columnspan=2, pady=5)
        self.language_frame.grid(row=2, column=0, columnspan=2)
        self.shortcut_checkbox.grid(row=3, column=0, columnspan=2, pady=20)
        self.back_button.grid(row=4, column=0, pady=10)
        self.next_button.grid(row=4, column=1, pady=10)

    def hide(self):
        self.title_label.grid_forget()
        self.language_label.grid_forget()
        self.language_frame.grid_forget()
        self.shortcut_checkbox.grid_forget()
        self.back_button.grid_forget()
        self.next_button.grid_forget()


class Step4:
    """ Verification of the parameters """
    def __init__(self):
        self.title_label = ctk.CTkLabel(win, text="Verification of the entered parameters", font=bold_font)

        self.version_label = ctk.CTkLabel(win)

        self.path_title_label = ctk.CTkLabel(win, text="Installation path:")
        self.path_frame = ctk.CTkScrollableFrame(win, orientation="horizontal", width=350, height=30)
        self.path_label = ctk.CTkLabel(self.path_frame, text="")
        self.path_label.pack()

        self.language_title_label = ctk.CTkLabel(win, text="Languages to install:")
        self.language_frame = ctk.CTkScrollableFrame(win, width=350, height=100)
        self.languages_label_list = []

        self.back_button = ctk.CTkButton(win, text="Back", command=lambda: show_step_3(False))
        self.next_button = ctk.CTkButton(win, text="Ok", command=show_step_5)

    def show(self):
        hide_all()
        self.title_label.grid(row=0, column=0, columnspan=2, pady=5)
        self.version_label.grid(row=1, column=0, columnspan=2, pady=5)
        self.path_title_label.grid(row=2, column=0, columnspan=2, pady=5)
        self.path_label.configure(text=step_2.explorer.get_path())
        self.path_frame.grid(row=3, column=0, columnspan=2)
        self.language_title_label.grid(row=4, column=0, columnspan=2, pady=5)
        for widget in self.languages_label_list:
            widget.destroy()
        self.languages_label_list.clear()
        row = 0
        for language in [widget.cget("text") for widget in step_3.language_checkboxes_list if widget.get()]:
            self.languages_label_list.append(ctk.CTkLabel(self.language_frame, text=language))
            self.languages_label_list[-1].grid(row=row, column=0)
            row += 1
        self.language_frame.grid(row=5, column=0, columnspan=2)
        self.back_button.grid(row=6, column=0, pady=10)
        self.next_button.grid(row=6, column=1, pady=10)

    def hide(self):
        self.title_label.grid_forget()
        self.version_label.grid_forget()
        self.path_title_label.grid_forget()
        self.path_frame.grid_forget()
        self.language_title_label.grid_forget()
        self.language_frame.grid_forget()
        self.back_button.grid_forget()
        self.next_button.grid_forget()


class Step5:
    """ Installation """
    def __init__(self):
        self.title_label = ctk.CTkLabel(win, text="Installation, please wait", font=bold_font)
        self.progress_bar = ctk.CTkProgressBar(win, width=300, height=15)
        self.progress_bar.set(0)
        self.current_process_label = ctk.CTkLabel(win, text="")
        self.reload_variable = ctk.IntVar(win, 0)  # variable to change widgets on the interface
        self.reload_variable.trace_add("write", self.reload)
        self.installed_path = ""

    def show(self):
        hide_all()
        self.title_label.grid(row=0, column=0, columnspan=2, pady=30)
        self.progress_bar.grid(row=1, column=0, columnspan=2, pady=10)
        self.current_process_label.grid(row=2, column=0, columnspan=2)
        self.install()

    def hide(self):
        self.title_label.grid_forget()
        self.progress_bar.grid_forget()
        self.current_process_label.grid_forget()

    @staticmethod
    def start_launcher(path: str):
        """ Starts the launcher at the given path and stops the installer """
        os.chdir(os.path.dirname(path))
        os.startfile(path)
        win.destroy()

    def reload(self, *args):
        """ Reloads the interface with the widgets corresponding to the value of self.reload_variable """
        var = self.reload_variable.get()
        if var == 0:  # base widgets
            self.progress_bar.set(0)
            self.current_process_label.configure(text="")
        elif var == 1:  # path creation
            self.progress_bar.set(0)
            self.current_process_label.configure(text="Creating directories to final path")
        elif var == 2:  # downloading
            self.progress_bar.set(0.1)
            self.current_process_label.configure(text="Downloading files")
        elif var == 3:  # unzip
            self.progress_bar.set(0.8)
            self.current_process_label.configure(text="Preparing files")
        elif var == 4:  # end
            self.progress_bar.set(1)
            self.current_process_label.configure(text="Done")
            self.title_label.configure(text="Installation is done")
            ctk.CTkButton(win, text="Start the launcher", command=lambda a=self.installed_path: self.start_launcher(a)).grid(row=3, column=0, pady=10, padx=10)
            ctk.CTkButton(win, text="Exit", command=win.destroy).grid(row=3, column=1, pady=10, padx=10)
        elif var == 5:  # connexion error
            self.current_process_label.configure(text="Check your connexion or try again later")
            self.title_label.configure(text="Installation stopped: connexion error")
            ctk.CTkButton(win, text="Exit", command=win.destroy).grid(row=3, column=1, pady=50, padx=10)

    def install(self):
        thread = threading.Thread(target=self._install, name="installer: installing launcher")
        thread.start()

    def _install(self):
        global installing
        installing = True

        path = step_2.explorer.get_path()
        languages = [widget.cget("text") for widget in step_3.language_checkboxes_list if widget.get()]
        desktop_shortcut = bool(step_3.shortcut_checkbox.get())
        if os.path.isdir(os.path.join(path, "APY!/APY! Launcher")):
            os.remove(os.path.join(path, "APY!/APY! Launcher"))
        elif os.path.isdir(os.path.join(path, "APY! Launcher")):
            os.remove(os.path.join(path, "APY! Launcher"))

        # path creation ("APY!" folder)
        self.reload_variable.set(1)
        if not path.endswith("/APY!") and not path.endswith("\\APY!"):  # have to create APY! directory
            path = os.path.join(path, "APY!")
            os.mkdir(path)

        # download
        self.reload_variable.set(2)
        try:
            response = requests.get("https://github.com/fastattackv/APY-launcher/raw/main/Downloads/APY!%20Launcher.zip")
            with open(os.path.join(path, "APY! Launcher.zip"), "wb") as f:
                f.write(response.content)
            for language in languages:
                response = requests.get(f"https://github.com/fastattackv/APY-launcher/raw/main/Downloads/{language}.lng")
                with open(os.path.join(path, f"{language}.lng"), "wb") as f:
                    f.write(response.content)
        except requests.ConnectionError:
            self.reload_variable.set(5)
            installing = False
        except requests.Timeout:
            self.reload_variable.set(5)
            installing = False
        else:  # download went well

            # unzip
            self.reload_variable.set(3)
            with zipfile.ZipFile(os.path.join(path, "APY! Launcher.zip"), "r") as f:
                f.extractall(path)
            os.remove(os.path.join(path, "APY! Launcher.zip"))
            # moving language files
            for language in languages:
                shutil.copy2(os.path.join(path, f"{language}.lng"), os.path.join(path, "APY! Launcher/lng files", f"{language}.lng"))
                os.remove(os.path.join(path, f"{language}.lng"))
            # changing language in the params.APYL file
            with open(os.path.join(path, "APY! Launcher/params.APYL"), "r", encoding="utf-8") as f:
                params = f.readlines()
            params[0] = f"language={languages[0]}\n"
            with open(os.path.join(path, "APY! Launcher/params.APYL"), "w", encoding="utf-8") as f:
                f.writelines(params)

            # creating shortcut
            if desktop_shortcut:
                shell = Dispatch('WScript.Shell', pythoncom.CoInitialize())
                shortcut = shell.CreateShortCut(os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop/APY! Launcher.lnk'))
                shortcut.Targetpath = os.path.join(path, "APY! Launcher/APY! Launcher.exe")
                shortcut.WorkingDirectory = os.path.join(path, "APY! Launcher")
                shortcut.IconLocation = os.path.join(path, "APY! Launcher/APY! Launcher.exe")
                shortcut.save()

            # end
            self.installed_path = os.path.join(path, "APY! Launcher/APY! Launcher.exe")
            self.reload_variable.set(4)

            installing = False


def show_step_1():
    step_1.show()


def show_step_2():
    step_2.show()


def show_step_3(check=True):
    if check:
        if os.path.isdir(os.path.join(step_2.explorer.get_path(), "APY!/APY! Launcher")) or os.path.isdir(os.path.join(step_2.explorer.get_path(), "APY! Launcher")):
            if askyesno("Path selection", "The app is already installed at the given path, do you want to replace it ?"):
                step_3.show()
        else:
            step_3.show()
    else:
        step_3.show()


def show_step_4():
    if [0 for widget in step_3.language_checkboxes_list if widget.get() == 1]:
        step_4.show()
    else:
        showwarning("Parameters", "You have to select at least one language to install")


def show_step_5():
    step_5.show()


# defining window
win = ctk.CTk()
win.geometry("400x500")
win.iconbitmap(get_resource_path("launcher data/launcher_icon.ico"))
win.title("APY! Launcher Installer")
win.resizable(False, False)
win.grid_columnconfigure(0, weight=1)
win.grid_columnconfigure(1, weight=1)
win.protocol("WM_DELETE_WINDOW", on_closing)

# defining ctk variables
subhead_font = ctk.CTkFont(size=20, weight="bold")
bold_font = ctk.CTkFont(size=13, weight="bold")

# global variables
installing = False

# checking installer version
versions = check_versions(["minversioninstaller", "launcher"])

# starting the installer
if versions == "connexion error":
    page = NotLaunchable("Connexion failed\n\nPlease check your connexion or try again later")
    page.show()
    win.mainloop()
elif versions["minversioninstaller"] == "unknown":
    page = NotLaunchable("There was an error retrieving the version of the installer\n\nPlease try again later")
    page.show()
    win.mainloop()
elif versions["minversioninstaller"] > _version:
    page = NotLaunchable("This installer is not up-to-date\n\nTo install the APY! launcher,\nplease download the last version of the installer")
    page.show()
    win.mainloop()
else:  # up-to-date
    step_1 = Step1()
    step_2 = Step2()
    step_3 = Step3()
    step_4 = Step4()
    step_5 = Step5()

    step_4.version_label.configure(text=f"Version to install: {versions["launcher"]}")
    step_1.show()
    win.mainloop()
