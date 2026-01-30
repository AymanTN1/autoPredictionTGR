@echo off
REM Exécute la suite pytest dans le dossier tests (paths résolus depuis scripts\windows)
echo Lancement des tests pytest...
"%~dp0..\..\venv\Scripts\python.exe" -m pytest "%~dp0..\..\tests" -q
pause
