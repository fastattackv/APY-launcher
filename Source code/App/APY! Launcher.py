"""
Main file for the APY! Launcher. Generates the window and loads other files.

Copyright (C) 2024  fastattack

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Contact: Discord server: https://discord.gg/pHPkkpXhUV
"""

import customtkinter as ctk
from tkinter import Menu
import os
import shutil
import sys
import datetime
import csv
from PIL import Image, UnidentifiedImageError
import win32com.client
import threading
import random

import get_icons as gi
import custom_ctk_toplevels as tl
import APY_launcher_updates as up
import game_detector as gd


# global variables
_log = True  # write errors to log file, should be set to True when converting to .exe
_debug = False  # print errors, should be set to False when converting to .exe
_version = "2.1.0"
_language_separators_indexes = [0, 7, 18, 72, 104, 121, 150, 167]
installing = False  # set to True when the launcher is updating itself and should not be closed


# custom errors
class APYLauncherExceptions:
    class ParamMissing(Exception):
        def __init__(self, param):
            message = f"Parameter {param} is missing from the params file (Err301)"
            super().__init__(message)

    class LngFileMissing(Exception):
        def __init__(self):
            message = "Did not found any valid language file to load (Err302)"
            super().__init__(message)


# Global functions
def log_error(error_code: int, message=""):
    """Logs errors in the log file / print the errors

    :param error_code: error code
    :param message: optional : message to write with the error code
    """
    if _log:
        if not os.path.isfile("APY launcher logs.log"):
            with open("APY launcher logs.log", "x"):
                pass
        with open("APY launcher logs.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now()} : Err{error_code}, {message}\n")
    if _debug:
        print(f"{datetime.datetime.now()} : Err{error_code}, {message}")


def read_params(path="params.APYL") -> dict[str, str | int | list]:
    """Reads the params in the given file, !doesn't check if the file exists!

    :param path: optional : path of the file to read, by default = "params.APYL"
    :return: dict containing the parameters
    """
    with open(path, "r", encoding="utf-8") as f:
        params = {}
        for line in f.readlines():
            line = line.removesuffix("\n")
            if line != "":
                if line.startswith("language="):
                    params["language"] = line.split("=", 1)[1]
                elif line.startswith("appearance="):
                    params["appearance"] = line.split("=", 1)[1]
                elif line.startswith("size="):
                    params["size"] = line.split("=", 1)[1]
                elif line.startswith("defaultfilter="):
                    a = line.split("=", 1)[1]
                    if a.isnumeric():
                        a = int(a)
                        if 0 <= a <= 6:
                            params["defaultfilter"] = a
                        else:
                            params["defaultfilter"] = 0
                            log_error(107, f"The entered value for the parameter defaultfilter is incorrect: {a}")
                    else:
                        params["defaultfilter"] = 0
                        log_error(107, f"The entered value for the parameter defaultfilter is incorrect: {a}")
                elif line.startswith("stoplauncherwhengame="):
                    value = line.split("=", 1)[1]
                    if value == "0":
                        params["stoplauncherwhengame"] = False
                    elif value == "1":
                        params["stoplauncherwhengame"] = True
                    else:
                        params["stoplauncherwhengame"] = False
                        log_error(108, f"The entered value for stoplauncherwhengame is incorrect: {value}")
                elif line.startswith("lastgame="):
                    params["lastgame"] = line.split("=", 1)[1]
                elif line.startswith("ignoredmessages="):
                    values = line.split("=", 1)[1].split(",")
                    final_values = []
                    for value in values:
                        if value == "":
                            continue
                        elif value.isnumeric():
                            final_values.append(int(value))
                        else:
                            log_error(115, f"The entered value for the parameter ignoredmessages is incorrect: \"{value}\"")
                    params["ignoredmessages"] = final_values
                elif line.startswith("branch="):
                    value = line.split("=", 1)[1]
                    if value in ("main", "Development"):
                        params["branch"] = value
                    else:
                        log_error(208, f"The branch parameter in the params.APYL file is invalid: \"{value}\"")
                else:
                    log_error(201, f"params file line unknown : \"{line}\"")
        for param in ["language", "appearance", "size", "defaultfilter", "stoplauncherwhengame", "lastgame", "ignoredmessages", "branch"]:
            if param not in params:
                log_error(301, f"param {param} is missing")
                raise APYLauncherExceptions.ParamMissing(param)
    return params


def write_params(params_dict: dict[str, str | int], path="params.APYL"):
    """Writes the params in the given dictionary in the given file

    :param params_dict: params to write
    :param path: optional : path of the file to write to
    """
    to_write = ""
    for param in params_dict:
        if type(params_dict[param]) is bool:
            if params_dict[param]:
                to_write += f"{param}=1\n"
            else:
                to_write += f"{param}=0\n"
        elif type(params_dict[param]) is list:
            to_write += f"{param}={",".join(map(str, params_dict[param]))}\n"
        else:
            to_write += f"{param}={params_dict[param]}\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(to_write)


def is_lng_file_valid(path: str) -> bool:
    """Verifies if the given lng file is valid

    :param path: path of the file to verify
    :return: True if the file is valid, else : False
    """
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for value, index in [
                            ("WINDOW:\n", _language_separators_indexes[0]),
                            ("HOME:\n", _language_separators_indexes[1]),
                            ("APPS:\n", _language_separators_indexes[2]),
                            ("ADD:\n", _language_separators_indexes[3]),
                            ("UPDATES:\n", _language_separators_indexes[4]),
                            ("OPTIONS:\n", _language_separators_indexes[5]),
                            ("DIALOGS:\n", _language_separators_indexes[6])]:
            if value not in lines or lines.count(value) != 1 or lines.index(value) != index:
                return False
        return True


def load_language(lang: str) -> dict[str, list[str]]:
    """Loads the given language

    :param lang: language to load (file name without the .lng)
    :return: dict containing the loaded language
    """
    if os.path.exists(f"lng files/{lang}.lng"):
        if is_lng_file_valid(f"lng files/{lang}.lng"):
            language_dict = {"WINDOW": [], "HOME": [], "APPS": [], "ADD": [], "UPDATES": [], "OPTIONS": [], "DIALOGS": []}
            with open(f"lng files/{lang}.lng", "r", encoding="utf8") as f:
                lines = f.readlines()
                for index in range(len(lines)):
                    line = lines[index].removesuffix("\n")
                    if _language_separators_indexes[0] < index < _language_separators_indexes[1]:
                        language_dict["WINDOW"].append(line)
                    elif _language_separators_indexes[1] < index < _language_separators_indexes[2]:
                        language_dict["HOME"].append(line)
                    elif _language_separators_indexes[2] < index < _language_separators_indexes[3]:
                        language_dict["APPS"].append(line)
                    elif _language_separators_indexes[3] < index < _language_separators_indexes[4]:
                        language_dict["ADD"].append(line)
                    elif _language_separators_indexes[4] < index < _language_separators_indexes[5]:
                        language_dict["UPDATES"].append(line)
                    elif _language_separators_indexes[5] < index < _language_separators_indexes[6]:
                        language_dict["OPTIONS"].append(line)
                    elif _language_separators_indexes[6] < index < _language_separators_indexes[7]:
                        language_dict["DIALOGS"].append(line)
            return language_dict
        else:
            log_error(111, f"The given language file: {lang}.lng is not valid, searching for another file")
    else:
        log_error(102, f"Could not find file {lang}.lng, searching for another file")

    # is only executed if the first language file was not loadable
    for file in os.listdir("lng files"):
        if file.endswith(".lng"):
            if is_lng_file_valid(f"lng files/{file}"):
                return load_language(file.removesuffix(".lng"))
    else:
        log_error(302, "Not found any valid lng files to load")
        raise APYLauncherExceptions.LngFileMissing()


def read_csv(path: str) -> dict[str, list]:
    """Reads the given file and returns the dict containing the apps infos, !doesn't check if the file exists!

    :param path: path of the file to read, the file must be a .csv file
    :return: dict containing the apps infos
    """
    to_return = {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter=",", quotechar='"', doublequote=True)
        for row in reader:
            if row[1] == "game" or row[1] == "bonus":
                to_return[row[0]] = row[1:]
            elif row[1] == "config":
                to_return[row[0]] = [row[1], row[2], row[3], row[4], row[5:]]
            elif row[1] == "folder":
                to_return[row[0]] = [row[1], row[2], row[3]]
            else:
                log_error(205, f"The type of the app is unknown: {row[1]}")
    return to_return


def write_csv(to_save: dict, path: str):
    """Saves the given apps dictionary to the given file

    :param to_save: dict containing the infos to write to the file
    :param path: path of the file to write to
    """
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=",", quotechar='"')
        for app, infos in to_save.items():
            if infos[0] == "game" or infos[0] == "bonus":
                to_write = infos.copy()
                to_write.insert(0, app)
            elif infos[0] == "config":
                to_write = [app, infos[0], infos[1], infos[2], infos[3]]
                to_write.extend(infos[4])
            elif infos[0] == "folder":
                to_write = [app, infos[0], infos[1], infos[2]]
            writer.writerow(to_write)


def launch(game, change_last_game=True):
    """Launches the given game

    :param game: game to execute
    :param change_last_game: if set to True, the param "lastgame" will be changed to the given game
    """
    if os.path.isfile(os.path.abspath(apps[game][3])):
        os.startfile(os.path.abspath(apps[game][3]))
        if change_last_game:
            params["lastgame"] = game
            home_tab.reload()
            write_params(params)
        if params["stoplauncherwhengame"]:
            on_closing()
    else:
        log_error(104, f"path {apps[game][3]} does not exist")
        tl.showwarning(language["APPS"][7], language["APPS"][8])


def insert_in_dict(dict_to_insert: dict, index: int, item: tuple) -> dict:
    """Inserts the given element at the given index in the given dict

    :param dict_to_insert: dict to insert the item
    :param index: index to insert the item at
    :param item: item to insert
    :return: dict with the inserted item
    """
    if index > len(dict_to_insert):
        raise ValueError(f"The given index is out of range: {index}")
    elif index == len(dict_to_insert):
        temp_dict = dict_to_insert.copy()
        temp_dict[item[0]] = item[1]
        return temp_dict
    else:
        temp_dict = {}
        x = 0
        for a in dict_to_insert.items():
            if x == index:
                temp_dict[item[0]] = item[1]
            temp_dict[a[0]] = a[1]
            x += 1
        return temp_dict


def rename_in_dict(dict_to_rename: dict, key, new_key) -> dict:
    """Renames one of the element of the given dict

    :param dict_to_rename: dict containing the item to rename
    :param key: previous key to rename
    :param new_key: new key to rename the previous one to
    :return: dict with the old key replaced by the new one
    """
    if key in dict_to_rename:
        new_dict = {}
        for item in dict_to_rename:
            if item == key:
                new_dict[new_key] = dict_to_rename[key]
            else:
                new_dict[item] = dict_to_rename[item]
        return new_dict
    else:
        raise KeyError(f"The given key is not in the dictionnary: {key}")


def rewrite_on_x_chrs(text: str, chars: int):
    """Inserts line breaks in the given text

    :param text: text to insert line breaks into
    :param chars: number of characters between each line breaks
    :return: text with inserted line breaks
    """
    final_text = ""
    while len(text) > chars:
        final_text += text[0:chars] + "\n"
        text = text[chars:]
    final_text += text
    return final_text


def cut_after_x_chrs(text: str, chars: int):
    """Cuts the text after the given number of chars and inserts "..." at the end of the text (the full length of the returned text is chars or less)

    :param text: text to cut
    :param chars: number of characters after which the text is cut
    :return: cut text
    """
    if len(text) > chars:
        return text[:chars-3] + "..."
    else:
        return text


def check_name(name: str) -> bool:
    """Checks if the given name doesn't contain any forbidden characters

    :param name: name to check
    :return: True if the name is valid, else: False
    """
    if "\\" in name or "/" in name or ":" in name or "*" in name or "?" in name or "\"" in name or "<" in name or ">" in name or "|" in name:
        return False
    else:
        return True


def get_apps_in_folder(folder: str) -> list[str]:
    """Get the apps in the given folder

    :param folder: folder to check in (should exist in the apps dict)
    :return: list of the apps contained in the folder
    """
    if folder in apps:  # folder exists
        return [app for app in apps if apps[app][2] == folder]
    else:
        return []


def delete_usages_of_app(app_to_remove: str):
    """Deletes the usages of an app in the apps dict (removes the app from configs)

    :param app_to_remove: app to remove
    """
    modified = False
    for app in list(apps.keys()):
        if apps[app][0] == "config":
            if app_to_remove in apps[app][4]:
                modified = True
                apps[app][4].remove(app_to_remove)
                if not apps[app][4]:  # config is now empty
                    del apps[app]
    if modified:
        write_csv(apps, "apps.csv")


def get_directories_tree() -> dict | None:
    """Returns the tree of the launcher directories in the form of dicts in dicts in dicts ... Do not call it excessively because it is slow if there are many directories

    :return: directories tree, None if the tree couldn't be created: this means that a directory has a parent that does not exist
    """
    tree = {}
    paths_dict = {}  # temporary dict to get the path of any given directory
    parent_not_created_yet = []
    for app in list(apps.keys()):
        if apps[app][0] == "folder":
            if apps[app][2] == ".":
                tree[app] = {}
                paths_dict[app] = []
            else:  # not in the root folder
                if apps[app][2] in paths_dict:  # parent already created
                    content = tree
                    for path_item in paths_dict[apps[app][2]]:
                        content = content[path_item]
                    content[app] = {}
                    paths_dict[app] = paths_dict[apps[app][2]] + [apps[app][2]]
                else:
                    parent_not_created_yet.append(app)

    last_len = len(parent_not_created_yet)
    while True:
        for app in parent_not_created_yet:
            if apps[app][2] in paths_dict:  # parent has been created
                content = tree
                for path_item in paths_dict[apps[app][2]]:
                    content = content[path_item]
                content[app] = {}
                paths_dict[app] = paths_dict[apps[app][2]] + [apps[app][2]]
                parent_not_created_yet.remove(app)
        if not parent_not_created_yet:  # list empty
            break
        elif last_len > len(parent_not_created_yet):
            last_len = len(parent_not_created_yet)
        else:  # at least one directory parent does not exist
            log_error(207, f"A directory has a parent that does not exist: {parent_not_created_yet}")
            return None

    return tree


