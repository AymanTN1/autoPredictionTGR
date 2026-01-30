@echo off
REM Wrapper root pour lancer les tests via scripts\windows\run_tests.bat
call "%~dp0scripts\windows\run_tests.bat" %*
