"""
This files contains functions that interacts with GitHub to download infos (versions) or applications

Copyright (C) 2024  fastattack

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

See the license in the COPYING file or at <https://www.gnu.org/licenses/>.
"""

import requests
import zipfile
import os
import shutil
import win32com.client


def get_file_version(path):
    """ Returns the version of the given file """
    information_parser = win32com.client.Dispatch("Scripting.FileSystemObject")
    version = information_parser.GetFileVersion(path)
    return version


def check_versions(apps_list: list, branch: str) -> dict[str, str] | str:
    """Returns the version of the given applications

    :param apps_list: list of the apps to retrieve the version of ("launcher" / )
    :param branch: branch to update from ("main" / "Development")
    :return: dict containing the retrieved versions / "unknown" if the game doesn't exist:
        {"launcher": "v2.0.0", "sudoku": "unknown"} or "connexion error" if a connexion error occurred
    """
    try:
        response = requests.get(f"https://github.com/fastattackv/APY-launcher/raw/{branch}/Downloads/Versions.txt")
    except requests.ConnectionError:
        return "connexion error"
    except requests.Timeout:
        return "connexion error"
    else:
        if response.status_code == 200:
            git_versions_dict = {a.split("=")[0]: a.split("=")[1] for a in response.text.split("\n") if a != ""}
            versions_dict = {}
            for app in apps_list:
                if app in git_versions_dict:
                    versions_dict[app] = git_versions_dict[app]
                else:
                    versions_dict[app] = "unknown"
            return versions_dict
        else:
            return "connexion error"


def check_for_launcher_message(branch: str) -> dict[int, str] | None:
    """Checks if there are messages available for the launcher

    :param branch: branch to update from ("main" / "Development")
    :return: dict containing the available messages ids and texts if there are messages, otherwise None
    """
    try:
        messages = requests.get(f"https://github.com/fastattackv/APY-launcher/raw/{branch}/Downloads/Messages/Message.txt")
    except requests.ConnectionError:
        return None
    except requests.Timeout:
        return None
    else:
        if messages.status_code == 200:
            messages = messages.text.split("&&")
            messages_dict = {int(message.split("\n", 1)[0]): message.split("\n", 1)[1].removesuffix("\n") for message in messages if message != ""}
            return messages_dict
        else:
            return None


def check_for_version_message(initial_version: str, current_version: str, branch: str) -> str | None:
    """Checks if there is a message available for the given version of the launcher

    :param initial_version: version the launcher was before update
    :param current_version: current version of the launcher
    :param branch: branch to update from ("main" / "Development")
    :return: available message if there is one, otherwise None
    """
    try:
        versions_list = requests.get(f"https://github.com/fastattackv/APY-launcher/raw/{branch}/Downloads/Versions%20list.txt")
        if versions_list.status_code == 200:
            versions_list = versions_list.text.split("\n")
            versions_to_check = [version for version in versions_list if initial_version < version <= current_version and version != ""]
            if versions_to_check:
                message = ""
                for version in reversed(versions_to_check):
                    response = requests.get(f"https://github.com/fastattackv/APY-launcher/raw/{branch}/Downloads/Messages/{version}.txt")
                    if response.status_code == 200:
                        message += response.text
                        message += "\n\n"
                    else:
                        return None
            else:
                return None
        else:
            return None
    except requests.ConnectionError:
        return None
    except requests.Timeout:
        return None
    else:
        return message


def update_updater(branch: str, callback_func):
    """Downloads the latest version of the updater and replaces the current version by the latest one

    :param branch: branch to update from ("main" / "Development")
    :param callback_func: function to call when the update is over. It should take an argument: the code to indicate how the update went ("ok", "up-to-date", "connexion error" or "error")
    """
    if not os.path.isfile("APY! Launcher Updater.exe"):
        callback_func("error")
        return
    versions = check_versions(["updater"], branch)
    if versions == "connexion error":
        callback_func("connexion error")
    elif versions["updater"] == "unknown":
        callback_func("error")
    else:
        if get_file_version("APY! Launcher Updater.exe") < versions["updater"]:
            try:
                response = requests.get(f"https://github.com/fastattackv/APY-launcher/raw/{branch}/Downloads/APY!%20Launcher%20Updater.zip", timeout=(5, 10))
            except requests.ConnectionError:
                callback_func("connexion error")
            except requests.Timeout:
                callback_func("connexion error")
            else:
                if response.status_code == 200:
                    with open("cache/APY! Launcher Updater.zip", "wb") as f:
                        f.write(response.content)
                    with zipfile.ZipFile("cache/APY! Launcher Updater.zip", "r") as f:
                        f.extractall("cache")
                    os.remove("APY! Launcher Updater.exe")
                    shutil.copy2("cache/APY! Launcher Updater.exe", "APY! Launcher Updater.exe")
                    os.remove("cache/APY! Launcher Updater.exe")
                    os.remove("cache/APY! Launcher Updater.zip")
                    callback_func("ok")
                else:
                    callback_func("error")
        else:
            callback_func("up-to-date")
