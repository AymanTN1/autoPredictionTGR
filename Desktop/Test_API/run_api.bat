@echo off
REM Script de lancement rapide de l'API sur Windows

echo.
echo ==============================================================
echo  API Prediction des Depenses - Lancement rapide
echo ==============================================================
echo.

REM Verifier si Python est disponible
C:/Users/ayman/Desktop/Test_API/venv/Scripts/python.exe --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python non trouve
    echo Assurez-vous que l'environnement virtuel est configure
    pause
    exit /b 1
)

echo [1/3] Verification des dependances...
C:/Users/ayman/Desktop/Test_API/venv/Scripts/python.exe -c "import fastapi; import uvicorn; import pandas; import statsmodels" >nul 2>&1
if errorlevel 1 (
    echo [!] Installation des dependances...
    C:/Users/ayman/Desktop/Test_API/venv/Scripts/python.exe -m pip install -q -r requirements.txt
)
echo [OK] Dependances verifiees

echo.
echo [2/3] Test de fonctionnalite de la logique...
C:/Users/ayman/Desktop/Test_API/venv/Scripts/python.exe -c "
from logic import predict_from_file_content
import os
try:
    with open(os.path.join('dataSets', 'depensesEtat.csv'), 'rb') as f:
        result = predict_from_file_content(f.read(), months=3)
    if result['status'] == 'success':
        print('[OK] Logic fonctionne - Modele choisi:', result['model_info']['name'])
    else:
        print('[ERROR]', result['error_message'])
except Exception as e:
    print('[ERROR]', str(e))
"

if errorlevel 1 (
    echo [ERROR] La logique n'a pas pu etre testee
    pause
    exit /b 1
)

echo.
echo [3/3] Lancement du serveur FastAPI...
echo.
echo    INFO: Serveur demarre sur http://localhost:8000
echo    INFO: Documentation: http://localhost:8000/docs
echo.
echo    Pour arreter le serveur: Appuyez sur Ctrl+C
echo.

C:/Users/ayman/Desktop/Test_API/venv/Scripts/python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
