@echo off
REM ============================================================
REM activate_venv.bat - Lance l'environnement virtuel Python
REM ============================================================

echo.
echo ACTIVATION DE L'ENVIRONNEMENT VIRTUEL (venv)
echo.

REM Verifier que venv existe
if not exist "venv\" (
    echo ERREUR : Le dossier 'venv' n'existe pas!
    echo.
    echo Solution : Creer venv avec :
    echo   python -m venv venv
    echo.
    pause
    exit /b 1
)

REM Activer venv
call venv\Scripts\activate.bat

if %ERRORLEVEL% EQU 0 (
    echo OK - Environnement virtuel active avec succes!
    echo.
    echo Vous etes maintenant dans venv. Pour :
    echo   - Demarrer l'API      : double-cliquer start_api.bat
    echo   - Installer packages  : pip install -r requirements.txt
    echo   - Quitter venv        : deactivate
    echo.
) else (
    echo ERREUR lors de l'activation de venv
    pause
    exit /b 1
)
