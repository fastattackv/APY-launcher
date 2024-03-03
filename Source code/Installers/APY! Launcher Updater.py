"""
This file contains the app to update the launcher
"""

import customtkinter as ctk
import os
import threading
import requests
import shutil
import zipfile
import win32com.client

from custom_ctk_toplevels import get_resource_path, askdir, showwarning
from APY_launcher_updates import check_versions


_version = "1.0.0"


def on_closing():
    """ Handles the closing event """
    if installing:
        showwarning("Closing", "The launcher is currently being updated, closing is impossible\n(Please don't end the task in the task manager except you are sure it's stuck because it can corrupt the application)")
    else:
        win.destroy()


def get_file_version(path):
    """ Returns the version of the given file """
    information_parser = win32com.client.Dispatch("Scripting.FileSystemObject")
    version = information_parser.GetFileVersion(path)
    return version


def is_path_a_launcher_path(path_to_check: str) -> bool:
    """ Checks if the given path is a correct path where the launcher is installed (checks if the given directory is "APY! Launcher" and if there is "APY! Launcher.exe" and "cache" in it) """
    if os.path.isfile(os.path.join(path_to_check, "APY! Launcher.exe")) and os.path.isdir(os.path.join(path_to_check, "cache")) and path_to_check.endswith("APY! Launcher"):
        return True
    else:
        return False


def hide_all():
    step_1.hide()
    step_2.hide()
    step_3.hide()
    step_4.hide()
    launcher_up_to_date.hide()


class NotLaunchable:
    """ Not launchable installer page """
    def __init__(self, text: str):
        self.title_label = ctk.CTkLabel(win, text=text)
        self.stop_button = ctk.CTkButton(win, text="Exit", command=win.destroy)

    def show(self):
        self.title_label.grid(row=0, column=0, columnspan=2, pady=5)
        self.stop_button.grid(row=1, column=0, columnspan=2, pady=30)


class LauncherUpToDate:
    """ Launcher up-to-date page """
    def __init__(self):
        self.title_label = ctk.CTkLabel(win, text="The selected launcher instance is up-to-date", font=bold_font)
        self.back_button = ctk.CTkButton(win, text="Back", command=show_step_2)
        self.stop_button = ctk.CTkButton(win, text="Exit", command=win.destroy)

    def show(self):
        hide_all()
        self.title_label.grid(row=0, column=0, columnspan=2, pady=5)
        self.back_button.grid(row=1, column=0, pady=30)
        self.stop_button.grid(row=1, column=1, pady=30)

    def hide(self):
        self.title_label.grid_forget()
        self.back_button.grid_forget()
        self.stop_button.grid_forget()


class Step1:
    """ Start """
    def __init__(self):
        self.title_label = ctk.CTkLabel(win, text="Welcome to the APY! launcher updater", font=subhead_font)
        self.version_label = ctk.CTkLabel(win, text=f"Updater version: {_version}")
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
    """ Confirming path """
    def __init__(self):
        self.title_label = ctk.CTkLabel(win, text="Is the path below the correct path to update ?", font=bold_font)
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
        path = askdir("Select the path to the launcher to update")
        if path is not None:  # not cancelled
            if is_path_a_launcher_path(path):
                self.path_label.configure(text=path)
            else:
                showwarning("Selecting path", "The selected path does not contain a launcher installation")


