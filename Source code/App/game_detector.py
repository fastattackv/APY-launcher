"""
This file contains functions to detect games in a folder or what games are installed on the system

Copyright (C) 2024  fastattack

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

See the license in the COPYING file or at <https://www.gnu.org/licenses/>.
"""

import os
import win32com.client


def detect_name(path: str) -> str:
    """Detects the name of a given application path

    :param path: path of the application to analyse
    :return: name of the application
    """
    name = path.split("\\")[-1].split("/")[-1]
    name = name.split(".")
    name = ".".join(name[0:-1])
    return name


def detect_games_in_folder(path: str, check_recursively=False, _lastdir="") -> list | str:
    """Detects the games in a given folder

    :param path: path of the directory to check
    :param check_recursively: optional, if set to True, the function will also search games in subdirectories
    :param _lastdir: DO NOT CHANGE THIS VARIABLE MANUALLY, contains the relative path to add before the games names
    :return: list of the detected games relative paths (to the given folder) or "invalid path" if path doesn't exist
    """
    if os.path.isdir(path):
        games = []
        for item in os.listdir(path):
            if os.path.isfile(os.path.join(path, item)):  # file
                if item.endswith(".url"):
                    with open(os.path.join(path, item), "r") as f:
                        lines = f.readlines()
                        for line in lines:
                            if line.startswith("URL=steam://rungameid/"):  # steam game
                                games.append(os.path.join(_lastdir, item))
                                break
                            elif line.startswith("URL=com.epicgames.launcher://apps/"):  # epicgames game
                                games.append(os.path.join(_lastdir, item))
                                break
                            elif line.startswith("URL=uplay://launch/"):  # uplay game
                                games.append(os.path.join(_lastdir, item))
                                break
                elif item.endswith(".lnk"):
                    shell = win32com.client.Dispatch("WScript.Shell")
                    shortcut = shell.CreateShortCut(os.path.join(path, item))
                    target_path = shortcut.Targetpath
                    if target_path.endswith(".exe"):
                        games.append(os.path.join(_lastdir, item))
                elif item.endswith(".exe"):
                    games.append(os.path.join(_lastdir, item))
            else:  # folder
                if check_recursively:
                    games.extend(detect_games_in_folder(os.path.join(path, item), True, os.path.join(_lastdir, item)))
        return games
    else:
        return "invalid path"