def find_uses_in_config(app_to_find: str) -> list[str]:
    """Returns a list of the configs using the given app

    :param app_to_find: app to check for
    :return: list of the configs using the app
    """
    uses = []
    for app in apps:
        if apps[app][0] == "config":
            if app_to_find in apps[app][4]:
                uses.append(app)
    return uses


# ctk functions
def hide_all():
    """ Hides all the tabs """
    home_tab.hide()
    apps_tab.hide()
    single_app_tab.hide()
    add_game_tab.hide()
    updates_tab.hide()
    options_tab.hide()


def on_closing():
    """ Is called when the close button is pressed (or when alt+F4 is pressed). Returns True if the launcher is being closed """
    if not installing:
        win.destroy()
        return True
    else:
        tl.showwarning(language["UPDATES"][0], language["UPDATES"][13])
        return False


def show_message(message: str, time: int):
    """Shows a message at the top of the windows for the given time

    :param message: message to show
    :param time: time to display the message (in ms)
    """
    show_message_label.configure(text=message)
    show_message_label.after(time, show_message_label.grid_forget)
    show_message_label.grid(column=1, row=0, padx=10)


def reload_window(tab: str):
    """Deletes every widget and recreates them (allows to change language)

    :param tab: tab to change to after reload is done
    """
    home_tab.reload_page()
    apps_tab.reload_page()
    single_app_tab.reload_page()
    add_game_tab.reload_page()
    updates_tab.reload_page()
    options_tab.reload_page()

    tabs.configure(values=[language["WINDOW"][1], language["WINDOW"][2], language["WINDOW"][3], language["WINDOW"][4], language["WINDOW"][5]])
    tabs.set(tab)
    change_tab(tab)


def change_tab(tab):
    """Changes the active tab to the given one

    :param tab: new tab to change to
    """
    if tab == language["WINDOW"][1]:
        home_tab.show()
    elif tab == language["WINDOW"][2]:
        apps_tab.show()
    elif tab == language["WINDOW"][3]:
        add_game_tab.show()
    elif tab == language["WINDOW"][4]:
        updates_tab.show()
    elif tab == language["WINDOW"][5]:
        options_tab.show()
    else:
        log_error(103, f"Tried to change to an unknown tab ({tab})")


def change_size(*args):
    """ Handles the event when the window's size is modified """
    global win_width, win_height
    width = win.winfo_width()
    height = win.winfo_height()
    if width != win_width or height != win_height:
        win_width = width
        win_height = height
        if apps_tab.active:
            apps_tab.reload_size()


def get_coordinates_from_root(widget) -> tuple[int, int]:
    x = widget.winfo_x()
    y = widget.winfo_y()
    while not isinstance(win.nametowidget(widget.winfo_parent()), (ctk.CTk, ctk.CTkToplevel)):  # while the parent is not the root
        widget = win.nametowidget(widget.winfo_parent())
        x += widget.winfo_x()
        y += widget.winfo_y()
    return x, y


# checking cwd
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):  # running as .exe
    if os.path.dirname(sys.executable) != os.getcwd():  # .exe path is not cwd
        os.chdir(os.path.dirname(sys.executable))
else:  # running as .py
    if os.path.dirname(__file__) != os.getcwd():  # .py path is not cwd
        os.chdir(os.path.dirname(__file__))


# checking directories
if not os.path.isdir("cache"):
    os.mkdir("cache")
if not os.path.isdir("icons"):
    os.mkdir("icons")
if not os.path.isdir("lng files"):
    os.mkdir("lng files")
if not os.path.isdir("url shortcuts"):
    os.mkdir("url shortcuts")

# reading parameters
if os.path.exists("params.APYL"):
    params = read_params()
else:
    log_error(101, "File params.APYL not found, recreating it")
    if os.path.exists("lng files/english.lng"):
        language = "english"
    else:
        for file in os.listdir("lng files"):
            if file.endswith(".lng"):
                if is_lng_file_valid(f"lng files/{file}"):
                    language = file.removesuffix(".lng")
                    break
        else:
            log_error(302, "Did not found any valid lng files to load")
            raise APYLauncherExceptions.LngFileMissing()
    params = {
        "language": language,
        "appearance": "dark",
        "size": "1280x720",
        "defaultfilter": 0,
        "stoplauncherwhengame": False,
        "lastgame": "",
        "ignoredmessages": [],
        "branch": "main"
    }
    with open("params.APYL", "x"):
        write_params(params)

# loading language
language = load_language(params["language"])
tl._language = language["DIALOGS"]  # changing toplevel widgets language

# applying parameters
ctk.set_appearance_mode(params["appearance"])

# reading installed apps
if os.path.exists("apps.csv"):
    apps = read_csv("apps.csv")
else:
    log_error(202, "apps.csv file not found, recreating one")
    with open("apps.csv", "x"):
        pass
    apps = {}

# defining window
win = ctk.CTk()
win.iconbitmap(tl.get_resource_path("launcher data/launcher_icon.ico"))
win.title(language["WINDOW"][0])
win.geometry(params["size"])
win.minsize(1000, 600)
win.protocol("WM_DELETE_WINDOW", on_closing)
win_width, win_height = 0, 0
ctk.ScalingTracker().add_window(lambda *args: win.geometry(params["size"]), win)  # resizes the window if scaling is modified

# defining ctk variables
head_font = ctk.CTkFont(size=30, weight="bold")
subhead_font = ctk.CTkFont(size=20, weight="bold")
bold_font = ctk.CTkFont(size=13, weight="bold")
normal_font = ctk.CTkFont(size=13)
star_image = ctk.CTkImage(Image.open(tl.get_resource_path("launcher data/star.png")), size=(30, 30))

# defining root frame (contains all the widgets except the top_frame)
root_frame = ctk.CTkFrame(win, fg_color="transparent")
root_frame.grid(row=1, column=0, sticky="nw")


# ctk classes
class HomeTab:
    """ Home tab containing info about the state of the version of the launcher (is it up-to-date ?) and a button to launch the last game launched """
    def __init__(self):
        self.active = False
        self.title_label = ctk.CTkLabel(root_frame, text=language["HOME"][0], font=head_font)
        self.updates_label = ctk.CTkLabel(root_frame, text=language["HOME"][1], font=subhead_font)
        self.update_launcher_label = ctk.CTkLabel(root_frame, text=language["HOME"][2])
        self.last_game_label = ctk.CTkLabel(root_frame, text=language["HOME"][5], font=subhead_font)
        if params["lastgame"] in apps:
            self.last_game_button = ctk.CTkButton(root_frame, text=params["lastgame"], command=lambda a=params["lastgame"]: launch(a))
        else:
            self.last_game_button = ctk.CTkButton(root_frame, text=language["HOME"][6], state="disabled")
        self.messages_label = ctk.CTkLabel(root_frame, text=language["HOME"][7], font=subhead_font)
        self.messages_button = ctk.CTkButton(root_frame, text=language["HOME"][7], command=lambda: self.show_launcher_normal_messages(ignore_ignored_messages=False))
        self.messages_toplevel = None
        self.messages_checkbox = None
        self.messages_ids_list = []
        self.update_messages_button = ctk.CTkButton(root_frame, text=language["HOME"][9], command=lambda: self.show_launcher_update_messages("2.0.0"))

    def show(self):
        if not self.active:
            hide_all()
            self.active = True
            self.title_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            self.updates_label.grid(row=1, column=0, padx=10, pady=15, sticky="w")
            self.update_launcher_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
            self.last_game_label.grid(row=3, column=0, padx=10, pady=15, sticky="w")
            self.last_game_button.grid(row=4, column=0, padx=10, pady=5, sticky="w")
            self.messages_label.grid(row=5, column=0, padx=10, pady=15, sticky="w")
            self.messages_button.grid(row=6, column=0, padx=10, pady=5, sticky="w")
            self.update_messages_button.grid(row=7, column=0, padx=10, pady=5, sticky="w")

    def hide(self):
        if self.active:
            self.active = False
            self.title_label.grid_forget()
            self.updates_label.grid_forget()
            self.update_launcher_label.grid_forget()
            self.last_game_label.grid_forget()
            self.last_game_button.grid_forget()
            self.messages_label.grid_forget()
            self.messages_button.grid_forget()
            self.update_messages_button.grid_forget()

    def reload_page(self):
        """ Reconfigures every widget, allows to change language """
        self.title_label.configure(text=language["HOME"][0])
        self.updates_label.configure(text=language["HOME"][1])
        self.last_game_label.configure(text=language["HOME"][5])
        self.messages_label.configure(text=language["HOME"][7])
        self.messages_button.configure(text=language["HOME"][7])
        self.update_messages_button.configure(text=language["HOME"][9])
        self.reload()

    def reload(self):
        """ Reloads the variable labels """
        # launcher update
        if updates_tab.launcher_has_to_update:
            self.update_launcher_label.configure(text=language["HOME"][4], font=bold_font)
        else:
            self.update_launcher_label.configure(text=language["HOME"][3], font=normal_font)

        # lastgame
        if params["lastgame"] in apps:
            self.last_game_button.configure(text=params["lastgame"], state="normal", command=lambda a=params["lastgame"]: launch(a))
        else:
            self.last_game_button.configure(text=language["HOME"][6], state="disabled", command=None)

    @staticmethod
    def show_launcher_update_messages(version_message: str = None):
        """Starts the search for update messages in a new thread

        :param version_message: if set to a version string, shows update messages for versions from the given version up to the current version of the launcher
        """
        if "checking for messages" not in threading.enumerate():
            threading.Thread(target=lambda version=version_message: home_tab._show_launcher_update_messages(version), name="checking for messages", daemon=True).start()

    @staticmethod
    def _show_launcher_update_messages(version_message: str = None):
        """Checks if there are available update messages to show and shows them if available

        :param version_message: if set to a version string, shows update messages for versions from the given version up to the current version of the launcher
        """
        if version_message is not None:
            message = up.check_for_version_message(version_message, _version, params["branch"])
            if message is not None:
                toplevel = ctk.CTkToplevel()
                toplevel.title(language["UPDATES"][12])
                toplevel.geometry("900x500")
                win.after(200, lambda: toplevel.iconbitmap(tl.get_resource_path("launcher data/launcher_icon.ico")))  # wait at least 200ms because else it doesn't work
                win.after(100, lambda: toplevel.lift())  # wait at least 100ms because else it doesn't work
                textbox = ctk.CTkTextbox(toplevel)
                textbox.insert("1.0", message)
                textbox.configure(state="disabled")
                textbox.pack(expand=True, fill="both")
            else:
                log_error(116, f"The retrieve of the launcher update message failed for versions {version_message} to {_version}")

    @staticmethod
    def show_launcher_normal_messages(ignore_ignored_messages=True):
        """Starts the search for normal messages in a new thread

        :param ignore_ignored_messages: if set to True, ignores the messages marked as ignored in the params dict
        """
        if "checking for messages" not in threading.enumerate():
            threading.Thread(target=home_tab._show_launcher_normal_messages, args=[ignore_ignored_messages], name="checking for messages", daemon=True).start()

    def _show_launcher_normal_messages(self, ignore_ignored_messages=True):
        """Checks if there are available messages to show and shows them if available

        :param ignore_ignored_messages: if set to True, ignores the messages marked as ignored in the params dict
        """
        self.messages_ids_list.clear()
        self.closing_messages()
        response = up.check_for_launcher_message(params["branch"])
        if response is not None:
            final_message = ""
            for message_id, message in response.items():
                if not ignore_ignored_messages or message_id not in params["ignoredmessages"]:
                    final_message += message
                    final_message += "\n\n"
                    self.messages_ids_list.append(message_id)
            if final_message != "":
                self.messages_toplevel = ctk.CTkToplevel()
                self.messages_toplevel.title(language["HOME"][7])
                self.messages_toplevel.geometry("900x500")
                self.messages_toplevel.protocol("WM_DELETE_WINDOW", self.closing_messages)
                win.after(200, lambda: self.messages_toplevel.iconbitmap(tl.get_resource_path("launcher data/launcher_icon.ico")))  # wait at least 200ms because else it doesn't work
                win.after(100, lambda: self.messages_toplevel.lift())  # wait at least 100ms because else it doesn't work
                textbox = ctk.CTkTextbox(self.messages_toplevel)
                textbox.insert("1.0", final_message)
                textbox.configure(state="disabled")
                textbox.pack(expand=True, fill="both")
                if ignore_ignored_messages:
                    self.messages_checkbox = ctk.CTkCheckBox(self.messages_toplevel, text=language["HOME"][8])
                    self.messages_checkbox.pack(side="left", padx=5, pady=5)

    def closing_messages(self):
        """ Called by the messages toplevel when getting closed """
        if self.messages_toplevel is not None:
            if self.messages_checkbox is not None:
                if bool(self.messages_checkbox.get()):
                    params["ignoredmessages"].extend(self.messages_ids_list)
                    write_params(params)
            self.messages_toplevel.destroy()

    def show_all_launcher_messages(self, version_message: str = None, ignore_ignored_messages=True):
        """Checks if there are available messages (normal and update messages) to show and shows them if available. Does not execute in a new thread

        :param version_message: if set to a version string, shows update messages for versions from the given version up to the current version of the launcher
        :param ignore_ignored_messages: if set to True, ignores the messages marked as ignored in the params dict
        """
        self._show_launcher_update_messages(version_message)
        self._show_launcher_normal_messages(ignore_ignored_messages)


