"""
TODO:
    NEW:
        v2.1.0:
            - create configurations : launch multiple apps at the same time
            - fast configuration (auto detect new games / select a folder containing games)
            - make an order for the apps in the apps tab
            - folder in the apps tab
            - select a random game in all games / in a folder
            - sound when show_message ?
            - make apps more "separated" in the file explorer ?
            - make options more separated in the options tab
            - make show_message not move the other widgets
        v2.2.0:
            - install / update / uninstall APY! games
                - queue system
                - make button disabled when updating its game
                - make installer / updater
                - make cancel functionality
            - language system on launcher installers
        v2.3.0 / v3.0.0:
            - controller support
            - full screen func (like steam big picture)
    BUGS:
        - seemingly memory leak when reloading games tab (adding until a certain point and then resets)
"""

import customtkinter as ctk
from tkinter import Menu
import os
import datetime
import csv
from PIL import Image
import win32com.client
import threading

import get_icons as gi
import custom_ctk_toplevels as tl
import APY_launcher_updates as up


# global variables
_log = True  # write errors to log file, should be set to True when converting to .exe
_debug = False  # print errors, should be set to False when converting to .exe
_version = "2.0.0"
_language_separators_indexes = [0, 7, 15, 35, 51, 64, 86, 103]


# custom errors
class APYLauncherExceptions:
    class ParamMissing(Exception):
        def __init__(self, param):
            message = f"Parameter {param} is missing from the params file (Err301)"
            super().__init__(message)

    class LngFileMissing(Exception):
        def __init__(self):
            message = "Not found any valid language file to load (Err302)"
            super().__init__(message)


# Global functions
def log_error(error_code: int, message=""):
    """Logs errors in the log file / print the errors

    :param error_code: error code
    :param message: optional : message to write with the error code
    """
    if _log:
        if not os.path.exists("APY launcher logs.log"):
            with open("APY launcher logs.log", "x"):
                pass
        with open("APY launcher logs.log", "a") as f:
            f.write(f"{datetime.datetime.now()} : Err{error_code}, {message}\n")
    if _debug:
        print(f"{datetime.datetime.now()} : Err{error_code}, {message}")


