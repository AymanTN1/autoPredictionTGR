@echo off
REM Wrapper: délégation vers scripts\windows\stop_api.bat
call "%~dp0scripts\windows\stop_api.bat" %*