class AppsTab:
    """ Apps tab containing all the apps stored in the launcher """
    def __init__(self):
        self.active = False
        self.number_columns = 0
        self.apps_dict = {}
        self.last_movement = None
        self.folder_stack = []

        self.top_frame = ctk.CTkFrame(root_frame)

        self.title_label = ctk.CTkLabel(self.top_frame, text=language["APPS"][0], font=head_font)

        filter_values = [language["APPS"][1], language["APPS"][2], language["APPS"][3], language["APPS"][4], language["APPS"][5], language["APPS"][24], language["APPS"][25]]
        self.filter_var = ctk.StringVar(self.top_frame, filter_values[params["defaultfilter"]])
        self.filter_menu = ctk.CTkOptionMenu(self.top_frame, values=filter_values, variable=self.filter_var, command=self.filter)

        self.search_label = ctk.CTkLabel(self.top_frame, text=language["APPS"][6])
        self.search_var = ctk.StringVar(self.top_frame)
        self.search_var.trace_add("write", self.search_modified)
        self.search_entry = ctk.CTkEntry(self.top_frame, textvariable=self.search_var)
        self.stop_search_button = ctk.CTkButton(self.top_frame, text="X", width=20, fg_color=ctk.ThemeManager.theme["CTkFrame"]["top_fg_color"], text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"], command=self.stop_search)

        self.random_select_button = ctk.CTkButton(self.top_frame, text=language["APPS"][19], command=self.random_select)

        self.cancel_app_movement_button = ctk.CTkButton(self.top_frame, text=language["APPS"][32], state="disabled", width=100, command=self.cancel_app_movement)

        self.path_label = ctk.CTkLabel(self.top_frame, text=language["APPS"][47])

        self.title_label.grid(row=0, column=0, padx=5, pady=5)
        self.filter_menu.grid(row=0, column=1, padx=25, pady=5)
        self.search_label.grid(row=0, column=2, padx=5, pady=5)
        self.search_entry.grid(row=0, column=3, padx=0, pady=5)
        self.stop_search_button.grid(row=0, column=4, padx=5, pady=5)
        self.random_select_button.grid(row=0, column=5, padx=25, pady=5)
        self.cancel_app_movement_button.grid(row=0, column=6, padx=15, pady=5)
        self.path_label.grid(row=1, column=0, columnspan=7, padx=5, pady=5, sticky="w")

        self.apps_frame = ctk.CTkScrollableFrame(root_frame, fg_color="transparent")

        self.title_label.after(100, lambda: self.reload_apps(False))

        self.right_click_menu = Menu(self.apps_frame, tearoff=0)
        self.right_click_menu.add_command(label=language["APPS"][48], command=self.create_folder)
        self.apps_frame.bind("<Button-3>", self.right_click)
        self.apps_frame._parent_canvas.bind("<Button-3>", self.right_click)

    def show(self):
        if not self.active:
            hide_all()
            self.active = True
            self.top_frame.grid(row=0, column=0, sticky="w", padx=10, pady=10, columnspan=3)
            self.reload_size()

    def hide(self):
        if self.active:
            self.active = False
            self.top_frame.grid_forget()
            self.apps_frame.grid_forget()

    def reload_page(self):
        """ Reconfigures every widget, allows to change language """
        self.title_label.configure(text=language["APPS"][0], font=head_font)

        filter_values = [language["APPS"][1], language["APPS"][2], language["APPS"][3], language["APPS"][4], language["APPS"][5], language["APPS"][24], language["APPS"][25]]
        self.filter_var.set(filter_values[params["defaultfilter"]])
        self.filter_menu.configure(values=filter_values)

        self.search_label.configure(text=language["APPS"][6])

        self.random_select_button.configure(text=language["APPS"][19])

        self.cancel_app_movement_button.configure(text=language["APPS"][32])

        if self.folder_stack:
            folder = self.folder_stack[-1]
        else:
            folder = "."
        path = folder
        if path != ".":
            parent_folder = folder
            while True:
                parent_folder = apps[parent_folder][2]
                path = parent_folder + " > " + path
                if parent_folder == ".":
                    break
        self.path_label.configure(text=f"{language["APPS"][47]}   {path}")

        self.reload_apps(False)

    def reload_size(self):
        """ Reloads the size of the apps frame and grid the apps in the apps dict """
        # reconfigure apps_frame size
        scaling = ctk.ScalingTracker().get_window_scaling(win)
        self.apps_frame.configure(width=win.winfo_width() / scaling - 23, height=win.winfo_height() / scaling - 145)

        # calculate number of columns
        self.number_columns = int((win.winfo_width() / scaling - 23) // 216)
        row = 0
        column = 0

        # grid every app
        for app in self.apps_dict:
            self.apps_dict[app].grid(column=column, row=row, padx=8, pady=8)
            column += 1
            if column >= self.number_columns:
                row += 1
                column = 0

        self.apps_frame.grid(row=1, column=0, columnspan=4, sticky="nsew")

    def reload_apps(self, grid=True):
        """Reloads the apps showed on the apps tab

        :param grid: if set to True, the apps_frame will be gridded when reloading is complete
        """
        search = self.search_var.get()
        active_filter = self.filter_var.get()

        # folder check
        if self.folder_stack:
            folder = self.folder_stack[-1]
        else:
            folder = "."

        if active_filter == language["APPS"][1]:  # no filter
            apps_to_load = {app: apps[app] for app in apps if app.lower().startswith(search.lower()) and apps[app][1] != "hidden" and apps[app][2] == folder}
        elif active_filter == language["APPS"][2]:  # favorites
            apps_to_load = {app: apps[app] for app in apps if app.lower().startswith(search.lower()) and apps[app][1] == "favorite" and apps[app][1] != "hidden" and apps[app][2] == folder}
        elif active_filter in [language["APPS"][3], language["APPS"][4], language["APPS"][5], language["APPS"][24]]:  # game / bonus / folder / config
            app_type = {language["APPS"][3]: "game", language["APPS"][4]: "bonus", language["APPS"][5]: "folder", language["APPS"][24]: "config"}[active_filter]
            apps_to_load = {app: apps[app] for app in apps if app.lower().startswith(search.lower()) and apps[app][0] == app_type and apps[app][1] != "hidden" and apps[app][2] == folder}
        elif active_filter == language["APPS"][25]:  # hidden
            apps_to_load = {app: apps[app] for app in apps if app.lower().startswith(search.lower()) and apps[app][1] == "hidden" and apps[app][2] == folder}
        else:  # unknown filter
            apps_to_load = apps.copy()

        # destroy previous widgets
        for app in self.apps_dict:
            self.apps_dict[app].destroy()
        self.apps_dict.clear()

        # create folder box if needed
        if folder != ".":
            folder_frame = ctk.CTkFrame(self.apps_frame, height=133)
            ctk.CTkLabel(folder_frame, text=language["APPS"][33], font=bold_font).grid(row=0, column=0, padx=5, pady=5)
            ctk.CTkLabel(folder_frame, text=cut_after_x_chrs(folder, 20), font=subhead_font).grid(row=1, column=0, padx=5)
            ctk.CTkButton(folder_frame, text=language["APPS"][34], command=self.move_back_folder_stack, width=100).grid(row=2, column=0, padx=5, pady=5)
            self.apps_dict[None] = folder_frame

        # create the apps_dict
        for app in apps_to_load:
            if apps_to_load[app][0] == "game" or apps_to_load[app][0] == "bonus":
                self.apps_dict[app] = App(self.apps_frame, app)
            elif apps_to_load[app][0] == "config":
                self.apps_dict[app] = Configuration(self.apps_frame, app)
            elif apps_to_load[app][0] == "folder":
                self.apps_dict[app] = Folder(self.apps_frame, app)

        # change the shown current path
        path = folder
        if path != ".":
            parent_folder = folder
            while True:
                parent_folder = apps[parent_folder][2]
                path = parent_folder + " > " + path
                if parent_folder == ".":
                    break

        self.path_label.configure(text=f"{language["APPS"][47]}   {path}")

        if grid:
            self.reload_size()  # grid the apps

    def filter(self, *args):
        self.reload_apps()

    def search_modified(self, *args):
        self.reload_apps()

    def stop_search(self, *args):
        self.search_var.set("")
        self.reload_apps()

    def random_select(self):
        folder = self.folder_stack[-1] if self.folder_stack else "."
        games_list = [app for app in apps.keys() if (apps[app][0] == "game" or apps[app][0] == "config") and (apps[app][2] == folder)]
        if games_list:
            game = random.choice(games_list)
            if tl.askyesno(language["APPS"][19], f"{language["APPS"][20]} {game}\n{language["APPS"][21]}"):
                launch(game)

    def change_last_movement(self, app: str, last_index: int):
        self.last_movement = (app, last_index)
        self.cancel_app_movement_button.configure(state="normal")

    def cancel_app_movement(self):
        """ Cancels the last app movement """
        global apps
        if self.last_movement is not None:
            item = apps[self.last_movement[0]]
            del apps[self.last_movement[0]]
            apps = insert_in_dict(apps, self.last_movement[1], (self.last_movement[0], item))
            self.cancel_app_movement_button.configure(state="disabled")
            self.last_movement = None
            write_csv(apps, "apps.csv")
            self.reload_apps()
        else:
            self.cancel_app_movement_button.configure(state="disabled")

    def add_folder_to_stack(self, folder: str, reload=True):
        """ Adds a folder to the stack """
        if folder in apps and apps[folder][0] == "folder":
            self.folder_stack.append(folder)
            if reload:
                self.reload_apps()

    def move_back_folder_stack(self, reload=True):
        """ Goes back to the previous folder in the stack (and removes the last folder from the stack) """
        if self.folder_stack:
            self.folder_stack.pop(-1)
            if reload:
                self.reload_apps()

    def clear_folder_stack(self, reload=True):
        """ Clears the folder stack """
        self.folder_stack.clear()
        if reload:
            self.reload_apps()

    def right_click(self, event):
        try:
            self.right_click_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.right_click_menu.grab_release()

    def create_folder(self):
        while True:
            name = tl.askstring(language["APPS"][48], language["APPS"][49], allow_none=False)
            if name is None:  # cancel
                break
            elif name in apps:
                tl.showwarning(language["APPS"][48], language["ADD"][9])
            elif name == ".":  # invalid name
                tl.showwarning(language["APPS"][48], language["APPS"][50])
            else:  # valid name
                apps[name] = ["folder", "not favorite", self.folder_stack[-1] if self.folder_stack else "."]
                write_csv(apps, "apps.csv")
                apps_tab.reload_apps()
                break


class App(ctk.CTkFrame):
    def __init__(self, master, name: str, drag=True, info_box=True, icon_type="app", width=200, height=140):
        """Class to contain a game name, icon and path to show in the AppsTab

        :param master: master window for the frame
        :param name: name of the app
        :param drag: optional: if set to True, dragging will be activated
        :param info_box: optional: if set to True, the info box will be activated
        :param icon_type: type of the icon to show in the explorer ("app" (game or bonus), "config" or "folder")
        :param width: width of the frame (200 pixels by default)
        :param width: height of the frame (140 pixels by default)
        """
        super().__init__(master)

        self.name = name
        if icon_type == "app":
            self.icon_index = 4
        elif icon_type == "config":
            self.icon_index = 3
        else:
            self.icon_index = None

        # icon label
        if icon_type == "app" or (icon_type == "config" and apps[name][self.icon_index] != ""):
            if os.path.isfile(apps[name][self.icon_index]):  # icon path exists
                try:
                    image = ctk.CTkImage(Image.open(apps[name][self.icon_index]), size=(85, 85))
                except UnidentifiedImageError:
                    image = ctk.CTkImage(Image.open(tl.get_resource_path("launcher data/question_mark_light.png")), size=(85, 85))
                self.icon_label = ctk.CTkLabel(self, text="", image=image)
                self.icon_label.grid(row=0, column=0, pady=5)
            else:
                self.icon_label = ctk.CTkLabel(self, text="", image=ctk.CTkImage(Image.open(tl.get_resource_path("launcher data/question_mark_light.png")), Image.open(tl.get_resource_path("launcher data/question_mark_dark.png")), (85, 85)))
                self.icon_label.grid(row=0, column=0, pady=5)
        elif icon_type == "config" and apps[name][self.icon_index] == "":
            self.icon_label = ctk.CTkLabel(self, text="", image=ctk.CTkImage(Image.open(tl.get_resource_path("launcher data/configuration_light.png")), Image.open(tl.get_resource_path("launcher data/configuration_dark.png")), (85, 85)))
            self.icon_label.grid(row=0, column=0, pady=5)
        elif icon_type == "folder":
            self.icon_label = ctk.CTkLabel(self, text="", image=ctk.CTkImage(Image.open(tl.get_resource_path("launcher data/folder_light.png")), Image.open(tl.get_resource_path("launcher data/folder_dark.png")), (85, 85)))
            self.icon_label.grid(row=0, column=0, pady=5)
        else:
            self.icon_label = ctk.CTkLabel(self, text="", image=ctk.CTkImage(Image.open(tl.get_resource_path("launcher data/question_mark_light.png")), Image.open(tl.get_resource_path("launcher data/question_mark_dark.png")), (85, 85)))
            self.icon_label.grid(row=0, column=0, pady=5)

        # name label
        if apps[name][1] == "favorite":
            self.name_label = ctk.CTkLabel(self, text=cut_after_x_chrs(name, 20), font=subhead_font, image=star_image, compound="right")
        else:
            self.name_label = ctk.CTkLabel(self, text=cut_after_x_chrs(name, 20), font=subhead_font)
        self.name_label.grid(row=1, column=0)

        self.update()
        chars_counter = 20
        while (width - self.name_label.winfo_width()) / 2 < 0:  # reduces the text until it is short enough to fit in the frame
            self.name_label.configure(text=cut_after_x_chrs(name, chars_counter))
            self.update()
            chars_counter -= 1
        x_padding = (width - self.name_label.winfo_width()) / 2
        y_padding = (height - 95 - self.name_label.winfo_height()) / 2
        if y_padding < 0:  # should not happen but if some wierd characters are used could theoretically cause a bug
            y_padding = 0
        self.name_label.grid(row=1, column=0, padx=x_padding, pady=y_padding)

        # bindings
        self.bind("<Double-Button-1>", self.double_left_click)
        self.bind("<Button-3>", self.right_click)
        self.icon_label.bind("<Double-Button-1>", self.double_left_click)
        self.icon_label.bind("<Button-3>", self.right_click)
        self.name_label.bind("<Double-Button-1>", self.double_left_click)
        self.name_label.bind("<Button-3>", self.right_click)

        # right click menu
        self.menu = Menu(master, tearoff=0)
        self.menu.add_command(label=language["APPS"][7], command=self.launch)
        self.menu.add_separator()
        if apps[name][1] == "favorite":
            self.menu.add_command(label=language["APPS"][11], command=self.remove_favorite)
            self.menu.add_command(label=language["APPS"][26], command=self.make_hidden)
        else:
            self.menu.add_command(label=language["APPS"][9], command=self.set_favorite)
            if apps[name][1] == "hidden":
                self.menu.add_command(label=language["APPS"][27], command=self.unmake_hidden)
            else:  # not hidden
                self.menu.add_command(label=language["APPS"][26], command=self.make_hidden)
        self.menu.add_separator()
        self.menu.add_command(label=language["APPS"][22], command=self.move)
        self.menu.add_command(label=language["APPS"][13], command=self.rename)
        self.menu.add_command(label=language["APPS"][17], command=self.delete)

        # dragging
        if drag:
            self.dragging = False
            self.startX = 0
            self.startY = 0
            self.drag_start_x = 0
            self.drag_start_y = 0
            self.start_grid_coordinates = (0, 0)
            self.place_app = App(master, self.name, False, False, icon_type)  # app to be placed for dragging
            self.bind("<Button-1>", self.drag_start)
            self.bind("<B1-Motion>", self.drag_motion)
            self.bind("<ButtonRelease-1>", self.drag_stop)
            self.icon_label.bind("<Button-1>", self.drag_start)
            self.icon_label.bind("<B1-Motion>", self.drag_motion)
            self.icon_label.bind("<ButtonRelease-1>", self.drag_stop)
            self.name_label.bind("<Button-1>", self.drag_start)
            self.name_label.bind("<B1-Motion>", self.drag_motion)
            self.name_label.bind("<ButtonRelease-1>", self.drag_stop)

        # info box
        if info_box:
            self.box_info_label = ctk.CTkLabel(win, text=rewrite_on_x_chrs(name, 20), font=bold_font, fg_color=ctk.ThemeManager.theme["CTkFrame"]["top_fg_color"], corner_radius=10)
            self.entered_for_more_than_1_sec = False
            self.after_func_id = ""
            self.bind("<Enter>", self.widget_entered)
            self.bind("<Leave>", self.widget_left)

    def destroy(self):
        self.name_label.destroy()
        self.icon_label.destroy()
        self.menu.destroy()
        try:
            self.place_app.destroy()
        except AttributeError:  # dragging is off
            pass
        try:
            self.box_info_label.destroy()
            if self.after_func_id:
                win.after_cancel(self.after_func_id)
        except AttributeError:  # info_box is off
            pass
        super().destroy()

    def double_left_click(self, event):
        self.box_info_label.place_forget()
        if self.after_func_id:
            win.after_cancel(self.after_func_id)
            self.after_func_id = ""

        single_app_tab.change_app(self.name)
        single_app_tab.show()

    def right_click(self, event):
        try:
            self.box_info_label.place_forget()
            if self.after_func_id:
                win.after_cancel(self.after_func_id)
                self.after_func_id = ""
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def launch(self):
        launch(self.name)

    def set_favorite(self):
        if apps[self.name][1] == "not favorite" or (apps[self.name][1] == "hidden" and tl.askyesno(language["APPS"][9], f"{language["APPS"][28]}\n{language["APPS"][29]}")):
            apps[self.name][1] = "favorite"
            write_csv(apps, "apps.csv")
            apps_tab.reload_apps()
            show_message(f"{self.name} {language["APPS"][10]}", 3000)

    def remove_favorite(self):
        apps[self.name][1] = "not favorite"
        write_csv(apps, "apps.csv")
        apps_tab.reload_apps()
        show_message(f"{self.name} {language["APPS"][12]}", 3000)

    def make_hidden(self):
        if apps[self.name][1] == "not favorite" or (apps[self.name][1] == "favorite" and tl.askyesno(language["APPS"][26], f"{language["APPS"][28]}\n{language["APPS"][29]}")):
            apps[self.name][1] = "hidden"
            write_csv(apps, "apps.csv")
            apps_tab.reload_apps()
            show_message(f"{self.name} {language["APPS"][30]}", 3000)

    def unmake_hidden(self):
        apps[self.name][1] = "not favorite"
        write_csv(apps, "apps.csv")
        apps_tab.reload_apps()
        show_message(f"{self.name} {language["APPS"][31]}", 3000)

    def move(self):
        tree = get_directories_tree()
        if tree is not None:
            resp = tl.asklauncherdir(language["APPS"][22], tree)
            if resp is not None:  # not cancelled
                if resp:
                    if resp[-1] in apps:
                        directory = resp[-1]
                    else:
                        log_error(206, f"Tried to move an app to a directory that does not exist: {resp[-1]}")
                        return
                else:  # selected the root directory
                    directory = "."
                apps[self.name][2] = directory
                write_csv(apps, "apps.csv")
                apps_tab.reload_apps()

    def rename(self):
        global apps
        while True:
            name = tl.askstring(language["APPS"][13], language["APPS"][14] + " " + self.name)
            if name is None:
                break
            else:
                if name in apps:
                    tl.showwarning(language["APPS"][13], language["APPS"][15])
                else:
                    if not check_name(name):
                        tl.showwarning(language["APPS"][13], language["ADD"][13])
                    else:
                        if self.icon_index is not None:  # not a folder
                            if os.path.isfile(apps[self.name][self.icon_index]):  # rename icon
                                if os.path.abspath("icons") == os.path.abspath(os.path.dirname(apps[self.name][self.icon_index])):  # file in icons folder
                                    os.rename(apps[self.name][self.icon_index], f"icons/{name}.png")
                                    apps[self.name][self.icon_index] = f"icons/{name}.png"
                            else:
                                log_error(106, f"Tried to rename the icon while renaming the game but its path did not exist: {apps[self.name][self.icon_index]}")
                        if self.icon_index == 4:  # game or bonus
                            if os.path.isfile(apps[self.name][3]):  # rename url shortcut if there is one
                                if os.path.abspath("url shortcuts") == os.path.abspath(os.path.dirname(apps[self.name][3])):  # file in url shortcuts folder
                                    os.rename(apps[self.name][3], f"url shortcuts/{name}.url")
                                    apps[self.name][3] = f"url shortcuts/{name}.url"
                            else:
                                log_error(112, f"Tried to rename the url shortcut while renaming the game but its path did not exist: {apps[self.name][3]}")
                        apps = rename_in_dict(apps, self.name, name)
                        for config in find_uses_in_config(self.name):
                            index = apps[config][4].index(self.name)
                            apps[config][4][index] = name
                        write_csv(apps, "apps.csv")
                        show_message(f"{self.name} {language["APPS"][16]} {name}", 3000)
                        self.name = name
                        self.name_label.configure(text=name)
                        apps_tab.reload_apps()
                        add_game_tab.reload()
                        break

    def delete(self):
        if tl.askyesno(language["APPS"][17], f"{language["APPS"][18]} {self.name}"):
            if self.icon_index is not None:  # not a folder
                if os.path.exists(apps[self.name][self.icon_index]):
                    if os.path.abspath("icons") == os.path.abspath(os.path.dirname(apps[self.name][self.icon_index])):  # file in icons folder
                        os.remove(apps[self.name][self.icon_index])
                else:
                    log_error(105, f"Tried to delete the icon while deleting the game but its path did not exist: \"{apps[self.name][self.icon_index]}\"")
            if self.icon_index == 4:  # game or bonus
                if os.path.isfile(apps[self.name][3]):
                    if os.path.abspath("url shortcuts") == os.path.abspath(os.path.dirname(apps[self.name][3])):  # file in url shortcuts folder
                        os.remove(f"url shortcuts/{self.name}.url")
                else:
                    log_error(113, f"Tried to delete the url shortcut while deleting the game but its path did not exist: {apps[self.name][3]}")
            del apps[self.name]
            write_csv(apps, "apps.csv")
            delete_usages_of_app(self.name)
            apps_tab.reload_apps()
            add_game_tab.reload()
            if params["lastgame"] == self.name:
                params["lastgame"] = ""
                write_params(params)
                home_tab.reload()

    def disable(self):
        """ Grays out the app text """
        self.name_label.configure(text_color="gray")

    def enable(self):
        """ Restores the app text to its normal color """
        self.name_label.configure(text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])

    def drag_start(self, event):
        self.dragging = True
        self.startX = event.x
        self.startY = event.y
        self.drag_start_x = self.place_app.winfo_x()
        self.drag_start_y = self.place_app.winfo_y()
        self.start_grid_coordinates = (self.grid_info()["column"], self.grid_info()["row"])
        self.disable()
        self.place_app.lift()

    def drag_motion(self, event):
        if self.dragging:
            x = self.winfo_x() - self.startX + event.x
            y = self.winfo_y() - self.startY + event.y
            if x <= 0:
                x = 1
            elif x > self.master.winfo_width() - self.winfo_width():
                x = self.master.winfo_width() - self.winfo_width()
            if y <= 0:
                y = 1
            elif y > self.master.winfo_height() - self.winfo_height():
                y = self.master.winfo_height() - self.winfo_height()
            self.place_app.place(x=x, y=y)

    def drag_stop(self, event):
        global apps
        if self.dragging:
            self.place_app.place_forget()
            self.enable()
            if self.drag_start_x != self.place_app.winfo_x() or self.drag_start_y != self.place_app.winfo_y():  # widget has been moved
                x = self.place_app.winfo_x() + self.place_app.winfo_width() // 2
                y = self.place_app.winfo_y() + self.place_app.winfo_height() // 2
                coordinates = self.master.grid_location(x, y)
                grid_size = self.master.grid_size()
                if coordinates[0] >= grid_size[0]:
                    coordinates = (grid_size[0] - 1, coordinates[1])
                if coordinates[1] >= grid_size[1]:
                    coordinates = (coordinates[0], grid_size[1] - 1)
                if self.start_grid_coordinates != coordinates:  # widget has been moved off its starting grid square
                    start_index = apps_tab.number_columns * self.start_grid_coordinates[1] + self.start_grid_coordinates[0]
                    index = apps_tab.number_columns * coordinates[1] + coordinates[0]
                    if index >= len(apps):
                        index = len(apps) - 1
                    item = (self.name, apps[self.name])
                    del apps[self.name]
                    apps = insert_in_dict(apps, index, item)
                    write_csv(apps, "apps.csv")
                    apps_tab.change_last_movement(self.name, start_index)
                    apps_tab.reload_apps()
            self.dragging = False

    def widget_entered(self, event):
        """ Called when the app frame is entered """
        if not self.entered_for_more_than_1_sec and not self.after_func_id:
            self.after_func_id = win.after(500, self.widget_entered_since_1_sec)

    def widget_entered_since_1_sec(self):
        """ Called when the widget has been entered for more than a second """
        self.after_func_id = ""
        cursor_x, cursor_y = win.winfo_pointerx() - win.winfo_rootx(), win.winfo_pointery() - win.winfo_rooty()
        x_min, y_min = get_coordinates_from_root(self)
        x_max, y_max = x_min + self.winfo_width(), y_min + self.winfo_height()
        if x_min <= cursor_x <= x_max and y_min <= cursor_y <= y_max:  # cursor is still in the app frame
            self.entered_for_more_than_1_sec = True
            self.box_info_label.place(x=x_max + 5, y=y_min)
            win.update()
            if get_coordinates_from_root(self)[0] + self.winfo_width() + 16 + self.box_info_label.winfo_width() > win.winfo_width():
                self.box_info_label.place(x=x_min - self.box_info_label.winfo_width() - 5, y=y_min)  # place to the left of the frame if it exceeds the window's width

    def widget_left(self, event):
        """ Called when the app frame is left """
        if self.entered_for_more_than_1_sec:
            x_min, y_min = get_coordinates_from_root(self)
            x_max, y_max = x_min + self.winfo_width(), y_min + self.winfo_height()
            cursor_x, cursor_y = event.x + x_min, event.y + y_min
            x_min += 1  # change the values to make the frame 1px smaller so the event is registered as left
            x_max -= 1
            y_min += 1
            y_max -= 1
            if cursor_x < x_min or cursor_x > x_max or cursor_y < y_min or cursor_y > y_max:  # cursor is not in the app frame
                self.entered_for_more_than_1_sec = False
                self.box_info_label.place_forget()


class Configuration(App):
    def __init__(self, master, name: str, drag=True, info_box=True):
        """Class to contain a config name, icon and apps to show in the AppsTab

        :param master: master window for the frame
        :param name: name of the config
        :param drag: optional: if set to True, dragging will be activated
        :param info_box: optional: if set to True, the info box will be activated
        """
        super().__init__(master, name, drag, info_box, "config")

    def launch(self):
        for a in apps[self.name][4]:
            if a in apps:
                if apps[a][0] == "game" or apps[a][0] == "bonus":
                    launch(a, False)
                else:
                    log_error(110, f"One of the apps contained in the {self.name} config is not a game / bonus: {apps[a][0]}")
            else:
                log_error(109, f"One of the apps contained in the {self.name} config does not exist: {a}")
        params["lastgame"] = self.name
        home_tab.reload()
        write_params(params)


class Folder(App):
    def __init__(self, master, name: str, drag=True, info_box=True):
        """Class to contain a folder name and apps to show in the AppsTab

        :param master: master window for the frame
        :param name: name of the folder
        :param drag: optional: if set to True, dragging will be activated
        :param info_box: optional: if set to True, the info box will be activated
        """
        super().__init__(master, name, drag, info_box, "folder")

    def launch(self):
        self.double_left_click(None)

    def double_left_click(self, event):
        apps_tab.add_folder_to_stack(self.name)

    def delete(self):
        if tl.askyesno(language["APPS"][17], f"{language["APPS"][18]} {self.name}"):
            resp = tl.askyesno(language["APPS"][17], f"{language["APPS"][51]}\n{language["APPS"][52]}")
            if resp:
                for app in get_apps_in_folder(self.name):
                    apps[app][2] = "."
            else:
                for app in get_apps_in_folder(self.name):
                    if apps[app][0] == "game" or apps[app][0] == "bonus":
                        icon_index = 4
                    else:
                        icon_index = 3

                    if os.path.exists(apps[app][icon_index]):
                        if os.path.abspath("icons") == os.path.abspath(
                                os.path.dirname(apps[app][icon_index])):  # file in icons folder
                            os.remove(apps[app][icon_index])
                    else:
                        log_error(105, f"Tried to delete the icon while deleting the game but its path did not exist: \"{apps[app][icon_index]}\"")
                    if icon_index == 4:  # game or bonus
                        if os.path.isfile(apps[app][3]):
                            if os.path.abspath("url shortcuts") == os.path.abspath(
                                    os.path.dirname(apps[app][3])):  # file in url shortcuts folder
                                os.remove(f"url shortcuts/{app}.url")
                        else:
                            log_error(113, f"Tried to delete the url shortcut while deleting the game but its path did not exist: {apps[self.name][3]}")
                    del apps[app]

            if resp is not None:
                del apps[self.name]
                write_csv(apps, "apps.csv")
                delete_usages_of_app(self.name)
                apps_tab.reload_apps()
                add_game_tab.reload()
                if params["lastgame"] == self.name:
                    params["lastgame"] = ""
                    write_params(params)
                    home_tab.reload()


class SingleAppTab:
    """ Single app tab containing infos about the selected app (shown when double-clicking on an app) """
    def __init__(self):
        self.active = False
        self.current_app = None

        self.back_button = ctk.CTkButton(root_frame, text=language["APPS"][34], command=apps_tab.show, image=ctk.CTkImage(Image.open(tl.get_resource_path("launcher data/back_arrow_light.png")), Image.open(tl.get_resource_path("launcher data/back_arrow_dark.png"))), width=120)
        self.title_label = ctk.CTkLabel(root_frame, text="", font=head_font)
        self.icon_label = ctk.CTkLabel(root_frame, text="")
        self.start_button = ctk.CTkButton(root_frame, text=language["APPS"][7], command=self.start_app)
        self.apps_frame = ctk.CTkScrollableFrame(root_frame, label_text=language["APPS"][23], width=300, height=400)

        # modify frame
        self.modify_frame = ctk.CTkFrame(root_frame)
        self.title_modify_label = ctk.CTkLabel(self.modify_frame, text=language["APPS"][35], font=subhead_font)
        self.save_button = ctk.CTkButton(self.modify_frame, text=language["OPTIONS"][1], command=self.save)
        self.cancel_button = ctk.CTkButton(self.modify_frame, text=language["APPS"][32], command=self.cancel)
        self.name_label = ctk.CTkLabel(self.modify_frame, text=language["ADD"][8])
        self.name_var = ctk.StringVar(self.modify_frame)
        self.name_entry = ctk.CTkEntry(self.modify_frame, textvariable=self.name_var)
        self.state_label = ctk.CTkLabel(self.modify_frame, text=language["APPS"][36])
        self.state_var = ctk.StringVar(self.modify_frame)
        self.state_menu = ctk.CTkOptionMenu(self.modify_frame, values=[language["APPS"][37], language["APPS"][38], language["APPS"][39]], variable=self.state_var)
        self.move_button = ctk.CTkButton(self.modify_frame, text=language["APPS"][22], command=self.move)
        self.delete_button = ctk.CTkButton(self.modify_frame, text=language["APPS"][17], command=self.delete)
        self.advanced_frame = ctk.CTkFrame(self.modify_frame)
        self.advanced_label = ctk.CTkLabel(self.advanced_frame, text=language["APPS"][40], font=bold_font)
        self.change_icon_button = ctk.CTkButton(self.advanced_frame, text=language["APPS"][41], command=self.change_icon_path)
        self.delete_icon_button = ctk.CTkButton(self.advanced_frame, text=language["APPS"][46], command=self.delete_icon)
        self.change_path_button = ctk.CTkButton(self.advanced_frame, text=language["APPS"][42], command=self.change_app_path)
        self.advanced_label.grid(row=0, column=0, padx=3, pady=3)
        self.change_icon_button.grid(row=1, column=0, padx=3, pady=3)
        self.delete_icon_button.grid(row=2, column=0, padx=3, pady=3)
        self.change_path_button.grid(row=3, column=0, padx=3, pady=3)

        self.title_modify_label.grid(row=0, column=0, padx=5, pady=15, columnspan=2)
        self.name_label.grid(row=1, column=0, padx=5, pady=5)
        self.name_entry.grid(row=1, column=1, padx=5, pady=5)
        self.state_label.grid(row=2, column=0, padx=5, pady=5)
        self.state_menu.grid(row=2, column=1, padx=5, pady=5)
        self.move_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)
        self.delete_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5)
        self.advanced_frame.grid(row=5, column=0, columnspan=2, padx=5, pady=5)
        self.save_button.grid(row=6, column=0, padx=5, pady=15)
        self.cancel_button.grid(row=6, column=1, padx=5, pady=15)

    def show(self):
        if not self.active:
            hide_all()
            self.active = True
            self.back_button.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            self.title_label.grid(row=1, column=0, padx=10, pady=10, sticky="nw")
            self.icon_label.grid(row=1, column=1, padx=30, pady=30, rowspan=3, sticky="nw")
            self.start_button.grid(row=2, column=0, padx=10, pady=10, sticky="w")
            self.modify_frame.grid(row=3, column=0, padx=10, pady=10, sticky="w")
            if apps[self.current_app][0] == "config":
                self.apps_frame.grid(row=1, column=2, padx=10, pady=10, rowspan=3)

    def hide(self):
        if self.active:
            self.active = False
            self.back_button.grid_forget()
            self.title_label.grid_forget()
            self.icon_label.grid_forget()
            self.start_button.grid_forget()
            self.modify_frame.grid_forget()
            self.apps_frame.grid_forget()

    def reload_page(self):
        """ Reconfigures every widget, allows to change language """
        self.back_button.configure(text=language["APPS"][34])
        self.start_button.configure(text=language["APPS"][7])
        self.apps_frame.configure(label_text=language["APPS"][23])
        self.title_modify_label.configure(text=language["APPS"][35])
        self.save_button.configure(text=language["OPTIONS"][1])
        self.name_label.configure(text=language["ADD"][8])
        self.state_label.configure(text=language["APPS"][36])
        if self.current_app is not None:
            self.state_var.set({"not favorite": language["APPS"][37], "favorite": language["APPS"][38], "hidden": language["APPS"][39]}[apps[self.current_app][1]])
        self.state_menu.configure(values=[language["APPS"][37], language["APPS"][38], language["APPS"][39]])
        self.delete_button.configure(text=language["APPS"][17])
        self.advanced_label.configure(text=language["APPS"][40])
        self.change_icon_button.configure(text=language["APPS"][41])
        self.delete_icon_button.configure(text=language["APPS"][46])
        self.change_path_button.configure(text=language["APPS"][42])

    def change_app(self, app_name: str):
        """Changes the current app shown in the single app tab

        :param app_name: name of the app / config to show (has to be in the apps dict)
        """
        if app_name in apps:
            self.current_app = app_name
            self.name_var.set(app_name)
            self.state_var.set({"not favorite": language["APPS"][37], "favorite": language["APPS"][38], "hidden": language["APPS"][39]}[apps[app_name][1]])
            app_type = apps[app_name][0]
            icon_index = 4 if app_type == "game" or app_type == "bonus" else 3

            self.title_label.configure(text=cut_after_x_chrs(app_name, 20))
            if app_type == "game" or app_type == "bonus" or (app_type == "config" and apps[app_name][icon_index] != ""):
                if os.path.isfile(apps[app_name][icon_index]):  # icon path exists
                    try:
                        image = ctk.CTkImage(Image.open(apps[app_name][icon_index]), size=(200, 200))
                    except UnidentifiedImageError:
                        image = ctk.CTkImage(Image.open(tl.get_resource_path("launcher data/question_mark_light.png")), Image.open(tl.get_resource_path("launcher data/question_mark_dark.png")), (200, 200))
                    self.icon_label.configure(image=image)
                else:
                    self.icon_label.configure(image=ctk.CTkImage(Image.open(tl.get_resource_path("launcher data/question_mark_light.png")), Image.open(tl.get_resource_path("launcher data/question_mark_dark.png")), (200, 200)))
            elif app_type == "config" and apps[app_name][icon_index] == "":
                self.icon_label.configure(image=ctk.CTkImage(Image.open(tl.get_resource_path("launcher data/configuration_light.png")), Image.open(tl.get_resource_path("launcher data/configuration_dark.png")), (200, 200)))

            if app_type == "game" or app_type == "bonus":  # app
                self.change_path_button.grid(row=3, column=0, padx=3, pady=3)
            else:  # config
                self.change_path_button.grid_forget()
                for widget in self.apps_frame.winfo_children():
                    widget.destroy()
                row = 0
                for app in apps[self.current_app][4]:
                    ctk.CTkLabel(self.apps_frame, text=app).grid(row=row, column=0, padx=3, pady=3, sticky="w")
                    row += 1
        else:
            log_error(114, f"Tried to show an app that doesn't exist: {app_name}")

    def start_app(self):
        """ Starts the current shown app """
        if self.current_app is not None:
            app_type = apps[self.current_app][0]
            if app_type == "game" or app_type == "bonus":
                launch(self.current_app)
            elif app_type == "config":
                for a in apps[self.current_app][4]:
                    if a in apps:
                        if apps[a][0] == "game" or apps[a][0] == "bonus":
                            launch(a, False)
                        else:
                            log_error(110, f"One of the apps contained in the {self.current_app} config is not a game / bonus: {apps[a][0]}")
                    else:
                        log_error(109, f"One of the apps contained in the {self.current_app} config does not exist: {a}")
                params["lastgame"] = self.current_app
                home_tab.reload()
                write_params(params)

    def save(self):
        global apps

        # name
        name = self.name_var.get()
        if name != self.current_app:
            if name in apps:
                tl.showwarning(language["APPS"][13], language["APPS"][15])
                return
            else:
                if not check_name(name):
                    tl.showwarning(language["APPS"][13], language["ADD"][13])
                    return
                else:
                    if apps[self.current_app][0] == "game" or apps[self.current_app][0] == "bonus":
                        icon_index = 4
                    else:
                        icon_index = 3
                    if os.path.isfile(apps[self.current_app][icon_index]):  # rename icon
                        if os.path.abspath("icons") == os.path.abspath(os.path.dirname(apps[self.current_app][icon_index])):  # file in icons folder
                            os.rename(apps[self.current_app][icon_index], f"icons/{name}.png")
                            apps[self.current_app][icon_index] = f"icons/{name}.png"
                    else:
                        log_error(106, f"Tried to rename the icon while renaming the game but its path did not exist: {apps[self.current_app][icon_index]}")
                    if icon_index == 4:  # game or bonus
                        if os.path.isfile(apps[self.current_app][3]):  # rename url shortcut
                            if os.path.abspath("url shortcuts") == os.path.abspath(os.path.dirname(apps[self.current_app][3])):  # file in url shortcuts folder
                                os.rename(apps[self.current_app][3], f"url shortcuts/{name}.url")
                                apps[self.current_app][3] = f"url shortcuts/{name}.url"
                        else:
                            log_error(112, f"Tried to rename the url shortcut while renaming the game but its path did not exist: {apps[self.current_app][3]}")

                    apps = rename_in_dict(apps, self.current_app, name)
                    for config in find_uses_in_config(self.current_app):
                        index = apps[config][4].index(self.current_app)
                        apps[config][4][index] = name
                    self.current_app = name
                    self.title_label.configure(text=cut_after_x_chrs(self.current_app, 20))
                    add_game_tab.reload()

        # state
        new_state = {language["APPS"][37]: "not favorite", language["APPS"][38]: "favorite", language["APPS"][39]: "hidden"}[self.state_var.get()]
        if new_state != apps[self.current_app][1]:
            apps[self.current_app][1] = new_state

        # save parameters
        write_csv(apps, "apps.csv")
        apps_tab.reload_apps(False)
        show_message(language["APPS"][43], 3000)

    def cancel(self):
        self.name_var.set(self.current_app)
        self.state_var.set({"not favorite": language["APPS"][37], "favorite": language["APPS"][38], "hidden": language["APPS"][39]}[apps[self.current_app][1]])

    def delete(self):
        if tl.askyesno(language["APPS"][17], f"{language["APPS"][18]} {self.current_app}"):
            if apps[self.current_app][0] == "game" or apps[self.current_app][0] == "bonus":
                icon_index = 4
            else:
                icon_index = 3
            if os.path.exists(apps[self.current_app][icon_index]):
                if os.path.abspath("icons") == os.path.abspath(os.path.dirname(apps[self.current_app][icon_index])):  # file in icons folder
                    os.remove(apps[self.current_app][icon_index])
            else:
                log_error(105, f"Tried to delete the icon while deleting the game but its path did not exist: \"{apps[self.current_app][icon_index]}\"")
            if icon_index == 4:  # game or bonus
                if os.path.isfile(apps[self.current_app][3]):
                    if os.path.abspath("url shortcuts") == os.path.abspath(os.path.dirname(apps[self.current_app][3])):
                        os.remove(f"url shortcuts/{self.current_app}.url")
                else:
                    log_error(113, f"Tried to delete the url shortcut while deleting the game but its path did not exist: {apps[self.current_app][3]}")
            del apps[self.current_app]
            write_csv(apps, "apps.csv")
            delete_usages_of_app(self.current_app)
            apps_tab.show()
            apps_tab.reload_apps()
            add_game_tab.reload()
            if params["lastgame"] == self.current_app:
                params["lastgame"] = ""
                write_params(params)
                home_tab.reload()

    def move(self):
        tree = get_directories_tree()
        if tree is not None:
            resp = tl.asklauncherdir(language["APPS"][22], tree)
            if resp is not None:  # not cancelled
                if resp:
                    if resp[-1] in apps:
                        directory = resp[-1]
                    else:
                        log_error(206, f"Tried to move an app to a directory that does not exist: {resp[-1]}")
                        return
                else:  # selected the root directory
                    directory = "."
                apps[self.current_app][2] = directory
                write_csv(apps, "apps.csv")
                apps_tab.reload_apps(False)

    def change_icon_path(self):
        new_path = tl.askfile(language["APPS"][41], initialdir=os.path.normpath(os.path.expanduser("~/Desktop")))
        if new_path is not None:
            if os.path.isfile(new_path):
                try:
                    image = Image.open(new_path)
                except UnidentifiedImageError:
                    tl.showerror(language["APPS"][41], language["APPS"][44])
                else:
                    if apps[self.current_app][0] == "game" or apps[self.current_app][0] == "bonus":
                        icon_index = 4
                    else:  # config
                        icon_index = 3
                    apps[self.current_app][icon_index] = new_path
                    write_csv(apps, "apps.csv")
                    apps_tab.reload_apps(False)
                    self.icon_label.configure(image=ctk.CTkImage(image, size=(200, 200)))
                    show_message(language["APPS"][43], 3000)
            else:
                tl.showerror(language["APPS"][41], language["ADD"][7])

    def change_app_path(self):
        new_path = tl.askfile(language["APPS"][42], initialdir=os.path.normpath(os.path.expanduser("~/Desktop")))
        if new_path is not None:
            if os.path.isfile(new_path):
                if os.path.abspath(os.path.dirname(new_path)) != os.path.abspath("url shortcuts") and os.path.basename(new_path) == f"{self.current_app}.url":
                    new_path = shutil.copy2(new_path, f"url shortcuts/{self.current_app}.url")
                apps[self.current_app][3] = new_path

                if tl.askyesno(language["APPS"][42], language["APPS"][45]):  # modify icon
                    # get the image path
                    app_format = gi.get_type_file(new_path)
                    if app_format == "exe":
                        icon_path = gi.get_icon_from_exe(new_path, f"icons/{self.current_app}")
                    elif app_format == "steam" or app_format == "uplay":
                        icon_path = gi.get_icon_steam_uplay(new_path, f"icons/{self.current_app}")
                    elif app_format == "epic":
                        icon_path = gi.get_icon_epic(new_path, f"icons/{self.current_app}")
                    else:  # unknown / error
                        tl.showwarning(language["ADD"][0], language["ADD"][10])
                        icon_path = ""
                    if icon_path is None:
                        tl.showwarning(language["ADD"][0], language["ADD"][10])
                        icon_path = ""
                    # apply new parameters
                    if apps[self.current_app][0] == "game" or apps[self.current_app][0] == "bonus":
                        icon_index = 4
                    else:
                        icon_index = 3
                    apps[self.current_app][icon_index] = icon_path
                    image = Image.open(icon_path)
                    self.icon_label.configure(image=ctk.CTkImage(image, size=(200, 200)))

                write_csv(apps, "apps.csv")
                apps_tab.reload_apps(False)
                show_message(language["APPS"][43], 3000)
            else:
                tl.showerror(language["APPS"][42], language["ADD"][7])

    def delete_icon(self):
        if apps[self.current_app][0] == "game" or apps[self.current_app][0] == "bonus":
            icon_index = 4
        else:
            icon_index = 3
        if os.path.isfile(apps[self.current_app][icon_index]):
            if os.path.abspath("icons") == os.path.abspath(os.path.dirname(apps[self.current_app][icon_index])):  # file in icons folder
                os.remove(apps[self.current_app][icon_index])
        else:
            log_error(105, f"Tried to delete the icon while deleting the game but its path did not exist: \"{apps[self.current_app][icon_index]}\"")
        apps[self.current_app][icon_index] = ""
        write_csv(apps, "apps.csv")
        apps_tab.reload_apps(False)
        show_message(language["APPS"][43], 3000)
        if icon_index == 4:  # game or bonus
            self.icon_label.configure(image=ctk.CTkImage(Image.open(tl.get_resource_path("launcher data/question_mark_light.png")), Image.open(tl.get_resource_path("launcher data/question_mark_dark.png")), (200, 200)))
        else:  # config
            self.icon_label.configure(image=ctk.CTkImage(Image.open(tl.get_resource_path("launcher data/configuration_light.png")), Image.open(tl.get_resource_path("launcher data/configuration_dark.png")), (200, 200)))