def read_params(path="params.APYL") -> dict[str, str | int]:
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
                        if 0 <= a <= 4:
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
                else:
                    log_error(201, f"params file line unknown : \"{line}\"")
        for param in ["language", "appearance", "size", "defaultfilter", "stoplauncherwhengame", "lastgame"]:
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

    :param lang: language to load (without the .lng)
    :return: dict containing the loaded language
    """
    if os.path.exists(f"lng files/{lang}.lng") and is_lng_file_valid(f"lng files/{lang}.lng"):
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
        log_error(102, f"Could not find file {lang}.lng, searching for another file")
        for file in os.listdir("lng files"):
            if file.endswith(".lng"):
                if is_lng_file_valid(f"lng files/{file}"):
                    return load_language(file.removesuffix(".lng"))
        else:
            log_error(302, "Not found any valid lng files to load")
            raise APYLauncherExceptions.LngFileMissing()


def read_csv(path: str, typ: type) -> dict[str, list] | list[str]:
    """Reads the given file and returns the dict containing the apps infos, !doesn't check if the file exists!

    :param path: path of the file to read, the file must be a .csv file
    :param typ: type of the instance to return (list / dict)
    :return: dict containing the apps infos
    """
    if typ is dict:
        to_return = {}
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f, delimiter=",", quotechar='"', doublequote=True)
            for row in reader:
                to_return[row[0]] = row[1:]
        return to_return
    elif typ is list:
        to_return = []
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f, delimiter=",", quotechar='"', doublequote=True)
            for row in reader:
                to_return.extend(row)
        return to_return


def write_csv(to_save: dict | list, path: str):
    """Saves the given apps dictionary to the given file

    :param to_save: dict / list containing the infos to write to the file
    :param path: path of the file to write to
    """
    if type(to_save) is dict:
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=",", quotechar='"')
            for game, infos in to_save.items():
                to_write = infos.copy()
                to_write.insert(0, game)
                writer.writerow(to_write)
    elif type(to_save) is list:
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=",", quotechar='"')
            writer.writerow(to_save)


def launch(game, change_last_game=True):
    """Launches the given game

    :param game: game to execute
    :param change_last_game: if set to True, the param "lastgame" will be changed to the given game
    """
    if os.path.isfile(apps[game][2]):
        os.startfile(apps[game][2])
        if change_last_game:
            params["lastgame"] = game
            home_tab.reload()
            write_params(params)
        if params["stoplauncherwhengame"]:
            win.destroy()
    else:
        log_error(104, f"path {apps[game][2]} does not exist")
        tl.showwarning(language["APPS"][7], language["APPS"][8])


# ctk functions
def get_geometry() -> str:
    """Returns the current size of the window

    :return: current size of the window
    """
    return win.geometry().split("+", 1)[0]


def hide_all():
    """ Hides all the tabs """
    home_tab.hide()
    apps_tab.hide()
    add_game_tab.hide()
    updates_tab.hide()
    options_tab.hide()


def show_message(message: str, time: int):
    """Shows a message at the top of the windows for the given time

    :param message: message to show
    :param time: time to display the message (in ms)
    """
    label = ctk.CTkLabel(top_frame, text=message)
    label.after(time, lambda: label.destroy())
    label.grid(row=0, column=1, padx=10, sticky="w")


def reload_window(tab: str):
    """Deletes every widget and recreates them (allows to change language)

    :param tab: tab to change to after reload is done
    """
    global home_tab, apps_tab, add_game_tab, updates_tab, options_tab, tabs, top_frame
    hide_all()

    home_tab = HomeTab()
    apps_tab = AppsTab()
    add_game_tab = AddGameTab()
    updates_tab = UpdatesTab()
    options_tab = OptionsTab()

    home_tab.reload()

    top_frame.destroy()
    top_frame = ctk.CTkFrame(win, fg_color="transparent")

    tabs = ctk.CTkSegmentedButton(top_frame, values=[language["WINDOW"][1], language["WINDOW"][2], language["WINDOW"][3], language["WINDOW"][4], language["WINDOW"][5]], command=change_tab)
    tabs.set(tab)
    change_tab(tab)
    tabs.grid(row=0, column=0, sticky="w")

    top_frame.grid(row=0, column=0, columnspan=3, sticky="w")


def change_tab(tab):
    """Changes the active to tab to the given one

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
            apps_tab.reload_apps()


# ctk classes
class HomeTab:
    def __init__(self):
        self.active = False
        self.title_label = ctk.CTkLabel(win, text=language["HOME"][0], font=head_font)
        self.updates_label = ctk.CTkLabel(win, text=language["HOME"][1], font=subhead_font)
        self.update_launcher_label = ctk.CTkLabel(win, text=language["HOME"][2])
        self.last_game_label = ctk.CTkLabel(win, text=language["HOME"][5], font=subhead_font)
        if params["lastgame"] in apps:
            self.last_game_button = ctk.CTkButton(win, text=params["lastgame"], command=lambda a=params["lastgame"]: launch(a))
        else:
            self.last_game_button = ctk.CTkButton(win, text=language["HOME"][6], state="disabled")

    def show(self):
        if not self.active:
            hide_all()
            self.active = True
            self.title_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
            self.updates_label.grid(row=2, column=0, padx=10, pady=15, sticky="w")
            self.update_launcher_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
            self.last_game_label.grid(row=6, column=0, padx=10, pady=15, sticky="w")
            self.last_game_button.grid(row=7, column=0, padx=10, pady=5, sticky="w")

    def hide(self):
        if self.active:
            self.active = False
            self.title_label.grid_forget()
            self.updates_label.grid_forget()
            self.update_launcher_label.grid_forget()
            self.last_game_label.grid_forget()
            self.last_game_button.grid_forget()

    def reload(self):
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


