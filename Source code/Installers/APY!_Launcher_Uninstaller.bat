:: NO CHECKS ARE DONE TO CHECK IF THE DIRECTORY IS APY! OR APY! LAUNCHER SO YOU SHOULD NOT USE THIS SCRIPT MANUALLY
:: The first argument (%1) should be the path to the directory to uninstall enclosed by ""
:: Version 1.0.0

@echo off

set path=%1

:: set cwd to root so the directory to delete isn't the cwd
cd /

if exist %path% (
  :: delete files
  del /s /f /q %path%
  :: delete root repository of the launcher and its subdirectories
  rmdir /s /q %path%
  :: remove the .bat uninstaller file
  del %0
  )
)