class AddGameTab:
    """ Adding tab containing the functionalities to add apps / configs / folders to the launcher """
    def __init__(self):
        self.active = False
        self.active_tab = 0
        self.title_label = ctk.CTkLabel(root_frame, text=language["ADD"][0], font=head_font)
        self.tabs_button = ctk.CTkSegmentedButton(root_frame, values=[language["ADD"][15], language["ADD"][16], language["ADD"][17]], command=self.change_tab)
        self.tabs_button.set(language["ADD"][15])

        # single app
        self.single_app_frame = ctk.CTkFrame(root_frame, fg_color="transparent")

        self.type_label_s = ctk.CTkLabel(self.single_app_frame, text=language["ADD"][2])
        self.type_var_s = ctk.StringVar(root_frame, language["ADD"][3])
        self.type_menu_s = ctk.CTkOptionMenu(self.single_app_frame, variable=self.type_var_s, values=[language["ADD"][3], language["ADD"][4]], width=80)

        self.path_label_s = ctk.CTkLabel(self.single_app_frame, text=language["ADD"][5])
        self.path_var_s = ctk.StringVar(root_frame)
        self.selected_path_frame_s = ctk.CTkScrollableFrame(self.single_app_frame, width=275, height=30, orientation="horizontal")
        self.selected_path_label_s = ctk.CTkLabel(self.selected_path_frame_s, text="")
        self.selected_path_label_s.pack()
        self.path_button_s = ctk.CTkButton(self.single_app_frame, text=language["ADD"][6], command=self.select_path_s)

        self.name_label_s = ctk.CTkLabel(self.single_app_frame, text=language["ADD"][8])
        self.name_var_s = ctk.StringVar(root_frame)
        self.name_entry_s = ctk.CTkEntry(self.single_app_frame, width=150, textvariable=self.name_var_s)

        self.validate_button_s = ctk.CTkButton(self.single_app_frame, text=language["ADD"][1], command=self.validate_s)

        self.type_label_s.grid(row=0, column=0, padx=5, pady=30, sticky="e")
        self.type_menu_s.grid(row=0, column=1, padx=5, pady=30)
        self.path_label_s.grid(row=1, column=0, padx=5, pady=5)
        self.path_button_s.grid(row=1, column=1, padx=5, pady=5)
        self.selected_path_frame_s.grid(row=2, column=0, columnspan=2)
        self.name_label_s.grid(row=3, column=0, padx=5, pady=30)
        self.name_entry_s.grid(row=3, column=1, padx=5)
        self.validate_button_s.grid(row=4, column=0, columnspan=2, pady=20)

        # configuration
        self.configuration_frame = ctk.CTkFrame(root_frame, fg_color="transparent")

        self.apps_to_add_label_c = ctk.CTkLabel(self.configuration_frame, text=language["ADD"][18])
        self.apps_to_add_frame_c = ctk.CTkScrollableFrame(self.configuration_frame, width=325, height=225)
        self.name_label_c = ctk.CTkLabel(self.configuration_frame, text=language["ADD"][19])
        self.name_var_c = ctk.StringVar(root_frame)
        self.name_entry_c = ctk.CTkEntry(self.configuration_frame, textvariable=self.name_var_c)
        self.validate_button_c = ctk.CTkButton(self.configuration_frame, text=language["ADD"][1], command=self.validate_c)

        self.apps_to_add_label_c.grid(row=0, column=0, columnspan=2)
        self.apps_to_add_frame_c.grid(row=1, column=0, columnspan=2, pady=10, sticky="w")
        self.name_label_c.grid(row=2, column=0, padx=5, pady=20)
        self.name_entry_c.grid(row=2, column=1, padx=5, pady=20)
        self.validate_button_c.grid(row=3, column=0, columnspan=2, pady=10)

        # auto detect
        self.auto_detect_frame = ctk.CTkFrame(root_frame, fg_color="transparent")

        self.add_folder_button = ctk.CTkButton(self.auto_detect_frame, text=language["ADD"][23], command=self.add_folder)

        self.add_folder_button.grid(row=0, column=0, padx=5, pady=30, sticky="e")

        self.reload()

    def show(self):
        if not self.active:
            hide_all()
            self.active = True
            self.title_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            self.tabs_button.grid(row=1, column=0, padx=10, pady=5, sticky="w")
            if self.active_tab == 0:
                self.single_app_frame.grid(row=2, column=0, padx=10, pady=5, sticky="w")
            elif self.active_tab == 1:
                self.configuration_frame.grid(row=2, column=0, padx=10, pady=5, sticky="w")
            elif self.active_tab == 2:
                self.auto_detect_frame.grid(row=2, column=0, padx=10, pady=5, sticky="w")

    def hide(self):
        if self.active:
            self.active = False
            self.title_label.grid_forget()
            self.tabs_button.grid_forget()
            self.single_app_frame.grid_forget()
            self.configuration_frame.grid_forget()
            self.auto_detect_frame.grid_forget()

    def reload_page(self):
        """ Reconfigures every widget, allows to change language """
        self.title_label.configure(text=language["ADD"][0])
        self.tabs_button.configure(values=[language["ADD"][15], language["ADD"][16], language["ADD"][17]])
        self.tabs_button.set(language["ADD"][15])

        # single app
        self.type_label_s.configure(text=language["ADD"][2])
        self.type_var_s.set(language["ADD"][3])
        self.type_menu_s.configure(values=[language["ADD"][3], language["ADD"][4]])

        self.path_label_s.configure(text=language["ADD"][5])
        self.path_button_s.configure(text=language["ADD"][6])

        self.name_label_s.configure(text=language["ADD"][8])

        self.validate_button_s.configure(text=language["ADD"][1])

        # configuration
        self.apps_to_add_label_c.configure(text=language["ADD"][18])
        self.name_label_c.configure(text=language["ADD"][19])
        self.validate_button_c.configure(text=language["ADD"][1])

        # auto detect
        self.add_folder_button.configure(text=language["ADD"][23])

        self.reload()

    def change_tab(self, tab):
        """ Changes to the given tab """
        if tab == language["ADD"][15]:  # single app
            self.active_tab = 0
        elif tab == language["ADD"][16]:  # configuration
            self.active_tab = 1
        elif tab == language["ADD"][17]:  # auto detect
            self.active_tab = 2
        if self.active:
            self.hide()
            self.show()

    def reload(self):
        """ Reloads the page widgets """
        for widget in self.apps_to_add_frame_c.winfo_children():
            widget.destroy()
        row = 0
        for app in apps:
            if apps[app][0] == "game" or apps[app][0] == "bonus":
                ctk.CTkCheckBox(self.apps_to_add_frame_c, text=rewrite_on_x_chrs(app, 25)).grid(row=row, column=0, pady=5, sticky="w")
                row += 1

    def reset_entries_s(self):
        """ Resets the entries values to the default values """
        self.type_var_s.set(language["ADD"][3])
        self.path_var_s.set("")
        self.selected_path_label_s.configure(text="")
        self.name_var_s.set("")

    def select_path_s(self):
        """ Asks a new path to select """
        path = tl.askfile(language["ADD"][6], [".url", ".exe", ".lnk"], os.path.normpath(os.path.expanduser("~/Desktop")))
        if path != "" and path is not None:  # not cancelled
            self.path_var_s.set(path)
            self.selected_path_label_s.configure(text=path)
            if self.name_var_s.get() == "":
                self.name_var_s.set(gd.detect_name(path))

    def validate_s(self):
        """ Function to assign to a button, verify the entries to add a new game / bonus to the launcher """
        if self.type_var_s.get() == language["ADD"][3]:  # game
            app_type = "game"
        else:  # bonus
            app_type = "bonus"
        path = self.path_var_s.get()
        name = self.name_var_s.get()
        if name != "":
            if check_name(name):
                if os.path.exists(path):
                    if path.endswith(".lnk"):
                        shell = win32com.client.Dispatch("WScript.Shell")
                        shortcut = shell.CreateShortCut(path)
                        target_path = shortcut.Targetpath
                        if not os.path.isdir(target_path):
                            path = target_path
                        else:
                            path = None
                    if path is None:
                        tl.showwarning(language["ADD"][0], language["ADD"][11])
                    elif name not in apps:
                        app_format = gi.get_type_file(path)
                        if app_format == "exe":
                            icon_path = gi.get_icon_from_exe(path, f"icons/{name}")
                        elif app_format == "steam" or app_format == "uplay":
                            if os.path.abspath(os.path.dirname(path)) != os.path.abspath("url shortcuts") and os.path.basename(path) == f"{name}.url":
                                path = shutil.copy2(path, f"url shortcuts/{name}.url")
                            icon_path = gi.get_icon_steam_uplay(path, f"icons/{name}")
                        elif app_format == "epic":
                            if os.path.abspath(os.path.dirname(path)) != os.path.abspath("url shortcuts") and os.path.basename(path) == f"{name}.url":
                                path = shutil.copy2(path, f"url shortcuts/{name}.url")
                            icon_path = gi.get_icon_epic(path, f"icons/{name}")
                        else:  # unknown / error
                            tl.showwarning(language["ADD"][0], language["ADD"][10])
                            icon_path = ""
                        if icon_path is None:
                            tl.showwarning(language["ADD"][0], language["ADD"][10])
                            icon_path = ""
                        apps[name] = [app_type, "not favorite", ".", path, icon_path]
                        write_csv(apps, "apps.csv")
                        self.reset_entries_s()
                        show_message(language["ADD"][12], 3000)
                        apps_tab.reload_apps(False)
                        self.reload()
                    else:
                        tl.showwarning(language["ADD"][0], language["ADD"][9])
                else:  # path does not exist
                    tl.showwarning(language["ADD"][0], language["ADD"][7])
            else:
                tl.showwarning(language["ADD"][0], language["ADD"][13])
        else:
            tl.showwarning(language["ADD"][0], language["ADD"][14])

    def reset_entries_c(self):
        self.reload()
        self.name_var_c.set("")

    def validate_c(self):
        """ Function to assign to a button, verify the entries to add a new configuration / folder to the launcher """
        name = self.name_var_c.get()
        if name != "":
            if check_name(name):
                if name not in apps:
                    selected_apps = []
                    for widget in self.apps_to_add_frame_c.winfo_children():
                        if widget.get():
                            selected_apps.append(widget.cget("text").replace("\n", ""))
                    if selected_apps:
                        apps[name] = ["config", "not favorite", ".", "", selected_apps]
                        write_csv(apps, "apps.csv")
                        self.reset_entries_c()
                        show_message(language["ADD"][22], 3000)
                        apps_tab.reload_apps(False)
                    else:
                        tl.showwarning(language["ADD"][0], language["ADD"][21])
                else:
                    tl.showwarning(language["ADD"][0], language["ADD"][9])
            else:
                tl.showwarning(language["ADD"][0], language["ADD"][13])
        else:
            tl.showwarning(language["ADD"][0], language["ADD"][20])

    def add_folder(self):
        """ Function assigned to a button, when called, asks for a folder containing games to add to the launcher """
        folder = tl.askdir(language["ADD"][23], initialdir=os.path.normpath(os.path.expanduser("~/Desktop")))
        if folder is not None:
            files_list = []
            for item in os.listdir(folder):
                if os.path.isfile(os.path.join(folder, item)):
                    if gi.get_type_file(os.path.join(folder, item)) != "unknown":  # valid file
                        files_list.append(item)
                    elif item.endswith(".lnk"):
                        shell = win32com.client.Dispatch("WScript.Shell")
                        shortcut = shell.CreateShortCut(os.path.join(folder, item))
                        target_path = shortcut.Targetpath
                        if os.path.isfile(target_path) and target_path.endswith(".exe"):
                            files_list.append(item)

            if files_list:
                toplevel = ctk.CTkToplevel()
                toplevel.title(language["ADD"][23])
                toplevel.geometry("300x450")

                label = ctk.CTkLabel(toplevel, text=language["ADD"][24])
                scrollable_frame = ctk.CTkScrollableFrame(toplevel)
                validate_button = ctk.CTkButton(toplevel, text=language["ADD"][1], command=lambda: self.add_folder_validation(scrollable_frame, toplevel))
                cancel_button = ctk.CTkButton(toplevel, text=language["APPS"][32], command=toplevel.destroy)

                label.pack(side="top", padx=3, pady=3)
                scrollable_frame.pack(expand=True, fill="both", side="top", pady=3)
                validate_button.pack(expand=True, fill="both", side="right", padx=3, pady=3)
                cancel_button.pack(expand=True, fill="both", side="left", padx=3, pady=3)

                # fill the scrollable frame with the games
                for x in range(len(files_list)):
                    checkbox = ctk.CTkCheckBox(scrollable_frame, text=".".join(files_list[x].split(".")[:-1]), onvalue=os.path.join(folder, files_list[x]))  # using the onvalue argument to transfer the absolute path to the add_folder_validation method (I know I should not do that but it works)
                    checkbox.select()
                    checkbox.grid(row=x, column=0, sticky="w", padx=2, pady=3)
            else:  # files_list empty
                tl.showinfo(language["ADD"][23], language["ADD"][27])

    def add_folder_validation(self, frame: ctk.CTkScrollableFrame, toplevel: ctk.CTkToplevel):
        selected_list = []
        for children in frame.winfo_children():
            if children.get():  # selected
                selected_list.append(children.cget("onvalue"))
        toplevel.destroy()
        if not selected_list:
            return

        if tl.askyesno(language["ADD"][23], language["ADD"][29]):  # add in a folder
            while True:
                folder = tl.askstring(language["ADD"][23], language["ADD"][30], allow_none=False)
                if folder is None:
                    folder = "."
                    break
                elif folder in apps:
                    tl.showwarning(language["ADD"][23], language["ADD"][9])
                elif folder == ".":
                    tl.showwarning(language["APPS"][48], language["APPS"][50])
                else:
                    apps[folder] = ["folder", "not favorite", "."]
                    break
        else:
            folder = "."

        for path in selected_list:
            name = ".".join(os.path.basename(path).split(".")[:-1])
            if name in apps:
                if tl.askyesno(language["ADD"][23], f"{name}{language["ADD"][25]}"):
                    while True:
                        name = tl.askstring(language["ADD"][23], language["ADD"][26])
                        if name in apps and name is not None:
                            tl.showwarning(language["ADD"][23], language["ADD"][9])
                        else:
                            break
                else:
                    name = None
            if name is None:  # user canceled renaming
                continue

            if path.endswith(".lnk"):
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(path)
                path = shortcut.Targetpath

            app_format = gi.get_type_file(path)
            if app_format == "exe":
                icon_path = gi.get_icon_from_exe(path, f"icons/{name}")
            elif app_format == "steam" or app_format == "uplay":
                if os.path.abspath(os.path.dirname(path)) != os.path.abspath("url shortcuts") and os.path.basename(path) == f"{name}.url":
                    path = shutil.copy2(path, f"url shortcuts/{name}.url")
                icon_path = gi.get_icon_steam_uplay(path, f"icons/{name}")
            elif app_format == "epic":
                if os.path.abspath(os.path.dirname(path)) != os.path.abspath("url shortcuts") and os.path.basename(path) == f"{name}.url":
                    path = shutil.copy2(path, f"url shortcuts/{name}.url")
                icon_path = gi.get_icon_epic(path, f"icons/{name}")
            else:  # unknown / error
                icon_path = ""
            if icon_path is None:
                icon_path = ""
            apps[name] = ["game", "not favorite", folder, path, icon_path]

        write_csv(apps, "apps.csv")
        self.reset_entries_s()
        show_message(language["ADD"][28], 3000)
        apps_tab.reload_apps(False)
        self.reload()


