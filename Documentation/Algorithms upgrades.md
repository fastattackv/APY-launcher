# Upgrades of algorithms used in the APY! Launcher explained

## Upgrade of the algorithm determining what apps should be shown in the apps tab

This algorithm is used in the `AppsTab.reload_apps()` method to determine what apps should be shown by analysing the search, active filter and active folder.

To determine what algorithm between the 2 methods below was better, I tested their speed with 2 different datasets

- 1st dataset: average time of 10 times 1,000,000 iterations for an apps dict of 4 elements
- 2st dataset: average time of 10 times 500,000 iterations for an apps dict of 9 elements


### 1st method
The first method consists of firstly creating a copy of the apps dict containing only the apps in the active folder and then determine which of these apps should be shown.

Its code was:

````python
if folder is None:
    temp_apps = apps.copy()
else:
    temp_apps = {app: apps[app] for app in apps[folder][2] if app in apps}

if active_filter == "no filter":  # no filter
    apps_to_load = {app: apps[app] for app in temp_apps if app.lower().startswith(search.lower()) and apps[app][1] != "hidden"}
elif active_filter == "favorites":  # favorites
    apps_to_load = {app: apps[app] for app in temp_apps if app.lower().startswith(search.lower()) and apps[app][1] == "favorite" and apps[app][1] != "hidden"}
elif active_filter == "game":  # game
    apps_to_load = {app: apps[app] for app in temp_apps if app.lower().startswith(search.lower()) and apps[app][0] == "game" and apps[app][1] != "hidden"}
elif active_filter == "bonus":  # bonus
    apps_to_load = {app: apps[app] for app in temp_apps if app.lower().startswith(search.lower()) and apps[app][0] == "bonus" and apps[app][1] != "hidden"}
elif active_filter == "folder":  # folder
    apps_to_load = {app: apps[app] for app in temp_apps if app.lower().startswith(search.lower()) and apps[app][0] == "folder" and apps[app][1] != "hidden"}
elif active_filter == "configs":  # configs
    apps_to_load = {app: apps[app] for app in temp_apps if app.lower().startswith(search.lower()) and apps[app][0] == "config" and apps[app][1] != "hidden"}
elif active_filter == "hidden":  # hidden
    apps_to_load = {app: apps[app] for app in temp_apps if app.lower().startswith(search.lower()) and apps[app][1] == "hidden"}
else:  # unknown filter
    apps_to_load = temp_apps
````

Results:
- 1st dataset
  - 1.2592999999999848
  - 1.2516000000000076
  - 1.1936999999999898
  - 1.2016000000000076
  - 1.2842999999999847
- 2nd dataset
  - 2.65
  - 2.678099999999995
  - 2.6375
  - 2.628200000000015
  - 2.592200000000048

### 2nd method
The second method consists of directly determining what apps should be shown by looking for each app if it is in the active folder (which wasn't the case of the first algorithm).

Its code was:

````python
if active_filter == "no filter":  # no filter
    apps_to_load = {app: apps[app] for app in apps if app.lower().startswith(search.lower()) and apps[app][1] != "hidden" and (app in apps[folder][2] if folder is not None else True)}
elif active_filter == "favorites":  # favorites
    apps_to_load = {app: apps[app] for app in apps if app.lower().startswith(search.lower()) and apps[app][1] == "favorite" and apps[app][1] != "hidden" and (app in apps[folder][2] if folder is not None else True)}
elif active_filter == "game":  # game
    apps_to_load = {app: apps[app] for app in apps if app.lower().startswith(search.lower()) and apps[app][0] == active_filter and apps[app][1] != "hidden" and (app in apps[folder][2] if folder is not None else True)}
elif active_filter == "hidden":  # hidden
    apps_to_load = {app: apps[app] for app in apps if app.lower().startswith(search.lower()) and apps[app][1] == "hidden" and (app in apps[folder][2] if folder is not None else True)}
else:  # unknown filter
    apps_to_load = apps.copy()
````

Results:
- 1st dataset
  - 1.1389999999999874
  - 1.1780999999999948
  - 1.1516000000000077
  - 1.128099999999995 
  - 1.1282000000000152
- 2nd dataset
  - 1.2905999999999949
  - 1.3265999999999623
  - 1.3265000000000327
  - 1.325
  - 1.282800000000043


Even though the first dataset was fairly the same for each algorithm (0.1 sec of difference for 1,000,000 iterations) the second dataset clearly showed that the second algorithm is better and uses 2 times less time than the first one (2.63 sec for 500,000 iterations for the first algorithm and 1.31 sec for 500,000 iterations for the second algorithm).

That's why now the used algorithm is an upgraded version of the second method (the current version (v2.1.0 of the launcher at the time I write this) does not show apps on the home tab if they are in a folder).
