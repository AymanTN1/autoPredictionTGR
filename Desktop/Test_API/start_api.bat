@echo off
REM ============================================================
REM start_api.bat - Demarre l'API FastAPI
REM ============================================================

echo.
echo DEMARRAGE DE L'API FASTAPI
echo http://localhost:8000/docs
echo.

REM Verifier si venv est active
if "%VIRTUAL_ENV%"=="" (
    echo ATTENTION : venv n'est pas active!
    echo.
    echo Activation automatique de venv...
    call venv\Scripts\activate.bat
)

REM Verifier que les dependances sont installees
python -c "import fastapi" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR : FastAPI n'est pas installe!
    echo.
    echo Installation automatique des dependances...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo ERREUR : L'installation a echoue
        pause
        exit /b 1
    )
)

echo Environnement pret. Demarrage de l'API...
echo.
echo ============================================================
echo API EN COURS D'EXECUTION
echo ============================================================
echo.
echo Acces Swagger UI    : http://localhost:8000/docs
echo Acces ReDoc         : http://localhost:8000/redoc
echo Sante de l'API      : http://localhost:8000/health
echo.
echo Pour arreter l'API : Appuyer sur Ctrl+C
echo.
echo ============================================================
echo.

REM Lancer l'API
uvicorn main:app --reload --host 127.0.0.1 --port 8000

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERREUR : L'API s'est arretee de maniere anormale
    echo.
    pause
    exit /b 1
)