class UpdatesTab:
    """ Updates tab containing the functionalities to update the launcher or its plugins """
    def __init__(self):
        self.has_to_reload = ctk.BooleanVar(root_frame, False)
        self.has_to_reload.trace_add("write", self.reload)

        # update variables
        self.launcher_has_to_update = False  # set to True if the launcher has to be updated
        self.updating = False  # set to True if something is currently updating

        # ctk variables
        self.active = False
        self.top_frame = ctk.CTkFrame(root_frame)
        self.title_label = ctk.CTkLabel(self.top_frame, text=language["UPDATES"][0], font=head_font)
        self.refresh_button = ctk.CTkButton(self.top_frame, text=language["UPDATES"][1], command=self.check_updates)
        self.title_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.refresh_button.grid(row=0, column=1, padx=15, pady=5)

        self.launcher_title = ctk.CTkLabel(root_frame, text=language["UPDATES"][7], font=subhead_font)
        self.launcher_state_label = ctk.CTkLabel(root_frame, text=language["UPDATES"][5])
        self.launcher_button = ctk.CTkButton(root_frame, text=language["UPDATES"][4], command=self.update_launcher, state="disabled")

        self.check_updates()

    def show(self):
        if not self.active:
            hide_all()
            self.active = True
            self.top_frame.grid(row=0, column=0, padx=10, pady=10, sticky="w", columnspan=3)
            self.launcher_title.grid(row=1, column=0, padx=10, pady=20)
            self.launcher_state_label.grid(row=1, column=1, padx=10, pady=20, sticky="w")
            self.launcher_button.grid(row=1, column=2, padx=10, pady=20, sticky="w")

    def hide(self):
        if self.active:
            self.active = False
            self.top_frame.grid_forget()
            self.launcher_title.grid_forget()
            self.launcher_state_label.grid_forget()
            self.launcher_button.grid_forget()

    def reload_page(self):
        """ Reconfigures every widget, allows to change language """
        self.title_label.configure(text=language["UPDATES"][0])
        self.refresh_button.configure(text=language["UPDATES"][1])

        self.launcher_title.configure(text=language["UPDATES"][7])
        self.launcher_button.configure(text=language["UPDATES"][4])

        self.has_to_reload.set(True)

    def check_updates(self):
        """ Starts the refreshing process to know what updates are available """
        if "updater: checking updates" not in [thread.name for thread in threading.enumerate()]:  # not already refreshing
            self.launcher_state_label.configure(text=language["UPDATES"][2])
            self.launcher_button.configure(state="disabled")

            thread = threading.Thread(target=self._check_updates, name="updater: checking updates", daemon=True)
            thread.start()

    def _check_updates(self):
        """ Checks for updates and reloads the tab when it's done """
        self.git_versions = up.check_versions(["launcher", "updater"], params["branch"])
        self.has_to_reload.set(True)

    def reload(self, *args):
        """ Reloads the tab and resets self.has_to_reload to False """
        if self.has_to_reload.get():
            self.launcher_has_to_update = False

            if self.git_versions == "connexion error":
                self.launcher_state_label.configure(text=f"{language["UPDATES"][5]} {language["UPDATES"][6]}")
                self.launcher_button.configure(state="disabled")
            else:
                # launcher
                if installing:
                    self.launcher_state_label.configure(text=language["UPDATES"][14])
                    self.launcher_button.configure(state="disabled")
                elif _version < self.git_versions["launcher"] or (self.git_versions["updater"] != "unknown" and os.path.isfile("APY! Launcher Updater.exe") and up.get_file_version("APY! Launcher Updater.exe") < self.git_versions["updater"]):
                    self.launcher_state_label.configure(text=language["UPDATES"][9])
                    self.launcher_button.configure(state="normal")
                    self.launcher_has_to_update = True
                else:
                    self.launcher_state_label.configure(text=language["UPDATES"][8])
                    self.launcher_button.configure(state="disabled")

            home_tab.reload()
            show_message(language["UPDATES"][3], 3000)

            self.has_to_reload.set(False)

    ''' code written for the APY! games update but will not be used until 2.2.0
    def add_to_queue(self, game: str):
        """Adds the given game to the games to update queue, starts the update if nothing is updating

        :param game: game to add to the queue
        """
        if not self.launcher_has_to_update:
            if game not in self.update_queue:
                self.update_queue.append(game)
                if not self.updating:
                    game_to_update = self.update_queue.pop(0)
                    if self.update_queue:
                        text = language["UPDATES"][14] + " "
                        for game in self.update_queue:
                            text += f"{game}, "
                        text = text.removesuffix(", ")
                        if len(text) > 88:
                            text = text[0:89]
                        self.following_label.configure(text=text)
                    else:
                        self.following_label.configure(text="")
                    self.update_game(game_to_update)
        else:
            tl.showwarning(language["UPDATES"][0], language["UPDATES"][15])
    '''

    def update_launcher(self):
        """ Launches the update for the launcher """
        global installing
        if os.path.isfile("APY! Launcher Updater.exe"):
            if self.git_versions["updater"] != "unknown":
                if up.get_file_version("APY! Launcher Updater.exe") < self.git_versions["updater"]:
                    if not installing:
                        installing = True
                        self.launcher_state_label.configure(text=language["UPDATES"][14])
                        self.launcher_button.configure(state="disabled")
                        threading.Thread(target=up.update_updater, args=[params["branch"], self.updater_update_finished]).start()
                elif _version < self.git_versions["launcher"]:
                    if tl.askyesno(language["UPDATES"][0], language["UPDATES"][10]):
                        if on_closing():
                            os.startfile("APY! Launcher Updater.exe")
        else:
            log_error(203, "Path to launcher updater not found: cannot update")
            tl.showerror(language["UPDATES"][0], language["UPDATES"][11])

    def updater_update_finished(self, code: str):
        global installing
        installing = False
        if code == "connexion error":
            tl.showwarning(language["UPDATES"][0], language["UPDATES"][6])
        elif code == "error":
            tl.showerror(language["UPDATES"][0], language["UPDATES"][15])
        self.has_to_reload.set(True)