class Step3:
    """ Confirming update """
    def __init__(self):
        self.title = ctk.CTkLabel(win, text="Confirming update", font=bold_font)

        self.path_title_label = ctk.CTkLabel(win, text="Installation path to update:")
        self.path_frame = ctk.CTkScrollableFrame(win, orientation="horizontal", width=350, height=30)
        self.path_label = ctk.CTkLabel(self.path_frame, text="")
        self.path_label.pack()

        self.version_label = ctk.CTkLabel(win, text="")

        self.back_button = ctk.CTkButton(win, text="Back", command=show_step_2)
        self.next_button = ctk.CTkButton(win, text="Ok", command=show_step_4)

    def show(self):
        hide_all()
        self.title.grid(row=0, column=0, columnspan=2, pady=5)
        self.path_label.configure(text=path)
        self.path_title_label.grid(row=1, column=0, columnspan=2, pady=15)
        self.path_frame.grid(row=2, column=0, columnspan=2)
        self.version_label.configure(text=f"Updating from {launcher_version} to {github_version}")
        self.version_label.grid(row=3, column=0, columnspan=2, pady=20)
        self.next_button.grid(row=4, column=0, pady=5)
        self.back_button.grid(row=4, column=1, pady=5)

    def hide(self):
        self.title.grid_forget()
        self.path_title_label.grid_forget()
        self.path_frame.grid_forget()
        self.version_label.grid_forget()
        self.next_button.grid_forget()
        self.back_button.grid_forget()


class Step4:
    """ Installation """
    def __init__(self):
        self.title_label = ctk.CTkLabel(win, text="Updating, please wait", font=bold_font)
        self.progress_bar = ctk.CTkProgressBar(win, width=300, height=15)
        self.progress_bar.set(0)
        self.current_process_label = ctk.CTkLabel(win, text="")
        self.reload_variable = ctk.IntVar(win, 0)  # variable to change widgets on the interface
        self.reload_variable.trace_add("write", self.reload)

    def show(self):
        hide_all()
        self.title_label.grid(row=0, column=0, columnspan=2, pady=30)
        self.progress_bar.grid(row=1, column=0, columnspan=2, pady=10)
        self.current_process_label.grid(row=2, column=0, columnspan=2)
        self.update()

    def hide(self):
        self.title_label.grid_forget()
        self.progress_bar.grid_forget()
        self.current_process_label.grid_forget()

    @staticmethod
    def start_launcher(path: str):
        """ Starts the launcher at the given path and stops the installer """
        os.startfile(path)
        win.destroy()

    def reload(self, *args):
        """ Reloads the interface with the widgets corresponding to the value of self.reload_variable """
        var = self.reload_variable.get()
        if var == 0:  # base widgets
            self.progress_bar.set(0)
            self.current_process_label.configure(text="")
        elif var == 1:  # downloading
            self.progress_bar.set(0)
            self.current_process_label.configure(text="Downloading files")
        elif var == 2:  # unzip
            self.progress_bar.set(0.6)
            self.current_process_label.configure(text="Preparing files")
        elif var == 3:  # replacing old files
            self.progress_bar.set(0.7)
            self.current_process_label.configure(text="Replacing old files")
        elif var == 4:  # deleting cache files
            self.progress_bar.set(0.9)
            self.current_process_label.configure(text="Deleting temporary files")
        elif var == 5:  # end
            self.progress_bar.set(1)
            self.current_process_label.configure(text="Done")
            self.title_label.configure(text="Update is done")
            ctk.CTkButton(win, text="Start the launcher", command=lambda a=os.path.join(path, "APY! Launcher.exe"): self.start_launcher(a)).grid(row=3, column=0, pady=10, padx=10)
            ctk.CTkButton(win, text="Exit", command=win.destroy).grid(row=3, column=1, pady=10, padx=10)
        elif var == 6:  # connexion error
            self.current_process_label.configure(text="Check your connexion or try again later")
            self.title_label.configure(text="Update stopped: connexion error")
            ctk.CTkButton(win, text="Exit", command=win.destroy).grid(row=3, column=1, pady=50, padx=10)

    def update(self):
        thread = threading.Thread(target=self._update, name="updater: updating launcher")
        thread.start()

    def _update(self):
        global installing
        installing = True

        self.reload_variable.set(1)  # download
        try:
            # changed files
            response = requests.get("https://github.com/fastattackv/APY-launcher/raw/main/Downloads/Changed%20files.txt")
            changed_files = []
            for line in response.text.split("\n"):
                line = line.split("=")
                if line[0] > launcher_version:
                    for file in line[1].split(","):
                        if file not in changed_files:
                            changed_files.append(file)
            # APY! Launcher.zip
            response = requests.get("https://github.com/fastattackv/APY-launcher/raw/main/Downloads/APY!%20Launcher.zip")
            with open(os.path.join(path, "cache/APY! Launcher.zip"), "wb") as f:
                f.write(response.content)
        except requests.ConnectionError:
            self.reload_variable.set(6)
            installing = False
        except requests.Timeout:
            self.reload_variable.set(6)
            installing = False
        else:  # download went well

            self.reload_variable.set(2)  # unzip
            with zipfile.ZipFile(os.path.join(path, "cache/APY! Launcher.zip"), "r") as f:
                f.extractall(os.path.join(path, "cache"))

            self.reload_variable.set(3)  # replace old files
            for file in changed_files:
                if "." in file:  # file
                    shutil.copy2(os.path.join(path, "cache/APY! Launcher", file), os.path.join(path, file))
                else:  # directory
                    shutil.rmtree(os.path.join(path, file))
                    shutil.copytree(os.path.join(path, "cache/APY! Launcher", file), os.path.join(path, file))

            self.reload_variable.set(4)  # deleting cache files
            os.remove(os.path.join(path, "cache/APY! Launcher.zip"))
            shutil.rmtree(os.path.join(path, "cache/APY! Launcher"))

            self.reload_variable.set(5)  # end
            installing = False


