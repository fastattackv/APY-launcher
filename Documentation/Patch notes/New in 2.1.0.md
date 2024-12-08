# New features in the _Configurations and Folders update_ (2.1.0)

## Functionalities
- **Configurations**: launch multiple apps with only one click !
- **Folders**: store applications in a folder to organize them more easily !
- Games auto detector: select a folder in your pc containing all your games (or their shortcuts) and they will all be added to the launcher
- Single app tab: you can now double-click a game or a config to modify it.
- Messages: now, if a message has to be passed to the users of the launcher, they will not have to check GitHub or a discord server: a message will pop up in the launcher if connected to internet
- Moving apps: in the apps tab, you can now move your apps to put them in the order you want (if you miss clicked a drag, you can press the cancel button in the apps tab to cancel the last drag)
- Hidden apps: you can now hide an application / configuration / folder and it will only appear if you select the "Hidden apps" filter
- Experimental updates: you can now update to versions of the launcher in development. These versions might contain bugs and it is not impossible they could wipe the data in your launcher.
- Random selector: randomly selects a game or a configuration (not a bonus or folder) and ask the user if it should be launched
- New buttons in the options tab to open the local files of the launcher and the logs of the launcher

## Quality of life
- **Improved performance** and reduced RAM usage a bit
- Reduced the app weight by a little less than half of the original weight (from 148MB to 80MB)
- Made the app scaling aware. That means that if the scaling in Windows parameters is not 100%, the app will adapt and change its size.
- Reworked the calculation of the number of columns that can be shown, so it occupies all the window (and all apps now make the same size and if the name is too long, it is cut)
- The parameters in the options tab are now more clearly separated
- The application automatically fills the name entry if it's empty when adding an app
- Removed the 30 characters limit on apps names
- Favorites games now have a star to the right of their name
- Optimized the calculation of the display of the apps: it is now much faster
- To show the full name if it is cut for being too long, hover on the app for at least 0.5 seconds and a pop-up will show the full name of the app.
- Modified the default size of the window form 1380x800 to 1280x720 and the minimum size of the window to 1000x600 to fit widgets in the appstab
- If a shortcut added to the launcher is moved / deleted but the game is still installed, the app in saved in the launcher will now still work

## Resolved bugs
- The page was expending a lot when selecting a too long path when adding an app
- The app couldn't start if it was not started from the needed directory
- Added checking for app names to forbid windows forbidden characters
- When using light mode, after dragging an app, its text color would not return to black and instead would go white
- The launcher couldn't find an icon from a Steam or Epic Games game if the .url shortcut wasn't exactly built like Steam or Epic Games build it (even though the shortcut worked)
- uplay (ubisoft connect) games were added without their icon

## News for developers
There are no new functionalities for developers in this update :(

But prepare yourselves for the next update which will introduce the biggest planned feature for developers: Modules ! In the next update you will be able to create modules to add functionalities to the launcher using python and an API to control the launcher itself !

## Other
- The launcher is now licensed under GNU version 3 or later.