class AppsTab:
    def __init__(self):
        self.active = False
        self.top_frame = ctk.CTkFrame(win)

        self.title_label = ctk.CTkLabel(self.top_frame, text=language["APPS"][0], font=head_font)

        filter_values = [language["APPS"][1], language["APPS"][2], language["APPS"][3], language["APPS"][4], language["APPS"][5]]
        self.filter_var = ctk.StringVar(self.top_frame, filter_values[params["defaultfilter"]])
        self.filter_menu = ctk.CTkOptionMenu(self.top_frame, values=filter_values, variable=self.filter_var, command=self.filter)

        self.search_label = ctk.CTkLabel(self.top_frame, text=language["APPS"][6])
        self.search_var = ctk.StringVar(self.top_frame)
        self.search_var.trace_add("write", self.search_modified)
        self.search_entry = ctk.CTkEntry(self.top_frame, textvariable=self.search_var)
        self.stop_search_button = ctk.CTkButton(self.top_frame, text="X", width=20, fg_color=('#F9F9FA', '#343638'), command=self.stop_search)

        self.title_label.grid(row=0, column=0, padx=5, pady=5)
        self.filter_menu.grid(row=0, column=1, padx=25, pady=5)
        self.search_label.grid(row=0, column=2, padx=5, pady=5)
        self.search_entry.grid(row=0, column=3, padx=0, pady=5)
        self.stop_search_button.grid(row=0, column=4, padx=5, pady=5)

        self.apps_frame = ctk.CTkScrollableFrame(win)

        self.title_label.after(100, lambda: self.reload_apps(False))

    def show(self):
        if not self.active:
            hide_all()
            self.active = True
            self.top_frame.grid(row=1, column=0, sticky="w", padx=10, pady=10, columnspan=3)
            self.reload_apps(True)

    def hide(self):
        if self.active:
            self.active = False
            self.top_frame.grid_forget()
            self.apps_frame.grid_forget()

    def reload_apps(self, grid=True):
        # get the apps to show
        search = self.search_var.get()
        filter = self.filter_var.get()
        if filter == language["APPS"][1]:  # no filter
            apps_to_load = {app: apps[app] for app in apps if app.lower().startswith(search.lower())}
        elif filter == language["APPS"][2]:  # favorites
            apps_to_load = {app: apps[app] for app in apps if app.lower().startswith(search.lower()) and apps[app][1] == "favorite"}
        elif filter == language["APPS"][3]:  # game
            apps_to_load = {app: apps[app] for app in apps if app.lower().startswith(search.lower()) and apps[app][0] == "game"}
        elif filter == language["APPS"][4]:  # bonus
            apps_to_load = {app: apps[app] for app in apps if app.lower().startswith(search.lower()) and apps[app][0] == "bonus"}
        elif filter == language["APPS"][5]:  # folder
            #apps_to_load = {app: apps_to_load[app] for app in apps_to_load.copy() if app.lower().startswith(search.lower()) and apps_to_load[app][0] == "folder"}
            apps_to_load = {}
        else:
            apps_to_load = apps.copy()

        # destroy widgets
        self.apps_frame.grid_forget()
        self.apps_frame.destroy()

        # create new widgets
        number_columns = int(get_geometry().split("x")[0]) // 320
        self.apps_frame = ctk.CTkScrollableFrame(win, width=int(get_geometry().split("x")[0]) - 23, height=int(get_geometry().split("x")[1]) - 107, fg_color="transparent")

        row = 0
        column = 0
        for app in apps_to_load:
            App(self.apps_frame, app).grid(row=row, column=column, ipadx=5, ipady=5, padx=5, pady=5)
            column += 1
            if column >= number_columns:
                column = 0
                row += 1

        if grid:
            self.apps_frame.grid(row=2, column=0, columnspan=4)

    def filter(self, *args):
        self.reload_apps()

    def search_modified(self, *args):
        self.reload_apps()

    def stop_search(self, *args):
        self.search_var.set("")
        self.reload_apps()


