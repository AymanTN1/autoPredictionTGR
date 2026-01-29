@echo off
REM ============================================================
REM stop_api.bat - Arrete l'API FastAPI proprement
REM ============================================================

echo.
echo ARRET DE L'API FASTAPI
echo.

REM Trouver le processus uvicorn sur le port 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    set PID=%%a
)

if defined PID (
    echo Arret du processus API (PID: %PID%)...
    taskkill /PID %PID% /F
    if %ERRORLEVEL% EQU 0 (
        echo OK - API arretee avec succes
    ) else (
        echo ERREUR lors de l'arret de l'API
    )
) else (
    echo Aucun processus trouve sur le port 8000
    echo L'API n'est probablement pas en cours d'execution
)

echo.
