"""
This files contains functions that interacts with GitHub to download infos (versions) or applications
"""

import requests


def check_versions(apps_list: list) -> dict[str, str] | str:
    """Returns the version of the given applications

    :param apps_list: list of the apps to retrieve the version of ("launcher" / )
    :return: dict containing the retrieved versions / "unknown" if the game doesn't exist:
        {"launcher": "v2.0.0", "sudoku": "unknown"} or "connexion error" if a connexion error occurred
    """
    try:
        response = requests.get("https://github.com/fastattackv/APY-launcher/raw/main/Downloads/Versions.txt")
    except requests.ConnectionError:
        return "connexion error"
    except requests.Timeout:
        return "connexion error"
    else:
        git_versions_dict = {a.split("=")[0]: a.split("=")[1] for a in response.text.split("\n") if a != ""}
        versions_dict = {}
        for app in apps_list:
            if app in git_versions_dict:
                versions_dict[app] = git_versions_dict[app]
            else:
                versions_dict[app] = "unknown"
        return versions_dict