class App(ctk.CTkFrame):
    def __init__(self, master, name: str, drag=True):
        """Class to contain a game name, icon and path to show in the AppsTab

        :param master: master window for the frame
        :param name: name of the app
        :param drag: optional: if set to True, dragging will be activated
        """
        super().__init__(master)

        self.name = name

        if os.path.exists(apps[name][3]):  # icon path exists
            self.name_label = ctk.CTkLabel(self, text=name, font=subhead_font, image=ctk.CTkImage(Image.open(apps[name][3]), size=(85, 85)), compound="top")
        else:
            self.name_label = ctk.CTkLabel(self, text=name, font=subhead_font, image=ctk.CTkImage(Image.open(tl.get_resource_path("launcher data/question_mark_light.png")), Image.open(tl.get_resource_path("launcher data/question_mark_dark.png")), (85, 85)), compound="top")
        self.name_label.pack()
        self.name_label.bind("<Double-Button-1>", self.left_click)
        self.name_label.bind("<Button-3>", self.right_click)

        self.menu = Menu(master, tearoff=0)
        self.menu.add_command(label=language["APPS"][7], command=self.launch)
        if apps[name][1] == "not favorite":
            self.menu.add_command(label=language["APPS"][9], command=self.set_favorite)
        else:
            self.menu.add_command(label=language["APPS"][11], command=self.remove_favorite)
        self.menu.add_separator()
        self.menu.add_command(label=language["APPS"][13], command=self.rename)
        self.menu.add_command(label=language["APPS"][17], command=self.delete)

        if drag:
            self.dragging = False
            self.startX = 0
            self.startY = 0
            self.drag_start_x = 0
            self.drag_start_y = 0
            self.start_grid_coordinates = 0
            self.place_app = App(master, self.name, False)  # app to be placed for dragging
            self.name_label.bind("<Button-1>", self.drag_start)
            self.name_label.bind("<B1-Motion>", self.drag_motion)
            self.name_label.bind("<ButtonRelease-1>", self.drag_stop)

    def left_click(self, event):
        pass

    def right_click(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def launch(self):
        launch(self.name)

    def set_favorite(self):
        apps[self.name][1] = "favorite"
        write_csv(apps, "apps.csv")
        apps_tab.reload_apps()
        show_message(f"{self.name} {language["APPS"][10]}", 3000)

    def remove_favorite(self):
        apps[self.name][1] = "not favorite"
        write_csv(apps, "apps.csv")
        apps_tab.reload_apps()
        show_message(f"{self.name} {language["APPS"][12]}", 3000)

    def rename(self):
        while True:
            name = tl.askstring(language["APPS"][13], language["APPS"][14] + " " + self.name)
            if name is None:
                break
            else:
                if name in apps:
                    tl.showwarning(language["APPS"][13], language["APPS"][15])
                else:
                    if os.path.exists(apps[self.name][3]):
                        os.rename(apps[self.name][3], f"icons/{name}.png")
                        apps[self.name][3] = f"icons/{name}.png"
                    else:
                        log_error(106, f"Tried to rename the icon while renaming the game but its path did not exist: {apps[self.name][3]}")
                    apps[name] = apps[self.name]
                    del apps[self.name]
                    write_csv(apps, "apps.csv")
                    show_message(f"{self.name} {language["APPS"][16]} {name}", 3000)
                    self.name = name
                    self.name_label.configure(text=name)
                    apps_tab.search_modified()
                    break

    def delete(self):
        if tl.askyesno(language["APPS"][17], f"{language["APPS"][18]} {self.name}"):
            if os.path.exists(apps[self.name][3]):
                os.remove(apps[self.name][3])
            else:
                log_error(105, f"Tried to delete the icon while deleting the game but its path did not exist: {apps[self.name][3]}")
            del apps[self.name]
            write_csv(apps, "apps.csv")
            apps_tab.reload_apps()
            if params["lastgame"] == self.name:
                params["lastgame"] = ""
                write_params(params)
                home_tab.reload()

    def disable(self):
        """Grays out the app text
        """
        self.name_label.configure(text_color="gray")

    def enable(self):
        self.name_label.configure(text_color="white")

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
                    # modify the order of the apps
                    apps_tab.reload_apps()
            self.dragging = False


class AddGameTab:
    def __init__(self):
        self.active = False
        self.title_label = ctk.CTkLabel(win, text=language["ADD"][0], font=head_font)

        self.type_label = ctk.CTkLabel(win, text=language["ADD"][2])
        self.type_var = ctk.StringVar(win, language["ADD"][3])
        self.type_menu = ctk.CTkOptionMenu(win, variable=self.type_var, values=[language["ADD"][3], language["ADD"][4]], width=80)

        self.path_label = ctk.CTkLabel(win, text=language["ADD"][5])
        self.path_var = ctk.StringVar(win)
        self.selected_path_label = ctk.CTkLabel(win, text="")
        self.path_button = ctk.CTkButton(win, text=language["ADD"][6], command=self.select_path)

        self.name_label = ctk.CTkLabel(win, text=language["ADD"][8])
        self.name_var = ctk.StringVar(win)
        self.name_entry = ctk.CTkEntry(win, width=150, textvariable=self.name_var)

        self.validate_button = ctk.CTkButton(win, text=language["ADD"][1], command=self.validate)

    def show(self):
        if not self.active:
            hide_all()
            self.active = True
            self.title_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
            self.type_label.grid(row=2, column=0, pady=30, sticky="e")
            self.type_menu.grid(row=2, column=1)
            self.path_label.grid(row=3, column=0, pady=5)
            self.path_button.grid(row=3, column=1)
            self.selected_path_label.grid(row=4, column=0, columnspan=2)
            self.name_label.grid(row=5, column=0, pady=30)
            self.name_entry.grid(row=5, column=1)
            self.validate_button.grid(row=6, column=0, pady=20)

    def hide(self):
        if self.active:
            self.active = False
            self.title_label.grid_forget()
            self.type_label.grid_forget()
            self.type_menu.grid_forget()
            self.path_label.grid_forget()
            self.path_button.grid_forget()
            self.selected_path_label.grid_forget()
            self.name_label.grid_forget()
            self.name_entry.grid_forget()
            self.validate_button.grid_forget()

    def reset_entries(self):
        """Resets the entries values to the default values
        """
        self.type_var.set(language["ADD"][3])
        self.path_var.set("")
        self.selected_path_label.configure(text="")
        self.name_var.set("")

    def select_path(self):
        path = tl.askfile(language["ADD"][6], [".url", ".exe", ".lnk"], os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop'))
        if path != "" and path is not None:  # not cancelled
            self.path_var.set(path)
            self.selected_path_label.configure(text=path)

    def validate(self):
        """Function to assign to a button, verify the entries to add a new game to the launcher
        """
        if self.type_var.get() == language["ADD"][3]:  # game
            app_type = "game"
        else:  # bonus
            app_type = "bonus"
        path = self.path_var.get()
        name = self.name_var.get()
        if name != "":
            if len(name) <= 30:
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
                        elif app_format == "steam":
                            icon_path = gi.get_icon_steam(path, f"icons/{name}")
                        elif app_format == "epic":
                            icon_path = gi.get_icon_epic(path, f"icons/{name}")
                        else:  # unknown / error
                            tl.showwarning(language["ADD"][0], language["ADD"][10])
                            icon_path = ""
                        apps[name] = [app_type, "not favorite", path, icon_path]
                        write_csv(apps, "apps.csv")
                        self.reset_entries()
                        show_message(language["ADD"][12], 3000)
                        apps_tab.reload_apps(False)
                    else:
                        tl.showwarning(language["ADD"][0], language["ADD"][9])
                else:  # path does not exist
                    tl.showwarning(language["ADD"][0], language["ADD"][7])
            else:
                tl.showwarning(language["ADD"][0], language["ADD"][13])
        else:
            tl.showwarning(language["ADD"][0], language["ADD"][14])


class UpdatesTab:
    def __init__(self):
        self.has_to_reload = ctk.BooleanVar(win, False)
        self.has_to_reload.trace_add("write", self.reload)

        # update variables
        self.launcher_has_to_update = False  # set to True if the launcher has to be updated
        self.updating = False  # set to True if something is currently updating

        # ctk variables
        self.active = False
        self.top_frame = ctk.CTkFrame(win)
        self.title_label = ctk.CTkLabel(self.top_frame, text=language["UPDATES"][0], font=head_font)
        self.refresh_button = ctk.CTkButton(self.top_frame, text=language["UPDATES"][1], command=self.check_updates)
        self.title_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.refresh_button.grid(row=0, column=1, padx=15, pady=5)

        self.launcher_title = ctk.CTkLabel(win, text=language["UPDATES"][7], font=subhead_font)
        self.launcher_state_label = ctk.CTkLabel(win, text=language["UPDATES"][5])
        self.launcher_button = ctk.CTkButton(win, text=language["UPDATES"][4], command=self.update_launcher, state="disabled")

        self.check_updates()

    def show(self):
        if not self.active:
            hide_all()
            self.active = True
            self.top_frame.grid(row=1, column=0, padx=10, pady=10, sticky="w", columnspan=3)
            self.launcher_title.grid(row=2, column=0, padx=10, pady=20)
            self.launcher_state_label.grid(row=2, column=1, padx=10, pady=20, sticky="w")
            self.launcher_button.grid(row=2, column=2, padx=10, pady=20, sticky="w")

    def hide(self):
        if self.active:
            self.active = False
            self.top_frame.grid_forget()
            self.launcher_title.grid_forget()
            self.launcher_state_label.grid_forget()
            self.launcher_button.grid_forget()

    def check_updates(self):
        """ Starts the refreshing process to know what updates are available """
        if "updater: checking updates" not in [thread.name for thread in threading.enumerate()]:  # not already refreshing
            self.launcher_state_label.configure(text=language["UPDATES"][2])
            self.launcher_button.configure(state="disabled")

            thread = threading.Thread(target=self._check_updates, name="updater: checking updates", daemon=True)
            thread.start()

    def _check_updates(self):
        """ Checks for updates and reloads the tab when it's done """
        self.git_versions = up.check_versions(["launcher"])
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
                if _version < self.git_versions["launcher"]:
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

    @staticmethod
    def update_launcher():
        """ Launches the update for the launcher """
        if tl.askyesno(language["UPDATES"][0], language["UPDATES"][10]):
            if os.path.isfile("APY! Launcher Updater.exe"):
                os.startfile("APY! Launcher Updater.exe")
                win.destroy()
            else:
                log_error(203, "Path to launcher updater not found: cannot update")
                tl.showerror(language["UPDATES"][0], language["UPDATES"][11])


class OptionsTab:
    def __init__(self):
        self.active = False
        self.title_label = ctk.CTkLabel(win, text=language["OPTIONS"][0], font=head_font)
        self.save_button = ctk.CTkButton(win, text=language["OPTIONS"][1], command=self.save)
        self.default_params_button = ctk.CTkButton(win, text=language["OPTIONS"][2], command=self.set_default)
        self.about_button = ctk.CTkButton(win, text=language["OPTIONS"][5], command=self.about)

        self.language_label = ctk.CTkLabel(win, text=language["OPTIONS"][11])
        self.language_variable = ctk.StringVar(win, value=params["language"])
        self.language_menu = ctk.CTkOptionMenu(win, values=[file.removesuffix(".lng") for file in os.listdir("lng files") if file.endswith(".lng") and is_lng_file_valid(f"lng files/{file}")], variable=self.language_variable)

        if params["appearance"] == "dark":
            self.theme_variable = ctk.BooleanVar(win, False)
        else:
            self.theme_variable = ctk.BooleanVar(win, True)
        self.theme_button = ctk.CTkSwitch(win, text=language["OPTIONS"][12], variable=self.theme_variable, onvalue=True, offvalue=False)

        self.size_label = ctk.CTkLabel(win, text=language["OPTIONS"][13])
        self.size_variable = ctk.StringVar(win, value=params["size"])
        self.size_entry = ctk.CTkEntry(win, textvariable=self.size_variable)

        filter_values = [language["APPS"][1], language["APPS"][2], language["APPS"][3], language["APPS"][4], language["APPS"][5]]
        self.default_filter_label = ctk.CTkLabel(win, text=language["OPTIONS"][16])
        self.default_filter_variable = ctk.StringVar(win, filter_values[params["defaultfilter"]])
        self.default_filter_menu = ctk.CTkOptionMenu(win, values=filter_values, variable=self.default_filter_variable)

        if params["stoplauncherwhengame"]:
            self.stoplauncher_variable = ctk.BooleanVar(win, True)
        else:
            self.stoplauncher_variable = ctk.BooleanVar(win, False)
        self.stoplauncher_button = ctk.CTkCheckBox(win, text=language["OPTIONS"][17], variable=self.stoplauncher_variable)

        self.uninstall_button = ctk.CTkButton(win, text=language["OPTIONS"][18], command=self.uninstall)

    def show(self):
        if not self.active:
            hide_all()
            self.active = True
            self.title_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
            self.save_button.grid(row=2, column=0, pady=20)
            self.default_params_button.grid(row=2, column=1)
            self.about_button.grid(row=2, column=2, padx=50, pady=20)
            self.language_label.grid(row=3, column=0, padx=10, pady=20, sticky="e")
            self.language_menu.grid(row=3, column=1, padx=10, pady=20, sticky="w")
            self.theme_button.grid(row=6, column=0, columnspan=2, padx=10, pady=20)
            self.size_label.grid(row=4, column=0, padx=10, pady=20, sticky="e")
            self.size_entry.grid(row=4, column=1, padx=10, pady=20, sticky="w")
            self.default_filter_label.grid(row=5, column=0, padx=10, pady=20, sticky="e")
            self.default_filter_menu.grid(row=5, column=1, padx=10, pady=20, sticky="w")
            self.stoplauncher_button.grid(row=7, column=0, columnspan=2, padx=10, pady=20)
            self.uninstall_button.grid(row=3, column=2, padx=50, pady=20)

    def hide(self):
        if self.active:
            self.active = False
            self.title_label.grid_forget()
            self.save_button.grid_forget()
            self.default_params_button.grid_forget()
            self.about_button.grid_forget()
            self.language_label.grid_forget()
            self.language_menu.grid_forget()
            self.theme_button.grid_forget()
            self.size_label.grid_forget()
            self.size_entry.grid_forget()
            self.default_filter_label.grid_forget()
            self.default_filter_menu.grid_forget()
            self.stoplauncher_button.grid_forget()
            self.uninstall_button.grid_forget()

    @staticmethod
    def set_default():
        """Asks the user if the parameters should be reset to the default values (except the language)
        """
        if tl.askyesno(language["OPTIONS"][0], language["OPTIONS"][3]):
            params["appearance"] = "dark"
            ctk.set_appearance_mode("dark")
            params["size"] = "1380x800"
            params["defaultfilter"] = 0
            params["stoplauncherwhengame"] = False
            params["lastgame"] = ""
            home_tab.reload()
            write_params(params)
            win.geometry("1380x800")
            reload_window(language["WINDOW"][5])
            show_message(language["OPTIONS"][4], 3000)

    def save(self):
        """Reads the entered parameters, saves them and reapply them
        """
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
                if int(x) >= 650 and int(y) >= 600:
                    params["size"] = size
                    win.geometry(size)
                else:
                    tl.showwarning(language["OPTIONS"][0], language["OPTIONS"][15])
            else:
                tl.showwarning(language["OPTIONS"][0], language["OPTIONS"][14])
        else:
            tl.showwarning(language["OPTIONS"][0], language["OPTIONS"][14])

        filter_values = [language["APPS"][1], language["APPS"][2], language["APPS"][3], language["APPS"][4], language["APPS"][5]]
        params["defaultfilter"] = filter_values.index(self.default_filter_variable.get())

        params["stoplauncherwhengame"] = int(self.stoplauncher_variable.get())

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
                                            f"{language["OPTIONS"][7]}\n"
                                            f"{language["OPTIONS"][8]}\n"
                                            f"{language["OPTIONS"][9]}\n"
                                            f"{language["OPTIONS"][10]}")

    @staticmethod
    def uninstall():
        if tl.askyesno(language["OPTIONS"][18], language["OPTIONS"][19]):
            if os.path.isfile("APY! Launcher Uninstaller.exe") and os.path.isfile("APY!_Launcher_Uninstaller.bat"):
                os.startfile("APY! Launcher Uninstaller.exe")
                win.destroy()
            else:
                log_error(204, "Path to launcher uninstaller not found: cannot uninstall")
                tl.showerror(language["OPTIONS"][18], language["OPTIONS"][20])


# checking directories
if not os.path.isdir("cache"):
    os.mkdir("cache")
if not os.path.isdir("icons"):
    os.mkdir("icons")
if not os.path.isdir("lng files"):
    os.mkdir("lng files")

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
            log_error(302, "Not found any valid lng files to load")
            raise APYLauncherExceptions.LngFileMissing()
    params = {
        "language": language,
        "appearance": "dark",
        "size": "1300x800",
        "defaultfilter": 0,
        "stoplauncherwhengame": False,
        "lastgame": ""
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
    apps = read_csv("apps.csv", dict)
else:
    log_error(202, "apps.csv file not found, recreating one")
    with open("apps.csv", "x"):
        pass
    apps = {}

""" code written for the APY! games update but will not be used until 2.2.0
# reading installed APY! Games
APYGames = {}
for folder in os.listdir(".."):
    if os.path.isdir(os.path.join("..", folder)):
        if folder not in ["APY! Launcher"]:
            if "version.txt" in os.listdir(os.path.join("..", folder)):
                with open(os.path.join("..", folder, "version.txt")) as f:
                    APYGames[folder] = f.read()
"""

# defining window
win = ctk.CTk()
win.iconbitmap(tl.get_resource_path("launcher data/launcher_icon.ico"))
win.title(language["WINDOW"][0])
win.geometry(params["size"])
win.minsize(650, 600)
win_width, win_height = 0, 0

# defining ctk variables
head_font = ctk.CTkFont(size=30, weight="bold")
subhead_font = ctk.CTkFont(size=20, weight="bold")
bold_font = ctk.CTkFont(size=13, weight="bold")
normal_font = ctk.CTkFont(size=13)

# defining tabs
home_tab = HomeTab()
apps_tab = AppsTab()
add_game_tab = AddGameTab()
updates_tab = UpdatesTab()
options_tab = OptionsTab()

top_frame = ctk.CTkFrame(win, fg_color="transparent")

tabs = ctk.CTkSegmentedButton(top_frame, values=[language["WINDOW"][1], language["WINDOW"][2], language["WINDOW"][3], language["WINDOW"][4], language["WINDOW"][5]], command=change_tab)
tabs.set(language["WINDOW"][1])
tabs.grid(row=0, column=0, sticky="w")

top_frame.grid(row=0, column=0, columnspan=3, sticky="w")

# launching window
home_tab.show()
win.bind("<Configure>", change_size)

win.mainloop()
