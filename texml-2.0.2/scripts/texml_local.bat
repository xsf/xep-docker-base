set SCRIPTDIR=%~dp0
set PYTHONPATH=%SCRIPTDIR%\..;%PYTHONPATH%

python %SCRIPTDIR%texml.py %*

pause
