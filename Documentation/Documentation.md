# Documentation for the APY! Launcher:

## Languages:
The language files (.lng) store the dialogs for the application.

The launcher can be installed with english / french or both.

> [!TIP]
> If you want to add a language to the application, you can create a new file named "[name of the language].lng" and fill it by translating a language file that already exists (english for example).
> 
> When you are done translating, just copy your file in the "lng files" folder in the APY! Launcher installation folder and it should appear as an available language in the parameters.
>
> When the launcher gets updated (and languages files get modified), you can use github to see what lines have been modified / deleted / added to the lng files to update yours more easily.


## Updates:
All the update files are stored at "https://github.com/fastattackv/APY-launcher/tree/main/Downloads"

### Functioning of the updates
To update the launcher, the updater follows the following steps:
1. Firstly, the updater downloads the needed files (`APY! Launcher.zip` and the new version of the language files).
2. The updater reads `Files to update` with the [AUL](Documentation.md#the-apy-update-language-aul) to get what files to update because some files cannot be replaced and have to be modified (`apps.csv` or `params.APYL` for example).
3. If the user starts the launcher from the updater, the launcher will start and show what changes have been made to the launcher.

### The APY Update Language (AUL)
The language used by the launcher to update, see [here](AUL.md).


## Installation
The installer follows the following steps to install the launcher, if you want to install it manually, you can follow those steps:
1. Download the archive of the version you want to install (the installer downloads the latest one). The different version are stored in the releases tab of the github repo: [here](https://github.com/fastattackv/APY-launcher/releases).
2. Unpack this archive where you want the app to be installed (you don't need to create a `APY! Launcher` folder: the files in the archive are in a folder). (the installer also creates an `APY!` folder and unpack the archive in it)
3. Download the languages files you want to use (for the version you installed) and place them in the `lng files` folder which is in the folder that was in the archive.
4. Delete the archive.
5. Create a shortcut in the desktop if you want to.
6. You're done ! If you cannot start the launcher, check the `APY launcher logs.log` file in the folder that was in the archive and try to solve the error using the [documentation](Documentation.md#errors). If you cannot solve it, create an issue in the GitHub repo [here](https://github.com/fastattackv/APY-launcher/issues) or ask a question on the discord server [here](https://discord.gg/pHPkkpXhUV).


## Parameters:
The params.APYL[^1] file stores the parameters for the APY! Launcher

- `language` = language to use (name of the .lng file without .lng), does not change when parameters are set to default
- `appearance` = appearance to use (`dark` / `light`), default is `dark`
- `size` = size of the window (min is 1000x600) in pixels when the app is launched, default is `1280x720`. The size of the window is influenced by scaling in windows. For example, if 125% is selected in windows (os) settings, the window's size will be 1600x900 instead of 1280x720.
- `defaultfilter` = filter set by default in the apps tab (`0`=no filter, `1`=favorites, `2`=games, `3`=bonus, `4`=folders, `5`=configurations, `6`=hidden apps), default is `0`
- `stoplauncherwhengame` = defines if the launcher stops when a game is launched, `0` for False, `1` for True, default is False (`0`)
- `lastgame` = last game that has been launched, ` ` if there is no last game
- `ignoredmessages` = messages to ignore when checking for messages


## Apps:
The apps.csv file stores the applications that have been added in the launcher

- delimiter = `,`
- quotechar = `"`
- 1st column = app name
- 2nd column = type of the app (`game` / `bonus` / `config` / `folder`)
- 3rd column = state of the app (`favorite`, `not favorite`, `hidden`)
- 4th column = folder containing the app (in the launcher), `.` means that the app is not in a folder (folders can't be named `.`)

1. if the type of the app (2nd item) is "game" or "bonus":
   - 5th column = app path
   - 6th column = icon path
   - Example: `Name,type,state,folder,path,icon path`
2. if the type of the app is "config":
   - 5th column = icon path
   - 6th column and more = apps contained in the config
   - Example: `Name,config,state,folder,icon path,app1,app2,app3`
3. if the type of the app is "folder":
   - Example: `Name,folder,state,folder`

The apps are stored in the order they appear in the launcher


## Errors:
### 100 errors (minimal errors):
- Err101 = params file not found
- Err102 = language file not found
- Err103 = tried to change to a tab that does not exist
- Err104 = tried to launch an app but its path does not exist
- Err105 = tried to delete the icon while deleting the game but its path did not exist
- Err106 = tried to rename the icon while renaming the game but its path did not exist
- Err107 = the entered value for the parameter defaultfilter is incorrect
- Err108 = the entered value for the parameter stoplauncherwhengame is incorrect
- Err109 = One of the apps contained in a config / folder does not exist in the apps.csv file
- Err110 = One of the apps contained in a config / folder is not a game / bonus
- Err111 = The given language file si not valid
- Err112 = couldn't find the url shortcut when renaming an app
- Err113 = couldn't find the url shortcut when deleting an app
- Err114 = tried to show an app that doesn't exist in the SingleApp tab
- Err115 = an entered value for the parameter ignoredmessages is incorrect
- Err116 = the retrieve of the launcher update message failed

### 200 errors (important but not fatal errors):
- Err201 = params file line unknown
- Err202 = apps file not found
- Err203 = path to launcher updater incorrect
- Err204 = path to launcher uninstaller executable file and/or path to uninstaller batch file incorrect
- Err205 = type of the app is unknown (in the "apps.csv" file)
- Err206 = tried to move an app to a directory that does not exist
- Err207 = a directory has a parent that does not exist
- Err208 = the branch parameter in the params.APYL file is invalid

### 300 errors (fatal errors):
- Err301 = param missing in the given params file
- Err302 = not found any valid .lng file to load

[^1]: The .APYL format is a file format created for the launcher, it uses the utf-8 encoder and is the shrinkage of "APY Launcher"
