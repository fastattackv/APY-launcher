"""
This file contains the app to update the launcher

Copyright (C) 2024  fastattack

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

See the license in the COPYING file or at <https://www.gnu.org/licenses/>.
"""

import customtkinter as ctk
import os
import sys
import time
import threading
import requests
import shutil
import zipfile
import subprocess
import csv

from custom_ctk_toplevels import get_resource_path, showinfo, showwarning
from APY_launcher_updates import check_versions, get_file_version


_version = "2.0.0"


def on_closing():
    """ Handles the closing event """
    if installing:
        showwarning("Closing", "The launcher is currently being updated, closing is impossible\n(Please don't end the task in the task manager except you are sure it's stuck because it could corrupt the application)")
    else:
        win.destroy()


def is_path_a_launcher_path(path_to_check: str) -> bool:
    """ Checks if the given path is a correct path where a launcher is installed (checks if the given directory is "APY! Launcher" and if there is "APY! Launcher.exe" and "cache" in it) """
    if os.path.isfile(os.path.join(path_to_check, "APY! Launcher.exe")) and os.path.isdir(os.path.join(path_to_check, "cache")) and path_to_check.endswith("APY! Launcher"):
        return True
    else:
        return False


class APYUpdateLanguageInterpreter:
    """ Interpreter to execute the commands to update the launcher files using the APY Update Language. To work, the cwd should be set to the launcher folder and the zip file should be unzipped """
    def __init__(self):
        self.commands = {
            "replacefile": self.replacefile,
            "replacedir": self.replacedir,
            "createfile": self.createfile,
            "createdir": self.createdir,
            "deletefile": self.deletefile,
            "deletedir": self.deletedir,
            "update": self.update,
            "updatecsv": self.updatecsv
        }

    @staticmethod
    def parse_command(command: str) -> list[str]:
        """ Parses the given command and returns the list of arguments """
        in_quotation = False
        parsed_command = []
        current_argument = ""
        for char in command:
            if char == "\"":
                in_quotation = not in_quotation
            elif char == " " and not in_quotation:
                parsed_command.append(current_argument)
                current_argument = ""
            else:
                current_argument += char
        if current_argument != "":
            parsed_command.append(current_argument)
        return parsed_command

    def execute(self, command: str) -> bool:
        """ Executes the given command, returns False if there was an error, True otherwise """
        command = self.parse_command(command)
        if command[0] in self.commands:
            return self.commands[command[0]](command[1:])
        else:
            return False

    @staticmethod
    def replacefile(arguments: list[str]):
        if len(arguments) == 1:
            launcher_folder = os.path.abspath(os.getcwd())
            old_file = os.path.join(launcher_folder, arguments[0])
            new_file = os.path.join(launcher_folder, "cache/APY! Launcher", arguments[0])
            if os.path.isfile(new_file):  # the new file exists
                if os.path.isfile(old_file):  # there is a file to replace
                    os.remove(old_file)
                shutil.copy2(new_file, old_file)
            else:
                return False
        else:
            return False

    @staticmethod
    def replacedir(arguments: list[str]):
        if len(arguments) == 1:
            launcher_folder = os.path.abspath(os.getcwd())
            old_dir = os.path.join(launcher_folder, arguments[0])
            new_dir = os.path.join(launcher_folder, "cache/APY! Launcher", arguments[0])

            for file in os.listdir(old_dir):  # remove all files in old dir
                full_path = os.path.join(old_dir, file)
                if os.path.isfile(full_path):
                    os.remove(full_path)
                else:
                    shutil.rmtree(full_path)

            for file in os.listdir(new_dir):  # copy all new files
                src = os.path.join(new_dir, file)
                dst = os.path.join(old_dir, file)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                else:
                    shutil.copytree(src, dst)

            else:
                return False
        else:
            return False

    @staticmethod
    def createfile(arguments: list[str]):
        if len(arguments) == 1:
            path = os.path.join(os.path.abspath(os.getcwd()), arguments[0])
            if not os.path.isfile(path):
                with open(path, "x"):
                    pass
            return True
        else:
            return False

    @staticmethod
    def createdir(arguments: list[str]):
        if len(arguments) == 1:
            path = os.path.join(os.path.abspath(os.getcwd()), arguments[0])
            if not os.path.isdir(path):
                os.mkdir(path)
            return True
        else:
            return False

    @staticmethod
    def deletefile(arguments: list[str]):
        if len(arguments) == 1:
            path = os.path.join(os.path.abspath(os.getcwd()), arguments[0])
            if os.path.isfile(path):
                os.remove(path)
            return True
        else:
            return False

    @staticmethod
    def deletedir(arguments: list[str]):
        if len(arguments) == 1:
            path = os.path.join(os.path.abspath(os.getcwd()), arguments[0])
            if os.path.isdir(path):
                if os.listdir(path):  # not empty
                    shutil.rmtree(path)
                else:
                    os.rmdir(path)
            return True
        else:
            return False

    @staticmethod
    def update(arguments: list[str]):
        path = os.path.join(os.path.abspath(os.getcwd()), arguments[0])
        if os.path.isfile(path):

            if arguments[1] == "newline" and len(arguments) == 3:
                if arguments[2].isnumeric() or arguments[2] == "end":
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.readlines()
                    index = int(arguments[2]) if arguments[2].isnumeric() else len(content)
                    content.insert(index, "\n")
                    with open(path, "w", encoding="utf-8") as f:
                        f.writelines(content)
                    return True
                else:
                    return False

            elif arguments[1] == "deleteline" and len(arguments) == 4:
                if (arguments[2] == "index" and arguments[3].isnumeric()) or (arguments[2] == "start"):
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.readlines()
                    if arguments[2] == "index" and arguments[3].isnumeric():
                        index = int(arguments[3])
                    else:
                        for x in range(len(content)):
                            if content[x].startswith(arguments[3]):
                                index = x
                                break
                        else:
                            return False
                    content.pop(index)
                    with open(path, "w", encoding="utf-8") as f:
                        f.writelines(content)
                    return True
                else:
                    return False

            elif arguments[1] == "rewriteline" and len(arguments) == 5:
                if (arguments[2] == "index" and arguments[3].isnumeric() or arguments[2] == "index" and arguments[3] == "end") or arguments[2] == "start":
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.readlines()
                        print(content)
                    if arguments[2] == "index" and arguments[3].isnumeric():
                        index = int(arguments[3])
                    elif arguments[2] == "index" and arguments[3] == "end":
                        index = len(content) - 1
                    else:  # start
                        for x in range(len(content)):
                            if content[x].startswith(arguments[3]):
                                index = x
                                break
                        else:
                            return False
                    if arguments[3] == "end" and content[index] != "\n" and content[index].endswith("\n"):
                        content.append(arguments[4])
                    else:
                        content[index] = arguments[4] + "\n"
                    with open(path, "w", encoding="utf-8") as f:
                        f.writelines(content)
                    return True
                else:
                    return False

            elif arguments[1] == "modifyline" and len(arguments) == 7:
                if ((arguments[2] == "index" and arguments[3].isnumeric()) or arguments[2] == "start") and arguments[5].isnumeric():
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.readlines()
                    splitter_char = arguments[4]
                    if arguments[2] == "index" and arguments[3].isnumeric():
                        index = int(arguments[3])
                    else:
                        for x in range(len(content)):
                            if content[x].startswith(arguments[3]):
                                index = x
                                break
                        else:
                            return False
                    line = content[index]
                    line = line.split(splitter_char)
                    line[int(arguments[5])] = arguments[6]
                    line = splitter_char.join(line)
                    line += "\n"
                    content[index] = line
                    with open(path, "w", encoding="utf-8") as f:
                        f.writelines(content)
                    return True
                else:
                    return False

            else:
                return False
        else:
            return False

    @staticmethod
    def updatecsv(arguments: list[str]):
        if (len(arguments) == 4 and arguments[2] in ["add", "delete"]) or (len(arguments) == 5 and arguments[2] == "modify"):
            path = os.path.join(os.path.abspath(os.getcwd()), arguments[0])
            if os.path.isfile(path):
                if arguments[1] in ["game", "bonus", "config", "folder", "all"]:
                    if arguments[3].isnumeric() or arguments[3] == "end":

                        new_content = []
                        with open(path, "r", encoding="utf-8", newline="") as f:
                            reader = csv.reader(f, delimiter=",", quotechar='"', doublequote=True)
                            for line in reader:
                                if line[1] == arguments[1] or arguments[1] == "all":
                                    if arguments[2] == "add":
                                        index = int(arguments[3]) if arguments[3].isnumeric() else len(line)
                                        line.insert(index, "")
                                    elif arguments[2] == "delete":
                                        index = int(arguments[3]) if arguments[3].isnumeric() else len(line) - 1
                                        line.pop(index)
                                    else:  # modify
                                        index = int(arguments[3]) if arguments[3].isnumeric() else len(line) - 1
                                        line[index] = arguments[4]
                                    new_content.append(line)
                                else:
                                    new_content.append(line)
                        with open(path, "w", encoding="utf-8", newline="") as f:
                            writer = csv.writer(f, delimiter=",", quotechar='"')
                            writer.writerows(new_content)
                        return True

                    else:
                        return False
                else:
                    return False
            else:
                return False
        else:
            return False


