"""
This file contains functions to extract icons from .url and .exe files for the APY! launcher

Copyright (C) 2024  fastattack

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

See the license in the COPYING file or at <https://www.gnu.org/licenses/>.
"""

import os
import shutil
import icoextract
from PIL import Image


def get_type_file(path: str) -> str:
    """Returns the type of the given file

    :param path: file to analyse
    :return: type of the file ("steam" / "epic" / "uplay" / "exe" / "unknown")
    """
    if os.path.isfile(path):
        if path.endswith(".exe"):
            return "exe"
        elif path.endswith(".url"):
            with open(path, "r") as f:
                for line in f.readlines():
                    if line.startswith("URL=steam://rungameid/"):
                        return "steam"
                    elif line.startswith("URL=com.epicgames.launcher://apps/"):
                        return "epic"
                    elif line.startswith("URL=uplay://launch/"):
                        return "uplay"
                return "unknown"
        else:
            return "unknown"
    else:
        return "unknown"


def ico_to_png(source: str) -> str | None:
    """Replaces the given .ico file with the corresponding .png file

    :param source: .ico file to convert
    :return: path the icon was converted to, None if an error occurred
    """
    if os.path.exists(source):
        img = Image.open(source)
        destination = source.removesuffix(".ico") + ".png"
        img.save(destination)
        img.close()
        os.remove(source)
        return destination
    else:
        return None


def get_icon_from_exe(source: str, destination: str, png=True) -> str | None:
    """Extracts the icon from a .exe file and copies it to the destination

    :param source: .exe file to get the icon from
    :param destination: destination (file path) to copy the icon to WITHOUT the format (.png or .ico)
    :param png: if set to True, converts the .ico file into a .png file
    :return: path the icon was copied to, None if an error occurred
    """
    if os.path.isfile(source):
        try:
            extractor = icoextract.IconExtractor(source)
        except icoextract.NoIconsAvailableError:
            return None
        else:
            destination = destination + ".ico"
            extractor.export_icon(destination)
            if png:
                return ico_to_png(destination)
            else:
                return destination
    else:
        return None


def get_icon_steam_uplay(source: str, destination: str, png=True) -> str | None:
    """Extracts the icon from a .url steam or uplay file and copies it to the destination

    :param source: .url file to get the icon from
    :param destination: destination (file path) to copy the icon to WITHOUT the format (.png or .ico)
    :param png: if set to True, converts the .ico file into a .png file
    :return: path the icon was copied to, None if an error occurred or if no icon were found
    """
    if os.path.isfile(source):
        try:
            with open(source, "r") as f:
                for line in f.readlines():
                    if line.startswith("IconFile="):
                        icon_path = line.removeprefix("IconFile=").removesuffix("\n")
                        break
                else:  # did not find any icon
                    return None
            if os.path.isfile(icon_path):
                destination = destination + ".ico"
                shutil.copy2(icon_path, destination)
                if png:
                    return ico_to_png(destination)
                else:
                    return destination
            else:
                return None
        except:
            return None
    else:
        return None


def get_icon_epic(source: str, destination: str, png=True) -> str | None:
    """Extracts the icon from a .url epic games file and copies it to the destination

    :param source: .url file to get the icon from
    :param destination: destination (file path) to copy the icon to WITHOUT the format (.png or .ico)
    :param png: if set to True, converts the .ico file into a .png file
    :return: path the icon was copied to, None if an error occurred or if no icon were found
    """
    if os.path.isfile(source):
        try:
            with open(source, "r") as f:
                for line in f.readlines():
                    if line.startswith("IconFile="):
                        exe_path = line.removeprefix("IconFile=").removesuffix("\n")
                        break
                else:  # did not find any exe
                    return None
            if os.path.isfile(exe_path):
                return get_icon_from_exe(exe_path, destination, png)
            else:
                return None
        except:
            return None
    else:
        return None