class OptionsTab:
    """ Options tab containing the buttons to modify parameters of the launcher """
    def __init__(self):
        self.active = False
        self.title_label = ctk.CTkLabel(root_frame, text=language["OPTIONS"][0], font=head_font)
        self.save_button = ctk.CTkButton(root_frame, text=language["OPTIONS"][1], command=self.save)
        self.default_params_button = ctk.CTkButton(root_frame, text=language["OPTIONS"][2], command=self.set_default)

        self.general_buttons_frame = ctk.CTkFrame(root_frame)
        self.about_button = ctk.CTkButton(self.general_buttons_frame, text=language["OPTIONS"][5], command=self.about)
        self.uninstall_button = ctk.CTkButton(self.general_buttons_frame, text=language["OPTIONS"][18], command=self.uninstall)
        self.open_local_button = ctk.CTkButton(self.general_buttons_frame, text=language["OPTIONS"][21], command=self.open_local)
        self.show_logs_button = ctk.CTkButton(self.general_buttons_frame, text=language["OPTIONS"][23], command=self.show_logs)
        self.about_button.grid(row=0, column=0, padx=5, pady=10)
        self.uninstall_button.grid(row=1, column=0, padx=5, pady=10)
        self.open_local_button.grid(row=2, column=0, padx=5, pady=10)
        self.show_logs_button.grid(row=3, column=0, padx=5, pady=10)

        self.language_frame = ctk.CTkFrame(root_frame)
        self.language_label = ctk.CTkLabel(self.language_frame, text=language["OPTIONS"][11])
        self.language_variable = ctk.StringVar(root_frame, value=params["language"])
        self.language_menu = ctk.CTkOptionMenu(self.language_frame, values=[file.removesuffix(".lng") for file in os.listdir("lng files") if file.endswith(".lng") and is_lng_file_valid(f"lng files/{file}")], variable=self.language_variable)
        self.language_label.grid(row=0, column=0, padx=7, pady=7)
        self.language_menu.grid(row=0, column=1, padx=7, pady=7)

        self.size_frame = ctk.CTkFrame(root_frame)
        self.size_label = ctk.CTkLabel(self.size_frame, text=language["OPTIONS"][13])
        self.size_variable = ctk.StringVar(root_frame, value=params["size"])
        self.size_entry = ctk.CTkEntry(self.size_frame, textvariable=self.size_variable)
        self.size_label.grid(row=0, column=0, padx=7, pady=7)
        self.size_entry.grid(row=0, column=1, padx=7, pady=7)

        self.default_filter_frame = ctk.CTkFrame(root_frame)
        filter_values = [language["APPS"][1], language["APPS"][2], language["APPS"][3], language["APPS"][4], language["APPS"][5], language["APPS"][24], language["APPS"][25]]
        self.default_filter_label = ctk.CTkLabel(self.default_filter_frame, text=language["OPTIONS"][16])
        self.default_filter_variable = ctk.StringVar(root_frame, filter_values[params["defaultfilter"]])
        self.default_filter_menu = ctk.CTkOptionMenu(self.default_filter_frame, values=filter_values, variable=self.default_filter_variable)
        self.default_filter_label.grid(row=0, column=0, padx=7, pady=7)
        self.default_filter_menu.grid(row=0, column=1, padx=7, pady=7)

        self.theme_frame = ctk.CTkFrame(root_frame)
        if params["appearance"] == "dark":
            self.theme_variable = ctk.BooleanVar(root_frame, False)
        else:
            self.theme_variable = ctk.BooleanVar(root_frame, True)
        self.theme_button = ctk.CTkSwitch(self.theme_frame, text=language["OPTIONS"][12], variable=self.theme_variable, onvalue=True, offvalue=False)
        self.theme_button.grid(row=0, column=0, padx=7, pady=7)

        self.stoplauncher_frame = ctk.CTkFrame(root_frame)
        if params["stoplauncherwhengame"]:
            self.stoplauncher_variable = ctk.BooleanVar(root_frame, True)
        else:
            self.stoplauncher_variable = ctk.BooleanVar(root_frame, False)
        self.stoplauncher_button = ctk.CTkCheckBox(self.stoplauncher_frame, text=language["OPTIONS"][17], variable=self.stoplauncher_variable)
        self.stoplauncher_button.grid(row=0, column=0, padx=7, pady=7)

        self.branch_frame = ctk.CTkFrame(root_frame)
        if params["branch"] == "main":
            self.branch_variable = ctk.BooleanVar(root_frame, False)
        else:
            self.branch_variable = ctk.BooleanVar(root_frame, True)
        self.branch_switch = ctk.CTkSwitch(self.branch_frame, text=language["OPTIONS"][26], variable=self.branch_variable)
        self.branch_switch.grid(row=0, column=0, padx=7, pady=7)

    def show(self):
        if not self.active:
            hide_all()
            self.active = True
            self.title_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            self.save_button.grid(row=1, column=0, pady=20, padx=5)
            self.default_params_button.grid(row=1, column=1)
            self.general_buttons_frame.grid(row=1, column=2, padx=50, pady=20, rowspan=4, sticky="n")
            self.language_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="w")
            self.size_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="w")
            self.default_filter_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="w")
            self.theme_frame.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="w")
            self.stoplauncher_frame.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="w")
            self.branch_frame.grid(row=7, column=0, columnspan=2, padx=10, pady=10, sticky="w")

    def hide(self):
        if self.active:
            self.active = False
            self.title_label.grid_forget()
            self.save_button.grid_forget()
            self.default_params_button.grid_forget()
            self.general_buttons_frame.grid_forget()
            self.language_frame.grid_forget()
            self.size_frame.grid_forget()
            self.default_filter_frame.grid_forget()
            self.theme_frame.grid_forget()
            self.stoplauncher_frame.grid_forget()
            self.branch_frame.grid_forget()

    def reload_page(self):
        """ Reconfigures every widget, allows to change language """
        self.title_label.configure(text=language["OPTIONS"][0])
        self.save_button.configure(text=language["OPTIONS"][1])
        self.default_params_button.configure(text=language["OPTIONS"][2])
        self.about_button.configure(text=language["OPTIONS"][5])
        self.uninstall_button.configure(text=language["OPTIONS"][18])
        self.open_local_button.configure(text=language["OPTIONS"][21])
        self.show_logs_button.configure(text=language["OPTIONS"][23])

        self.language_label.configure(text=language["OPTIONS"][11])

        self.size_label.configure(text=language["OPTIONS"][13])

        filter_values = [language["APPS"][1], language["APPS"][2], language["APPS"][3], language["APPS"][4], language["APPS"][5], language["APPS"][24], language["APPS"][25]]
        self.default_filter_label.configure(text=language["OPTIONS"][16])
        self.default_filter_variable.set(filter_values[params["defaultfilter"]])
        self.default_filter_menu.configure(values=filter_values)

        self.theme_button.configure(text=language["OPTIONS"][12])

        self.stoplauncher_button.configure(text=language["OPTIONS"][17])

        self.branch_switch.configure(text=language["OPTIONS"][26])

    @staticmethod
    def set_default():
        """ Asks the user if the parameters should be reset to the default values (except language and branch) """
        if tl.askyesno(language["OPTIONS"][0], language["OPTIONS"][3]):
            params["appearance"] = "dark"
            ctk.set_appearance_mode("dark")
            params["size"] = "1280x720"
            params["defaultfilter"] = 0
            params["stoplauncherwhengame"] = False
            params["lastgame"] = ""
            home_tab.reload()
            write_params(params)
            win.geometry("1280x720")
            reload_window(language["WINDOW"][5])
            show_message(language["OPTIONS"][4], 3000)

    def save(self):
        """ Reads the entered parameters, saves them and reapply them """
        global language

        if self.theme_variable.get():
            params["appearance"] = "light"
            ctk.set_appearance_mode("light")
        else:
            params["appearance"] = "dark"
            ctk.set_appearance_mode("dark")

        size = self.size_variable.get()
        if "x" in size:
            x, y = size.split("x", 1)
            if x.isdigit() and y.isdigit():
                if int(x) >= 1000 and int(y) >= 600:
                    params["size"] = size
                    win.geometry(size)
                else:
                    tl.showwarning(language["OPTIONS"][0], f"{language["OPTIONS"][15]}1000x600")
            else:
                tl.showwarning(language["OPTIONS"][0], language["OPTIONS"][14])
        else:
            tl.showwarning(language["OPTIONS"][0], language["OPTIONS"][14])

        filter_values = [language["APPS"][1], language["APPS"][2], language["APPS"][3], language["APPS"][4], language["APPS"][5], language["APPS"][24], language["APPS"][25]]
        params["defaultfilter"] = filter_values.index(self.default_filter_variable.get())

        params["stoplauncherwhengame"] = int(self.stoplauncher_variable.get())

        if not self.branch_variable.get():  # main branch
            params["branch"] = "main"
        else:  # Development branch
            if params["branch"] == "main":  # not already selected
                if tl.askyesno(language["OPTIONS"][0], language["OPTIONS"][27]):
                    params["branch"] = "Development"
                else:
                    params["branch"] = "main"
            else:
                params["branch"] = "Development"

        params["language"] = self.language_variable.get()
        language = load_language(params["language"])
        tl._language = language["DIALOGS"]  # changing toplevel widgets language

        write_params(params)
        reload_window(language["WINDOW"][5])
        show_message(language["OPTIONS"][4], 3000)

    @staticmethod
    def about():
        """ Shows a popup showing the version of the launcher and link to GitHub repository """
        tl.showinfo(language["OPTIONS"][5], f"{language["OPTIONS"][6]} {_version}\n"
                                            f"{language["OPTIONS"][7]} fastattack\n"
                                            f"{language["OPTIONS"][8]}\n"
                                            f"{language["OPTIONS"][9]}\n"
                                            f"{language["OPTIONS"][10]} https://github.com/fastattackv/APY-launcher\n"
                                            f"{language["OPTIONS"][25]}")

    @staticmethod
    def uninstall():
        if tl.askyesno(language["OPTIONS"][18], language["OPTIONS"][19]):
            if os.path.isfile("APY! Launcher Uninstaller.exe") and os.path.isfile("APY!_Launcher_Uninstaller.bat"):
                if on_closing():
                    os.startfile("APY! Launcher Uninstaller.exe")
            else:
                log_error(204, "Path to launcher uninstaller not found: cannot uninstall")
                tl.showerror(language["OPTIONS"][18], language["OPTIONS"][20])

    @staticmethod
    def open_local():
        os.startfile(os.getcwd())

    @staticmethod
    def show_logs():
        toplevel = ctk.CTkToplevel()
        toplevel.title(language["OPTIONS"][22])
        toplevel.geometry("700x400")
        win.after(200, lambda: toplevel.iconbitmap(tl.get_resource_path("launcher data/launcher_icon.ico")))  # wait at least 200ms because else it doesn't work
        win.after(100, lambda: toplevel.lift())  # wait at least 100ms because else it doesn't work

        textbox = ctk.CTkTextbox(toplevel)
        if os.path.isfile("APY launcher logs.log"):
            with open("APY launcher logs.log", "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = ""
        if content != "":
            textbox.insert("1.0", content)
        else:
            textbox.insert("1.0", language["OPTIONS"][24])
        textbox.configure(state="disabled")
        textbox.pack(expand=True, fill="both")


# defining tabs
home_tab = HomeTab()
apps_tab = AppsTab()
single_app_tab = SingleAppTab()
add_game_tab = AddGameTab()
updates_tab = UpdatesTab()
options_tab = OptionsTab()

# defining top frame
top_frame = ctk.CTkFrame(win, fg_color="transparent")

tabs = ctk.CTkSegmentedButton(top_frame, values=[language["WINDOW"][1], language["WINDOW"][2], language["WINDOW"][3], language["WINDOW"][4], language["WINDOW"][5]], command=change_tab)
tabs.set(language["WINDOW"][1])
tabs.grid(row=0, column=0, sticky="w")

show_message_label = ctk.CTkLabel(top_frame, text="")

top_frame.grid(row=0, column=0, sticky="nw")

# check for messages
if len(sys.argv) > 1:
    for arg in sys.argv[1:]:
        if arg.startswith("updatedfrom="):
            v = arg.split("=", 1)[1]
            break
    else:
        v = None
else:
    v = None
threading.Thread(target=lambda version=v: home_tab.show_all_launcher_messages(version), name="checking for messages", daemon=True).start()

# launching main window
home_tab.show()
win.bind("<Configure>", change_size)

win.mainloop()