def hide_all():
    step_1.hide()
    step_2.hide()


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
        self.title_label = ctk.CTkLabel(win, text="APY! launcher updater", font=subhead_font)
        self.version_label = ctk.CTkLabel(win, text=f"Updater version: {_version}\nCurrent launcher version: {launcher_version}\nLatest launcher version: {versions["launcher"]}\nUpdating from the {"development" if branch == "Development" else "stable"} branch")
        self.start_button = ctk.CTkButton(win, text="Start the update", command=show_step_2)

    def show(self):
        hide_all()
        self.version_label.configure(text=f"Updater version: {_version}\nCurrent launcher version: {launcher_version}\nLatest launcher version: {versions["launcher"]}\nUpdating from the {"development" if branch == "Development" else "stable"} branch")  # refresh the label
        self.title_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        self.version_label.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        self.start_button.grid(row=2, column=0, columnspan=2, padx=5, pady=100)

    def hide(self):
        self.title_label.grid_forget()
        self.version_label.grid_forget()
        self.start_button.grid_forget()


class Step2:
    """ Installation """
    def __init__(self):
        self.title_label = ctk.CTkLabel(win, text="Updating, please wait", font=bold_font)
        self.progress_bar = ctk.CTkProgressBar(win, width=300, height=15)
        self.progress_bar.set(0)
        self.current_process_label = ctk.CTkLabel(win, text="")
        self.reload_variable = ctk.IntVar(win, 0)  # variable to change widgets on the interface
        self.reload_variable.trace_add("write", self.reload)
        self._connexion_error = False
        self._other_error = False
        self._launcher_files_downloaded = False
        self._langage_files_downloaded = False
        self._AUL_commands_downloaded = False
        self._AUL_commands = None

    def show(self):
        hide_all()
        self.title_label.grid(row=0, column=0, columnspan=2, pady=30)
        self.progress_bar.grid(row=1, column=0, columnspan=2, pady=10)
        self.current_process_label.grid(row=2, column=0, columnspan=2)

    def hide(self):
        self.title_label.grid_forget()
        self.progress_bar.grid_forget()
        self.current_process_label.grid_forget()

    @staticmethod
    def start_launcher(path: str, arguments: list):
        """ Starts the launcher at the given path and stops the installer """
        subprocess.Popen([path] + arguments)
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
        elif var == 3:  # updating files
            self.progress_bar.set(0.8)
            self.current_process_label.configure(text="Updating launcher files")
        elif var == 4:  # deleting cache files
            self.progress_bar.set(0.9)
            self.current_process_label.configure(text="Deleting temporary files")
        elif var == 5:  # end
            self.progress_bar.set(1)
            self.current_process_label.configure(text="Done")
            self.title_label.configure(text="Update is done")
            ctk.CTkButton(win, text="Start the launcher", command=lambda a=os.path.join(path, "APY! Launcher.exe"): self.start_launcher(a, [f"updatedfrom={launcher_version}"])).grid(row=3, column=0, pady=10, padx=10)
            ctk.CTkButton(win, text="Exit", command=win.destroy).grid(row=3, column=1, pady=10, padx=10)
        elif var == 6:  # connexion error
            self.current_process_label.configure(text="Check your connexion or try again later")
            self.title_label.configure(text="Update stopped: connexion error")
            ctk.CTkButton(win, text="Exit", command=win.destroy).grid(row=3, column=1, pady=50, padx=10)
        elif var == 7:  # error
            self.current_process_label.configure(text="An error occurred")
            self.title_label.configure(text="Update stopped: an error occurred when updating")
            ctk.CTkButton(win, text="Exit", command=win.destroy).grid(row=3, column=1, pady=50, padx=10)

    def _download_launcher_files(self):
        """ Downloads the launcher zip and writes it to the cache folder """
        global installing
        try:
            # APY! Launcher.zip
            response = requests.get(f"https://github.com/fastattackv/APY-launcher/raw/{branch}/Downloads/APY!%20Launcher.zip", timeout=(5, 10))
            if response.status_code == 200:
                with open(os.path.join(path, "cache/APY! Launcher.zip"), "wb") as f:
                    f.write(response.content)
            else:
                self.reload_variable.set(7)
                self._other_error = True
                return
        except requests.ConnectionError:
            self.reload_variable.set(6)
            self._connexion_error = True
        except requests.Timeout:
            self.reload_variable.set(6)
            self._connexion_error = True
        except:
            self.reload_variable.set(7)
            self._other_error = True
        else:
            self._launcher_files_downloaded = True

    def _download_language_files(self, languages: list[str]):
        """ Downloads the languages files needed and writes them to the cache folder """
        global installing
        try:
            for file in languages:
                response = requests.get(f"https://github.com/fastattackv/APY-launcher/raw/{branch}/Downloads/Languages/{file}", timeout=(5, 10))
                if response.status_code == 200:
                    with open(os.path.join(path, f"cache/{file}"), "wb") as f:
                        f.write(response.content)
                else:
                    self.reload_variable.set(7)
                    self._other_error = True
                    return
        except requests.ConnectionError:
            self.reload_variable.set(6)
            self._connexion_error = True
        except requests.Timeout:
            self.reload_variable.set(6)
            self._connexion_error = True
        except:
            self.reload_variable.set(7)
            self._other_error = True
        else:
            self._langage_files_downloaded = True

    def _get_update_commands_list(self, initial_version: str, current_version: str):
        """Returns the update commands for the versions between the given initial_version and the given current_version

        :param initial_version: version of the launcher before update
        :param current_version: current version of the launcher
        :return: list of the commands to update the files to the current version or None if there was an error (connexion failed...)
        """
        global installing
        try:
            # changed files
            versions_list = requests.get(f"https://github.com/fastattackv/APY-launcher/raw/{branch}/Downloads/Versions%20list.txt", timeout=(5, 10))
            if versions_list.status_code == 200:
                versions_list = versions_list.text.split("\n")
                versions_to_update = [version for version in versions_list if initial_version < version <= current_version]
                commands = []
                for version in versions_to_update:
                    response = requests.get(f"https://github.com/fastattackv/APY-launcher/raw/{branch}/Downloads/AUL%20commands/{version}.AUL", timeout=(5, 10))
                    if response.status_code == 200:
                        commands.extend(response.text.split("\n"))
                    else:
                        self.reload_variable.set(7)
                        self._other_error = True
                        return
            else:
                self.reload_variable.set(7)
                self._other_error = True
                return
        except requests.ConnectionError:
            self.reload_variable.set(6)
            self._connexion_error = True
        except requests.Timeout:
            self.reload_variable.set(6)
            self._connexion_error = True
        except:
            self.reload_variable.set(7)
            self._other_error = True
        else:
            self._AUL_commands = commands
            self._AUL_commands_downloaded = True

    def update(self):
        thread = threading.Thread(target=self._update, name="updater: updating launcher")
        thread.start()

    def _update(self):
        global installing
        installing = True

        self.reload_variable.set(1)  # download
        languages_to_download = [file for file in os.listdir("lng files") if os.path.isfile(os.path.join("lng files", file)) and file.endswith(".lng")]
        threading.Thread(target=self._download_launcher_files, name="updater: downloading launcher files").start()
        threading.Thread(target=self._download_language_files, args=[languages_to_download], name="updater: downloading language files").start()
        threading.Thread(target=self._get_update_commands_list, args=[launcher_version, versions["launcher"]], name="updater: downloading AUL commands").start()
        while (not self._launcher_files_downloaded or not self._langage_files_downloaded or not self._AUL_commands_downloaded) and (not self._connexion_error or not self._other_error):  # wait until all downloads are complete
            time.sleep(0.1)
        if self._connexion_error or self._other_error:  # stop installation if there is an error
            installing = False

        else:  # no errors
            self.reload_variable.set(2)  # unzip
            with zipfile.ZipFile(os.path.join(path, "cache/APY! Launcher.zip"), "r") as f:
                f.extractall(os.path.join(path, "cache"))

            self.reload_variable.set(3)  # updating launcher files
            # AUL commands
            interpreter = APYUpdateLanguageInterpreter()
            if self._AUL_commands is not None:
                for command in self._AUL_commands:
                    resp = interpreter.execute(command)
                    if not resp:  # an error occurred
                        self.reload_variable.set(7)
                        installing = False
            else:
                self.reload_variable.set(7)
                installing = False
            # replace old language files
            for file in languages_to_download:
                if os.path.isfile(os.path.join("cache", file)):
                    if os.path.isfile(f"lng files/{file}"):  # remove previous lng file
                        os.remove(f"lng files/{file}")
                    shutil.copy2(f"cache/{file}", f"lng files/{file}")

            self.reload_variable.set(4)  # deleting cache files
            for filename in os.listdir("cache"):
                file_path = os.path.join("cache", filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except:
                    self.reload_variable.set(7)
                    installing = False
                    break

            else:  # no errors while deleting cache files
                self.reload_variable.set(5)  # end
                installing = False


def show_step_1():
    global launcher_version
    if is_path_a_launcher_path(path):
        launcher_version = get_file_version(os.path.join(path, "APY! Launcher.exe"))
        if launcher_version < github_version:
            step_1.show()
        else:
            showinfo("APY! Launcher Updater", f"The launcher is up-to-date: {launcher_version}")
            exit()

    else:
        showwarning("APY! Launcher Updater", f"The updater is not placed in a directory containing an APY! Launcher installation: cannot start the update\n\nCurrent path of the updater:\n{path}")
        exit()


def show_step_2():
    step_2.show()
    step_2.update()


# defining window
win = ctk.CTk()
win.geometry("400x250")
win.iconbitmap(get_resource_path("launcher data/launcher_icon.ico"))
win.title("APY! Launcher Updater")
win.resizable(False, False)
win.grid_columnconfigure(0, weight=1)
win.grid_columnconfigure(1, weight=1)
win.protocol("WM_DELETE_WINDOW", on_closing)

# defining ctk variables
subhead_font = ctk.CTkFont(size=19, weight="bold")
bold_font = ctk.CTkFont(size=13, weight="bold")

# checking branch to update from
if len(sys.argv) > 1:
    if sys.argv[1] == "branch=main":
        branch = "main"
    elif sys.argv[1] == "branch=Development":
        branch = "Development"
    else:
        raise Exception(f"The given argument to specify what branch to update from is invalid: {sys.argv[1]}")
else:  # no argument
    if os.path.isfile("params.APYL"):
        with open("params.APYL", "r", encoding="utf-8") as f:
            for line in f.readlines():
                line = line.removesuffix("\n")
                if line.startswith("branch="):
                    branch = line.split("=", 1)[1]
                    if branch not in ("main", "Development"):
                        raise Exception(f"The branch to update from in params.APYL is invalid: {branch}")
                    else:
                        break
            else:
                raise Exception("Did not find a branch parameter in the params.APYL file")
    else:
        raise Exception("Did not find a params.APYL file to get the branch to update from")

installing = False
versions = check_versions(["minversionupdater", "launcher"], branch)

# starting the installer
if versions == "connexion error":
    page = NotLaunchable("Connexion failed\n\nPlease check your connexion or try again later")
    page.show()
    win.mainloop()
elif "unknown" in versions.values():
    page = NotLaunchable("There was an error retrieving the version of the installer\n\nPlease try again later")
    page.show()
    win.mainloop()
elif versions["minversionupdater"] > _version:
    page = NotLaunchable("This installer is not up-to-date\n\nTo update the APY! launcher,\nplease download the last version of the updater")
    page.show()
    win.mainloop()
else:  # updater is up-to-date
    path = os.getcwd()
    launcher_version = ""
    github_version = versions["launcher"]  # launcher version to download

    step_1 = Step1()
    step_2 = Step2()

    show_step_1()
    win.mainloop()
