@echo off
REM ============================================================
REM deactivate_venv.bat - Desactive l'environnement virtuel
REM ============================================================

echo.
echo DESACTIVATION DE L'ENVIRONNEMENT VIRTUEL
echo.

if defined VIRTUAL_ENV (
    set "PATH=%PATH:venv\Scripts;=%"
    set VIRTUAL_ENV=
) else (
    echo.
)

echo OK - Environnement virtuel desactive
echo.

