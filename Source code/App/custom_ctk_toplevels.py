"""
This file contains custom widgets / toplevel for the APY! launcher

Copyright (C) 2024  fastattack

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

See the license in the COPYING file or at <https://www.gnu.org/licenses/>.
"""

import customtkinter as ctk
import winsound
import os
import sys
from PIL import Image
from typing import Literal, Optional, Union, Tuple

_language = [
    'Entering value',
    'Please enter a value',
    'Please enter an integer',
    'Please enter a decimal number',
    'Cannot cancel, please enter a value',
    'Creating directory',
    'Enter the name of the directory to create',
    'The directory will be created in:',
    'The given name already exists, please enter another one',
    'Ok',
    'Cancel',
    'Entering path',
    'Please select a path',
    'Cannot cancel, please select a path',
    'Yes',
    'No'
]  # set to english by default, change this variable to change the language used in error messages


def join_paths(path: str, *paths: str) -> str:
    """Joins the given paths and returns the joined path

    :param path: first path to join
    :param paths: other paths to add
    :return: final path
    """
    return os.path.join(path, *paths).replace("\\", "/")


def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev (.py) and for PyInstaller (.exe) """
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class FileExplorer(ctk.CTkFrame):
    def __init__(self,
                 master: any,
                 responsetype: Literal["file", "directory"],

                 # file explorer parameters
                 filetypes: list[str] = None,
                 initialdir: str = None,
                 initialfile: str = None,

                 # customtkinter widget parameters
                 width: int = 200,
                 height: int = 200,
                 corner_radius: Optional[Union[int, str]] = None,
                 border_width: Optional[Union[int, str]] = None,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,

                 background_corner_colors: Union[Tuple[Union[str, Tuple[str, str]]], None] = None,
                 overwrite_preferred_drawing_method: Union[str, None] = None,
                 **kwargs):
        """File explorer widget to select a path that already contains scrollbars, see ctk.CTkFrame for widget arguments

        :param responsetype: type of the path to select ("file" / "directory")
        :param filetypes: extensions of the files that can be selected (ex: [".txt", ".csv"]), None if a directory should be selected or if all files can be selected
        :param initialdir: directory to start the selection from, if both initialdir and initialfile are None, the initialdir will be the current directory
        :param initialfile: path of the file selected at the start of the search
        """
        # checking arguments
        if responsetype not in ["file", "directory"]:
            raise ValueError(f"responsetype should be \"file\" or \"directory\", not {responsetype}")
        if initialdir is not None and initialfile is not None:
            raise ValueError(f"Cannot use initialdir and initialfile at the same time, set only one")
        if initialdir is not None and not os.path.isdir(initialdir):
            raise ValueError(f"Path of initialdir is unknown: {initialdir}")
        if initialfile is not None:
            if responsetype != "file":
                raise ValueError("Cannot use initialfile is responsetype is directory")
            if not os.path.isfile(initialfile):
                raise ValueError(f"Path of initialfile is unknown: {initialfile}")
            if filetypes is not None and initialfile.split(".")[-1] not in filetypes:
                raise ValueError(f"initialfile extension is not in filetypes: {initialfile.split(".")[-1]}")

        # creating widget
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color, border_color,
                         background_corner_colors, overwrite_preferred_drawing_method, **kwargs)

        self.response_type = responsetype
        self.filetypes = filetypes
        self.change_path = True  # if set to false, the tracing on self.selected_path will be disabled

        if initialdir is not None:
            self.path_to_show = ctk.StringVar(self, value=initialdir)  # always a directory, path to show in the explorer
            self.selected_path = ctk.StringVar(self, value=initialdir)  # selected path by the user
        elif initialfile is not None:
            self.path_to_show = ctk.StringVar(self, value=os.path.dirname(initialfile))
            self.selected_path = ctk.StringVar(self, value=initialfile)
        else:
            self.path_to_show = ctk.StringVar(self, value=os.getcwd())
            self.selected_path = ctk.StringVar(self, value=os.getcwd())
        self.selected_path.trace_add("write", self._user_path_changed)

        self.folder_image = ctk.CTkImage(Image.open(get_resource_path("launcher data/folder_light.png")), Image.open(get_resource_path("launcher data/folder_dark.png")))
        self.file_image = ctk.CTkImage(Image.open(get_resource_path("launcher data/file_light.png")), Image.open(get_resource_path("launcher data/file_dark.png")))

        self.canvas = ctk.CTkCanvas(self, width=width - 16, height=height - 54, highlightthickness=0)
        if fg_color == "transparent":
            self.canvas.configure(bg=self._apply_appearance_mode(self.cget("bg")))
        else:
            self.canvas.configure(bg=self._apply_appearance_mode(self.cget("fg_color")))

        self.explorer_frame = ctk.CTkFrame(self.canvas, width=width - 16, height=height - 54, fg_color=fg_color)

        self.back_button = ctk.CTkButton(self, image=ctk.CTkImage(Image.open(get_resource_path("launcher data/back_arrow_light.png")), Image.open(get_resource_path("launcher data/back_arrow_dark.png"))), text="", command=self._move_back, width=35)
        self.path_entry = ctk.CTkEntry(self, textvariable=self.selected_path, width=width - 96)
        self.create_dir_button = ctk.CTkButton(self, image=ctk.CTkImage(Image.open(get_resource_path("launcher data/new_folder_light.png")), Image.open(get_resource_path("launcher data/new_folder_dark.png"))), text="", command=self._create_directory, width=35)
        self.y_scrollbar = ctk.CTkScrollbar(self, height=height - 38, command=self.canvas.yview)
        self.x_scrollbar = ctk.CTkScrollbar(self, orientation="horizontal", width=width - 16, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.y_scrollbar.set)
        self.after(100, lambda: self.canvas.configure(xscrollcommand=self.x_scrollbar.set))  # you have to bind the other scrollbar at least 50ms after the first one, idk why but it works

        self.back_button.grid(row=0, column=0)
        self.path_entry.grid(row=0, column=1, padx=5, pady=5)
        self.create_dir_button.grid(row=0, column=2)
        self.canvas.grid(row=1, column=0, columnspan=3)
        self.y_scrollbar.grid(row=1, column=3, rowspan=2)
        self.x_scrollbar.grid(row=2, column=0, columnspan=3)

        self.canvas.create_window((1, 1), window=self.explorer_frame, anchor="nw")

        self.explorer_frame.bind("<Configure>", self._configure_frame)
        self.canvas.bind("<MouseWheel>", self._mousewheel)
        self.explorer_frame.bind("<MouseWheel>", self._mousewheel)

        self._fill_explorer()

    def _configure_frame(self, event):
        """ Handles the event when self.explorer_frame is configured """
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _mousewheel(self, event):
        """ Handles the mousewheel event on the explorer_frame """
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _reset_scrolling(self):
        """ Resets the scrolling of the explorer_frame to the beginning """
        self.canvas.yview_moveto(0)
        self.canvas.xview_moveto(0)

    def _move_back(self):
        """ Moves to the parent directory """
        self.change_path = False
        self.selected_path.set(os.path.dirname(self.path_to_show.get()))
        self.change_path = True
        self.path_to_show.set(os.path.dirname(self.path_to_show.get()))
        self._empty_explorer()
        self._fill_explorer()

    def _create_directory(self):
        """ Creates a new directory at the self.path_to_show location """
        while True:
            name = askstring(_language[5], f"{_language[6]}\n{_language[7]} {self.path_to_show.get()}", allow_none=False)
            if name is None:
                break
            elif os.path.exists(join_paths(self.path_to_show.get(), name)):
                showwarning(_language[5], _language[8])
            else:
                os.mkdir(join_paths(self.path_to_show.get(), name))
                self.path_to_show.set(join_paths(self.path_to_show.get(), name))
                self.change_path = False
                self.selected_path.set(join_paths(self.path_to_show.get()))
                self.change_path = True
                self._empty_explorer()
                self._fill_explorer()
                break

    def _select(self, path: str):
        """ Changes the self.selected_path to the given path """
        self.change_path = False
        self.selected_path.set(path)
        self.change_path = True

    def _move_to(self, path: str):
        """ Changes the current directory to the given path """
        self.path_to_show.set(path)
        self.change_path = False
        self.selected_path.set(path)
        self.change_path = True
        self._empty_explorer()
        self._fill_explorer()

    def _empty_explorer(self):
        """ Empties the explorer_frame """
        for children in self.explorer_frame.winfo_children():
            children.destroy()

    def _fill_explorer(self):
        """ Fills the explorer_frame with the files at self.path_to_show """
        row = 0
        path = self.path_to_show.get()
        if os.path.isdir(path):
            for item in os.listdir(path):
                if os.path.isdir(join_paths(path, item)):  # directory
                    label = ctk.CTkLabel(self.explorer_frame, text=f"  {item}", compound="left", image=self.folder_image)
                    label.bind("<Button-1>", lambda event, p=os.path.normpath(join_paths(path, item)): self._select(p))  # left click
                    label.bind("<Double-Button-1>", lambda event, p=join_paths(path, item): self._move_to(p))  # double left click
                    label.bind("<MouseWheel>", self._mousewheel)
                    label.grid(row=row, column=0, sticky="w", padx=3, pady=3)
                else:  # file
                    if not self.response_type == "directory":
                        if self.filetypes is None or self.filetypes is not None and f".{item.split(".")[-1]}" in self.filetypes:
                            label = ctk.CTkLabel(self.explorer_frame, text=f"  {item}", compound="left", image=self.file_image)
                            label.bind("<Button-1>", lambda event, p=os.path.normpath(join_paths(path, item)): self._select(p))  # left click
                            label.bind("<MouseWheel>", self._mousewheel)
                            label.grid(row=row, column=0, sticky="w", padx=3, pady=3)
                row += 1
            self._reset_scrolling()

    def _user_path_changed(self, *args):
        """ Handles the event when self.selected_path is modified """
        if self.change_path:
            if os.path.isdir(self.selected_path.get()) and self.selected_path.get() != self.path_to_show.get():
                if not self.selected_path.get().endswith(" "):
                    self.path_to_show.set(self.selected_path.get())
                    self._empty_explorer()
                    self._fill_explorer()
            elif os.path.isfile(self.selected_path.get()) and os.path.dirname(self.selected_path.get()) != self.path_to_show.get():  # path to show changed
                if not os.path.dirname(self.selected_path.get()).endswith(" "):
                    self.path_to_show.set(os.path.dirname(self.selected_path.get()))
                    self._empty_explorer()
                    self._fill_explorer()

    def get_path(self):
        """Returns the selected path

        :return: selected path, "" if no paths were selected
        """
        if self.response_type == "file" and os.path.isfile(self.selected_path.get()):
            return self.selected_path.get()
        elif self.response_type == "directory" and os.path.isdir(self.selected_path.get()):
            return self.selected_path.get()
        else:
            return ""


class Filedialog(ctk.CTkToplevel):
    def __init__(self, responsetype: Literal["file", "directory"], title: str, filetypes: list[str] = None,
                 initialdir: str = None, initialfile: str = None, allow_cancel=True, allow_kill=True):
        """Creates a filedialog instance to ask for a file / directory

        :param responsetype: type of the selected response: "file" / "directory"
        :param title: title of the widget
        :param filetypes: extension of the file to enter: ("text", ".txt"), None if the response should be a directory
        :param initialdir: initial directory to start the search from, None if initialfile is not None
        :param initialfile: initial file selected
        :param allow_cancel: if set to False, the user will not be allowed to cancel
        :param allow_kill: if set to False, the user will not be allowed to close the window
        """
        self.path = None
        self.allow_cancel = allow_cancel
        self.allow_kill = allow_kill

        super().__init__()
        self.lift()  # lift window on top
        self.attributes("-topmost", True)  # stay on top
        self.grab_set()  # make other windows not clickable

        self.title(title)
        self.after(200, lambda: self.iconbitmap(get_resource_path("launcher data/launcher_icon.ico")))
        self.geometry("400x550")
        self.resizable(False, False)

        self.protocol("WM_DELETE_WINDOW", self._kill_event)

        self.explorer = FileExplorer(self, responsetype, filetypes, initialdir, initialfile, width=400, height=512)
        self.ok_button = ctk.CTkButton(self, text=_language[9], command=self._ok_event)
        self.cancel_button = ctk.CTkButton(self, text=_language[10], command=self._cancel_event)

        self.explorer.grid(row=1, column=0, columnspan=2)
        self.ok_button.grid(row=2, column=0, padx=5, pady=5)
        self.cancel_button.grid(row=2, column=1, padx=5, pady=5)

        self.bind("<Return>", self._ok_event)
        self.bind("<Escape>", self._cancel_event)

    def _ok_event(self, event=None):
        path = self.explorer.get_path()
        if path != "":
            self.path = path
            self.grab_release()
            self.destroy()
        else:
            showwarning(_language[11], _language[12])

    def _cancel_event(self, event=None):
        if self.allow_cancel:
            self.path = None
            self.grab_release()
            self.destroy()
        else:
            showwarning(_language[11], _language[13])

    def _kill_event(self, event=None):
        if self.allow_kill:
            self.path = None
            self.grab_release()
            self.destroy()
        else:
            showwarning(_language[11], _language[13])

    def get_response(self) -> str | None:
        """Waits until the dialog is closed and returns the path the user selected or None if the user cancelled
        """
        self.master.wait_window(self)
        return self.path


class Message(ctk.CTkToplevel):
    def __init__(self, title: str, message: str, typ: Literal["info", "warning", "error"], sound=True, *args, **kwargs):
        """TopLevel widget already configured for displaying messages

        :param title: title of the toplevel widget
        :param message: message to show
        :param typ: type of message to show ("info" / "warning" / "error")
        :param sound: optional: if set to True (True by default), the beep windows sound will be played as the message
            shows
        :param args: args for ctk.CTkToplevel
        :param kwargs: kwargs for ctk.CTkToplevel
        """
        super().__init__(*args, **kwargs)
        self.lift()  # lift window on top
        self.attributes("-topmost", True)  # stay on top
        self.resizable(False, False)
        self.grab_set()  # make other windows not clickable

        self.title(title)
        self.after(200, lambda: self.iconbitmap(get_resource_path("launcher data/launcher_icon.ico")))

        if typ == "info":
            pil_image = Image.open(get_resource_path("launcher data/info.png"))
            ctk_image = ctk.CTkImage(pil_image, pil_image, (85, 85))
            self.image = ctk.CTkLabel(self, text="", image=ctk_image, width=85, height=85)
            self.image.grid(row=0, column=0, padx=10, pady=15)
            pil_image.close()
        elif typ == "warning":
            pil_image = Image.open(get_resource_path("launcher data/warning.png"))
            ctk_image = ctk.CTkImage(pil_image, pil_image, (85, 85))
            self.image = ctk.CTkLabel(self, text="", image=ctk_image, width=85, height=85)
            self.image.grid(row=0, column=0, padx=10, pady=15)
            pil_image.close()
        elif typ == "error":
            pil_image = Image.open(get_resource_path("launcher data/error.png"))
            ctk_image = ctk.CTkImage(pil_image, pil_image, (85, 85))
            self.image = ctk.CTkLabel(self, text="", image=ctk_image, width=85, height=85)
            self.image.grid(row=0, column=0, padx=10, pady=15)
            pil_image.close()

        self.label = ctk.CTkLabel(self, text=message, font=ctk.CTkFont(size=15))
        self.label.grid(row=0, column=1, padx=10, pady=15)

        self.ok_button = ctk.CTkButton(self, text=_language[9], command=self.ok)
        self.ok_button.grid(row=1, column=0, columnspan=2, padx=10, pady=15)

        if sound:
            if typ == "error":
                winsound.MessageBeep(16)
            else:
                winsound.MessageBeep()

        self.bind("<Return>", self.ok)

    def ok(self, event=None):
        self.grab_release()
        self.destroy()

    def wait_end(self):
        """When called, waits until the message is closed
        """
        self.master.wait_window(self)


class AskValue(ctk.CTkInputDialog):
    def __init__(self, typ: Literal["str", "int", "float"], allow_none=True, allow_cancel=True, allow_kill=True, *args, **kwargs):
        """Modified instance of CTkInputDialog, allows verifying entered values

        :param typ: type of the value to enter, should be "str", "int" or "float"
        :param allow_none: if set to False, the user will not be allowed to enter "" (only useful for entering str type)
        :param allow_cancel: if set to False, the user will not be allowed to cancel
        :param allow_kill: if set to False, the user will not be allowed to quit the window
        :param args: args for CTkInputDialog
        :param kwargs: kwargs for CTkInputDialog
        """
        super().__init__(*args, **kwargs)
        self.after(200, lambda: self.iconbitmap(get_resource_path("launcher data/launcher_icon.ico")))
        self.type = typ
        self.allow_none = allow_none
        self.allow_cancel = allow_cancel
        self.allow_kill = allow_kill

    # overrides _ok_event method to add verification
    def _ok_event(self, event=None):
        value = self._entry.get()
        if self.type == "str":
            if not self.allow_none and value == "":
                showwarning(_language[0], _language[1])
            else:  # data is verified
                self._user_input = value
                self.grab_release()
                self.destroy()
        elif self.type == "int":
            if not value.isnumeric():
                showwarning(_language[0], _language[2])
            else:  # data is verified
                self._user_input = value
                self.grab_release()
                self.destroy()
        elif self.type == "float":
            try:
                value = float(value)
            except ValueError:
                showwarning(_language[0], _language[3])
            else:  # data is verified
                self._user_input = value
                self.grab_release()
                self.destroy()
        else:
            self._user_input = value
            self.grab_release()
            self.destroy()

    # overrides _on_closing method to add verification
    def _on_closing(self):
        if not self.allow_kill:
            showwarning(_language[0], _language[4])
        else:
            self.grab_release()
            self.destroy()

    # overrides _cancel_event method to add verification
    def _cancel_event(self):
        if not self.allow_cancel:
            showwarning(_language[0], _language[4])
        else:
            self.grab_release()
            self.destroy()


class AskDialog(ctk.CTkToplevel):
    def __init__(self, title: str, message: str, *args, **kwargs):
        """TopLevel widget already configured to ask true / false

        :param title: title of the toplevel widget
        :param message: message to show
        :param args: args for ctk.CTkToplevel
        :param kwargs: kwargs for ctk.CTkToplevel
        """
        super().__init__(*args, **kwargs)
        self.lift()  # lift window on top
        self.attributes("-topmost", True)  # stay on top
        self.resizable(False, False)
        self.grab_set()  # make other windows not clickable

        self.title(title)
        self.after(200, lambda: self.iconbitmap(get_resource_path("launcher data/launcher_icon.ico")))

        self.label = ctk.CTkLabel(self, text=message, font=ctk.CTkFont(size=15))
        self.label.grid(row=0, column=0, columnspan=2, padx=10, pady=15)

        self.yes_button = ctk.CTkButton(self, text=_language[14], command=self.yes)
        self.yes_button.grid(row=1, column=0, padx=10, pady=15)

        self.no_button = ctk.CTkButton(self, text=_language[15], command=self.no)
        self.no_button.grid(row=1, column=1, padx=10, pady=15)

        self.response = None

        self.bind("<Return>", self.yes)
        self.bind("<Escape>", self.no)

    def yes(self, event=None):
        self.response = True
        self.grab_release()
        self.destroy()

    def no(self, event=None):
        self.response = False
        self.grab_release()
        self.destroy()

    def get_response(self) -> bool | None:
        """Waits until the dialog is closed and returns the response the user gave
        """
        self.master.wait_window(self)
        return self.response


class LauncherDirectoryExplorer(ctk.CTkFrame):
    def __init__(self,
                 master: any,

                 # explorer parameters
                 content: dict,
                 initialdir: list = None,

                 # customtkinter widget parameters
                 width: int = 200,
                 height: int = 200,
                 corner_radius: Optional[Union[int, str]] = None,
                 border_width: Optional[Union[int, str]] = None,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,

                 background_corner_colors: Union[Tuple[Union[str, Tuple[str, str]]], None] = None,
                 overwrite_preferred_drawing_method: Union[str, None] = None,
                 **kwargs):
        """LauncherDirectoryExplorer widget to select a directory in the APY! launcher. The widgets already contains scrollbars, see ctk.CTkFrame for widget arguments

        :param content: dict of dicts containing the content of the explorer (ex: {"parent folder 1": {"children folder 1": {}}, "parent folder 2": {"children folder 2": {}, "children folder 3": {}}})
        :param initialdir: path directory to start the selection from, if set to []: will start from the root directory
        """
        # creating widget
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color, border_color,
                         background_corner_colors, overwrite_preferred_drawing_method, **kwargs)

        self.content = content

        if initialdir:
            if self._exists(initialdir[-1], initialdir[0:-1]):
                self.path_to_show = initialdir
                self.selected_path = initialdir
                self.selected_path_text = ctk.StringVar(value=self.convert_path_in_text(initialdir))
            else:
                raise ValueError(f"The given initialdir does not exist: {initialdir}")
        else:
            self.path_to_show = []
            self.selected_path = []
            self.selected_path_text = ctk.StringVar()

        self.folder_image = ctk.CTkImage(Image.open(get_resource_path("launcher data/folder_light.png")),
                                         Image.open(get_resource_path("launcher data/folder_dark.png")))

        self.canvas = ctk.CTkCanvas(self, width=width - 16, height=height - 54, highlightthickness=0)
        if fg_color == "transparent":
            self.canvas.configure(bg=self._apply_appearance_mode(self.cget("bg")))
        else:
            self.canvas.configure(bg=self._apply_appearance_mode(self.cget("fg_color")))

        self.explorer_frame = ctk.CTkFrame(self.canvas, width=width - 16, height=height - 54, fg_color=fg_color)

        self.back_button = ctk.CTkButton(self, image=ctk.CTkImage(
            Image.open(get_resource_path("launcher data/back_arrow_light.png")),
            Image.open(get_resource_path("launcher data/back_arrow_dark.png"))), text="", command=self._move_back,
                                         width=35)
        self.path_entry = ctk.CTkEntry(self, textvariable=self.selected_path_text, width=width - 65, state="disabled")
        self.path_entry.xview("end")
        self.y_scrollbar = ctk.CTkScrollbar(self, height=height - 38, command=self.canvas.yview)
        self.x_scrollbar = ctk.CTkScrollbar(self, orientation="horizontal", width=width - 16, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.y_scrollbar.set)
        self.after(100, lambda: self.canvas.configure(
            xscrollcommand=self.x_scrollbar.set))  # you have to bind the other scrollbar at least 50ms after the first one, idk why but it works

        self.back_button.grid(row=0, column=0)
        self.path_entry.grid(row=0, column=1, padx=5, pady=5)
        self.canvas.grid(row=1, column=0, columnspan=3)
        self.y_scrollbar.grid(row=1, column=3, rowspan=2)
        self.x_scrollbar.grid(row=2, column=0, columnspan=3)

        self.canvas.create_window((1, 1), window=self.explorer_frame, anchor="nw")

        self.explorer_frame.bind("<Configure>", self._configure_frame)
        self.canvas.bind("<MouseWheel>", self._mousewheel)
        self.explorer_frame.bind("<MouseWheel>", self._mousewheel)

        self._fill_explorer()

    @staticmethod
    def convert_path_in_text(path: list) -> str:
        """Converts the given launcher path in text to be shown

        :param path: APY! Launcher path to convert in text
        :return: converted path
        """
        if path:
            text = ""
            for item in path:
                text += f"{item} -> "
            return text[0:-4]
        else:
            return ""

    def _configure_frame(self, event):
        """ Handles the event when self.explorer_frame is configured """
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _mousewheel(self, event):
        """ Handles the mousewheel event on the explorer_frame """
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _show_path_text(self, path: list):
        self.selected_path_text.set(self.convert_path_in_text(path))
        self.path_entry.xview("end")

    def _exists(self, directory: str, path: list = None) -> bool:
        """Checks if the given folder exists at the current path_to_show. Also checks if the given path exists

        :param directory: item to check for
        :param path: can optionally be set to the path to check at
        :return: True if the item exists, False otherwise
        """
        if path is None:
            path = self.path_to_show

        content = self.content.copy()
        for item in path:
            if item in content:
                content = content[item]
            else:
                return False
        if directory in content:
            return True
        else:
            return False

    def _reset_scrolling(self):
        """ Resets the scrolling of the explorer_frame to the beginning """
        self.canvas.yview_moveto(0)
        self.canvas.xview_moveto(0)

    def _move_back(self):
        """ Moves to the parent directory """
        if self.path_to_show:
            self.path_to_show.pop(-1)
            self.selected_path = self.path_to_show.copy()
            self._show_path_text(self.path_to_show)
            self._empty_explorer()
            self._fill_explorer()

    def _select(self, item: str):
        """ Changes the self.selected_path to the given path """
        if self._exists(item):
            self.selected_path = self.path_to_show.copy() + [item]
            self._show_path_text(self.selected_path)

    def _move_to(self, item: str):
        """ Changes the current directory to the given path """
        if self._exists(item):
            self.path_to_show.append(item)
            self.selected_path = self.path_to_show.copy()
            self._show_path_text(self.path_to_show)
            self._empty_explorer()
            self._fill_explorer()

    def _empty_explorer(self):
        """ Empties the explorer_frame """
        for children in self.explorer_frame.winfo_children():
            children.destroy()

    def _fill_explorer(self):
        """ Fills the explorer_frame with the files at self.path_to_show """
        row = 0
        content = self.content
        for item in self.path_to_show:
            if item in content:
                content = content[item]
            else:
                return False

        for item in content:
            label = ctk.CTkLabel(self.explorer_frame, text=f"  {item}", compound="left", image=self.folder_image)
            label.bind("<Button-1>", lambda event, p=item: self._select(p))  # left click
            label.bind("<Double-Button-1>", lambda event, p=item: self._move_to(p))  # double left click
            label.bind("<MouseWheel>", self._mousewheel)
            label.grid(row=row, column=0, sticky="w", padx=3, pady=3)
            row += 1

        self._reset_scrolling()

    def get_path(self):
        """Returns the selected path

        :return: selected path or an empty list if no paths were selected
        """
        return self.selected_path


class LauncherDirectoryDialog(ctk.CTkToplevel):
    def __init__(self, title: str, content: dict, initialdir: str = None, allow_cancel=True, allow_kill=True):
        """Creates a filedialog instance to ask for a launcher directory

        :param title: title of the widget
        :param content: content of the explorer !DOES NOT GET CHECKED!
        :param initialdir: initial directory to start the search from, None if initialfile is not None
        :param allow_cancel: if set to False, the user will not be allowed to cancel
        :param allow_kill: if set to False, the user will not be allowed to close the window
        """
        self.path = None
        self.allow_cancel = allow_cancel
        self.allow_kill = allow_kill

        super().__init__()
        self.lift()  # lift window on top
        self.attributes("-topmost", True)  # stay on top
        self.grab_set()  # make other windows not clickable

        self.title(title)
        self.after(200, lambda: self.iconbitmap(get_resource_path("launcher data/launcher_icon.ico")))
        self.geometry("400x550")
        self.resizable(False, False)

        self.protocol("WM_DELETE_WINDOW", self._kill_event)

        self.explorer = LauncherDirectoryExplorer(self, content, initialdir=initialdir, width=400, height=512)
        self.ok_button = ctk.CTkButton(self, text=_language[9], command=self._ok_event)
        self.cancel_button = ctk.CTkButton(self, text=_language[10], command=self._cancel_event)

        self.explorer.grid(row=1, column=0, columnspan=2)
        self.ok_button.grid(row=2, column=0, padx=5, pady=5)
        self.cancel_button.grid(row=2, column=1, padx=5, pady=5)

        self.bind("<Return>", self._ok_event)
        self.bind("<Escape>", self._cancel_event)

    def _ok_event(self, event=None):
        path = self.explorer.get_path()
        if path != "":
            self.path = path
            self.grab_release()
            self.destroy()
        else:
            showwarning(_language[11], _language[12])

    def _cancel_event(self, event=None):
        if self.allow_cancel:
            self.path = None
            self.grab_release()
            self.destroy()
        else:
            showwarning(_language[11], _language[13])

    def _kill_event(self, event=None):
        if self.allow_kill:
            self.path = None
            self.grab_release()
            self.destroy()
        else:
            showwarning(_language[11], _language[13])

    def get_response(self) -> str | None:
        """Waits until the dialog is closed and returns the path the user selected or None if the user cancelled
        """
        self.master.wait_window(self)
        return self.path


def showinfo(title: str, message: str):
    """Shows a TopLevel widget to tell an information

    :param title: title of the dialog
    :param message: message in the dialog
    """
    m = Message(title, message, "info")
    m.wait_end()


def showwarning(title: str, message: str):
    """Shows a TopLevel widget to tell a warning

    :param title: title of the dialog
    :param message: message in the dialog
    """
    m = Message(title, message, "warning")
    m.wait_end()


def showerror(title: str, message: str):
    """Shows a TopLevel widget to tell an error

    :param title: title of the dialog
    :param message: message in the dialog
    """
    m = Message(title, message, "error")
    m.wait_end()


def askfile(title: str, filetypes: list[str] = None, initialdir: str = None, initialfile: str = None, allow_cancel=True, allow_kill=True) -> str | None:
    """Asks for a file to select

    :param title: title of the widget
    :param filetypes: extension of the file to enter: [".png", ".txt"], None if the response should be a directory
    :param initialdir: initial directory to start the search from, None if initialfile is not None
    :param initialfile: initial file selected
    :param allow_cancel: if set to False, the user will not be allowed to cancel / close the window
    :param allow_kill: if set to False, the user will not be allowed to quit the window
    :return: path of the selected file, None if the user cancelled
    """
    dialog = Filedialog("file", title, filetypes=filetypes, initialdir=initialdir, initialfile=initialfile, allow_cancel=allow_cancel, allow_kill=allow_kill)
    return dialog.get_response()


def askdir(title: str, initialdir: str = None, allow_cancel=True, allow_kill=True) -> str | None:
    """Asks for a directory / folder to select

    :param title: title of the widget
    :param initialdir: initial directory to start the search from
    :param allow_cancel: if set to False, the user will not be allowed to cancel / close the window
    :param allow_kill: if set to False, the user will not be allowed to quit the window
    :return: path of the selected directory, None if the user cancelled
    """
    dialog = Filedialog("directory", title, initialdir=initialdir, allow_cancel=allow_cancel, allow_kill=allow_kill)
    return dialog.get_response()


def asklauncherdir(title: str, content: dict, initialdir: str = None, allow_cancel=True, allow_kill=True) -> list[str] | None:
    """Asks for a launcher directory / folder to select

    :param title: title of the widget
    :param content: content of the explorer !DOES NOT GET CHECKED!
    :param initialdir: initial directory to start the search from
    :param allow_cancel: if set to False, the user will not be allowed to cancel / close the window
    :param allow_kill: if set to False, the user will not be allowed to quit the window
    :return: path of the selected launcher directory, None if the user cancelled
    """
    dialog = LauncherDirectoryDialog(title, content, initialdir=initialdir, allow_cancel=allow_cancel, allow_kill=allow_kill)
    return dialog.get_response()


def askyesno(title: str, message: str) -> bool | None:
    """Shows a TopLevel widget to ask a question

    :param title: title of the dialog
    :param message: message in the dialog
    :return: True if the "Yes" button was clicked, False if the "No" button was clicked, None if the dialog was closed
    """
    dialog = AskDialog(title, message)
    return dialog.get_response()


def askstring(title: str, message: str, allow_none=True, allow_cancel=True, allow_kill=True) -> str:
    """Asks a string from the user

    :param title: title of the TopLevel window
    :param message: message to show in the TopLevel window
    :param allow_none: optional: if set to False, the user will not be able to enter ""
    :param allow_cancel: optional: if set to False, the user will not be able to cancel/close the window
    :param allow_kill: if set to False, the user will not be allowed to quit the window
    :return: string entered by the user, None if the user canceled
    """
    dialog = AskValue("str", allow_none, allow_cancel, allow_kill, title=title, text=message)
    return dialog.get_input()


def askinteger(title: str, message: str, allow_cancel=True, allow_kill=True) -> int:
    """Asks an int from the user

    :param title: title of the TopLevel window
    :param message: message to show in the TopLevel window
    :param allow_cancel: if set to False, the user will not be able to cancel/close the window
    :param allow_kill: if set to False, the user will not be allowed to quit the window
    :return: int entered by the user, None if the user canceled
    """
    dialog = AskValue("int", allow_cancel=allow_cancel, allow_kill=allow_kill, title=title, text=message)
    return dialog.get_input()


def askfloat(title: str, message: str, allow_cancel=True, allow_kill=True) -> float:
    """Asks a string from the user

    :param title: title of the TopLevel window
    :param message: message to show in the TopLevel window
    :param allow_cancel: if set to False, the user will not be able to cancel/close the window
    :param allow_kill: if set to False, the user will not be allowed to quit the window
    :return: int entered by the user, None if the user canceled
    """
    dialog = AskValue("float", allow_cancel=allow_cancel, allow_kill=allow_kill, title=title, text=message)
    return dialog.get_input()
