"""
This file contains functions to extract icons from .url and .exe files for the APY! launcher
"""

import os
import shutil
import icoextract
from PIL import Image


def get_type_file(path: str) -> str:
    """Returns the type of the given file

    :param path: file to analyse
    :return: type of the file ("steam" / "epic" / "exe" / "unknown")
    """
    if os.path.isfile(path):
        if path.endswith(".exe"):
            return "exe"
        elif path.endswith(".url"):
            with open(path, "r") as f:
                lines = f.readlines()
                if len(lines) == 7 and lines[5].startswith("URL=steam://rungameid/"):
                    return "steam"
                elif len(lines) == 8 and lines[6].startswith("URL=com.epicgames.launcher://apps/"):
                    return "epic"
                else:
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
    :param destination: destination (file path) to copy the icon to without the format (.png or .ico)
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


def get_icon_steam(source: str, destination: str, png=True) -> str | None:
    """Extracts the icon from a .url steam file and copies it to the destination

    :param source: .url file to get the icon from
    :param destination: destination (file path) to copy the icon to without the format (.png or .ico)
    :param png: if set to True, converts the .ico file into a .png file
    :return: True if the icon was copied to the destination, else : False
    """
    if os.path.exists(source):
        try:
            with open(source, "r") as f:
                icon_path = f.readlines()[6].removeprefix("IconFile=").removesuffix("\n")
            if os.path.exists(icon_path):
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
    :param destination: destination (file path) to copy the icon to without the format (.png or .ico)
    :param png: if set to True, converts the .ico file into a .png file
    :return: path the icon was copied to, None if an error occurred
    """
    if os.path.exists(source):
        try:
            with open(source, "r") as f:
                exe_path = f.readlines()[7].removeprefix("IconFile=").removesuffix("\n")
            if os.path.exists(exe_path):
                return get_icon_from_exe(exe_path, destination, png)
            else:
                return None
        except:
            return None
    else:
        return None