def show_step_1():
    step_1.show()


def show_step_2():
    global path
    if not is_path_a_launcher_path(path):
        path = askdir("Select the path of the launcher to update", allow_cancel=False)
        while True:
            if path is None:  # cancelled
                path = os.getcwd()
                break
            elif not is_path_a_launcher_path(path):
                showwarning("Selecting path", "The selected path does not contain a launcher installation")
                path = askdir("Select the path of the launcher to update", allow_cancel=False)
            else:  # valid path
                step_2.show()
                break
    else:
        step_2.show()


def show_step_3():
    global launcher_version
    launcher_version = get_file_version(os.path.join(path, "APY! Launcher.exe"))
    if launcher_version < github_version:
        step_3.show()
    else:
        launcher_up_to_date.show()


def show_step_4():
    step_4.show()


# defining window
win = ctk.CTk()
win.geometry("400x500")
win.iconbitmap(get_resource_path("launcher data/launcher_icon.ico"))
win.title("APY! Launcher Updater")
win.resizable(False, False)
win.grid_columnconfigure(0, weight=1)
win.grid_columnconfigure(1, weight=1)
win.protocol("WM_DELETE_WINDOW", on_closing)

# defining ctk variables
subhead_font = ctk.CTkFont(size=19, weight="bold")
bold_font = ctk.CTkFont(size=13, weight="bold")

installing = False
versions = check_versions(["minversionupdater", "launcher"])

# starting the installer
if versions == "connexion error":
    page = NotLaunchable("Connexion failed\n\nPlease check your connexion or try again later")
    page.show()
    win.mainloop()
elif versions["minversionupdater"] == "unknown":
    page = NotLaunchable("There was an error retrieving the version of the installer\n\nPlease try again later")
    page.show()
    win.mainloop()
elif versions["minversionupdater"] > _version:
    page = NotLaunchable("This installer is not up-to-date\n\nTo install the APY! launcher,\nplease download the last version of the installer")
    page.show()
    win.mainloop()
else:  # up-to-date
    path = os.getcwd()
    launcher_version = ""
    github_version = versions["launcher"]  # launcher version to download

    step_1 = Step1()
    step_2 = Step2()
    step_3 = Step3()
    step_4 = Step4()
    launcher_up_to_date = LauncherUpToDate()

    step_1.show()
    win.mainloop()
