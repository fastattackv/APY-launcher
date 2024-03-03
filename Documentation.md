# Documentation for the APY! Launcher:

## Languages:
The language files (.lng) store the dialogs for the application.

> [!TIP]
> If you want to add a language to the application, you can create a new file named "[name of the language].lng" and fill it by translating a language file that already exists (english for example).
> 
> When you are done translating, just copy your file in the "lng files" folder in the APY! Launcher installation folder and it should appear as an available language in the parameters.


## Updates:
- The updates of the launcher use a file telling the updater which files have to be changed
- The cancel option is available only during a certain part of the update, after a certain point, cancelling is not available
- All the update files are stored at "https://github.com/fastattackv/APY-launcher/tree/main/Downloads"
- The games installed and updated with the launcher are stored in the APY! directory containing the launcher


## Parameters:
The params.APYL[^1] file stores the parameters for the APY! Launcher

- language = language to use (name of the .lng file without .lng), does not change when parameters are set to default
- appearance = appearance to use (dark / light), default is dark
- size = size of the window (min is 650x600) in pixels when the app is launched, default is 1380x800
- defaultfilter = filter set by default in the apps tab (0=no filter, 1=favorites, 2=games, 3=bonus, 4=folders), default is 0
- stoplauncherwhengame = defines if the launcher stops when a game is launched, 0 for False, 1 for True
- lastgame = last game that has been launched, "" if there is no last game


## Apps:
The apps.csv file stores the applications that have been added in the launcher

- delimiter = ','
- quotechar = '"'
- 1st column = app name
- 2nd column = type of the app (game / bonus)
- 3rd column = app path
- 4th column = icon path


## Errors:
### 100 errors (minimal errors):
- Err101 = params file not found
- Err102 = language file not found or incorrect
- Err103 = tried to change to a tab that does not exist
- Err104 = tried to launch a game but its path does not exist
- Err105 = tried to delete the icon while deleting the game but its path did not exist
- Err106 = tried to rename the icon while renaming the game but its path did not exist
- Err107 = the entered value for the parameter defaultfilter is incorrect
- Err108 = the entered value for the parameter stoplauncherwhengame is incorrect

### 200 errors (important but not fatal errors):
- Err201 = params file line unknown
- Err202 = apps file not found
- Err203 = path to launcher updater incorrect
- Err204 = path to launcher uninstaller executable file and/or path to uninstaller batch file incorrect

### 300 errors (fatal errors):
- Err301 = param missing in the given params file
- Err302 = not found any valid .lng file to load

[^1]: The .APYL format is a file format created for the launcher, it uses the utf-8 encoder and is the shrinkage of "APY Launcher"
