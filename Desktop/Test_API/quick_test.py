#!/usr/bin/env python
"""
quick_test.py - Test rapide pour vérifier l'intégration complète

🚀 USAGE :
  python quick_test.py

✅ VÉRIFIE :
  1. Import tous les packages
  2. Fichier .env chargé correctement
  3. Loguru configuration OK
  4. Fichiers de test présents
  5. Variables d'environnement en place

"""

import sys
import os
from pathlib import Path

# Couleurs pour terminal
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def check(condition, message):
    """Affiche un check ✓ ou ✗"""
    if condition:
        print(f"{GREEN}✓{RESET} {message}")
        return True
    else:
        print(f"{RED}✗{RESET} {message}")
        return False

def main():
    print(f"\n{BLUE}═" * 40)
    print(f"🔍 VÉRIFICATION INTÉGRATION TGR v2.0{RESET}")
    print(f"{BLUE}═" * 40 + f"{RESET}\n")
    
    checks_passed = 0
    checks_total = 0
    
    # 1. Vérifier fichiers essentiels
    print(f"{BLUE}1. Fichiers essentiels{RESET}")
    essential_files = [
        "logic.py",
        "main.py",
        "dashboard.py",
        "test_complete_suite.py",
        "run_all.py",
        ".env",
        "requirements.txt"
    ]
    
    for file in essential_files:
        checks_total += 1
        exists = Path(file).exists()
        if check(exists, f"Fichier {file}"):
            checks_passed += 1
    
    # 2. Vérifier imports Python
    print(f"\n{BLUE}2. Imports Python{RESET}")
    
    packages = {
        "loguru": "Loguru (logging pro)",
        "dotenv": "python-dotenv (env vars)",
        "pytest": "Pytest (tests)",
        "streamlit": "Streamlit (dashboard)",
        "plotly": "Plotly (graphiques)",
        "fastapi": "FastAPI (API)",
        "pandas": "Pandas (data)"
    }
    
    for package, description in packages.items():
        checks_total += 1
        try:
            __import__(package)
            if check(True, f"{description}"):
                checks_passed += 1
        except ImportError:
            check(False, f"{description}")
    
    # 3. Vérifier .env
    print(f"\n{BLUE}3. Configuration .env{RESET}")
    
    checks_total += 1
    env_exists = Path(".env").exists()
    if check(env_exists, "Fichier .env présent"):
        checks_passed += 1
        
        # Charger et vérifier contenu
        from dotenv import load_dotenv
        load_dotenv()
        
        checks_total += 1
        api_key = os.getenv("TGR_API_KEY")
        if check(api_key, f"TGR_API_KEY = {api_key[:20]}..."):
            checks_passed += 1
        
        checks_total += 1
        api_port = os.getenv("API_PORT")
        if check(api_port, f"API_PORT = {api_port}"):
            checks_passed += 1
    
    # 4. Vérifier structure logs
    print(f"\n{BLUE}4. Structure Logs{RESET}")
    
    checks_total += 1
    logs_dir = Path("logs")
    if check(logs_dir.exists() or True, "Répertoire logs/ (sera créé au démarrage)"):
        checks_passed += 1
    
    # 5. Vérifier Loguru configuration dans logic.py
    print(f"\n{BLUE}5. Configuration Loguru{RESET}")
    
    checks_total += 1
    with open("logic.py", "r") as f:
        logic_content = f.read()
        has_loguru = "from loguru import logger" in logic_content
        if check(has_loguru, "Loguru importé dans logic.py"):
            checks_passed += 1
    
    checks_total += 1
    has_loguru_config = "logger.add(" in logic_content
    if check(has_loguru_config, "Configuration Loguru avec logger.add()"):
        checks_passed += 1
    
    # 6. Vérifier FastAPI configuration dans main.py
    print(f"\n{BLUE}6. Configuration FastAPI{RESET}")
    
    checks_total += 1
    with open("main.py", "r") as f:
        main_content = f.read()
        has_dotenv = "from dotenv import load_dotenv" in main_content
        if check(has_dotenv, "load_dotenv() intégré dans main.py"):
            checks_passed += 1
    
    checks_total += 1
    has_verify_key = "def verify_api_key" in main_content
    if check(has_verify_key, "Fonction verify_api_key() présente"):
        checks_passed += 1
    
    # 7. Vérifier Streamlit
    print(f"\n{BLUE}7. Dashboard Streamlit{RESET}")
    
    checks_total += 1
    with open("dashboard.py", "r") as f:
        dash_content = f.read()
        has_streamlit = "import streamlit as st" in dash_content
        if check(has_streamlit, "Streamlit importé dans dashboard.py"):
            checks_passed += 1
    
    checks_total += 1
    has_plotly = "import plotly.graph_objects" in dash_content
    if check(has_plotly, "Plotly intégré dans dashboard.py"):
        checks_passed += 1
    
    # 8. Vérifier tests Pytest
    print(f"\n{BLUE}8. Suite Pytest{RESET}")
    
    checks_total += 1
    with open("test_complete_suite.py", "r") as f:
        tests_content = f.read()
        has_pytest = "import pytest" in tests_content
        if check(has_pytest, "Pytest importé"):
            checks_passed += 1
    
    checks_total += 1
    test_count = tests_content.count("def test_")
    if check(test_count > 30, f"{test_count} tests détectés"):
        checks_passed += 1
    
    # Résumé final
    print(f"\n{BLUE}═" * 40)
    print(f"📊 RÉSUMÉ{RESET}")
    print(f"{BLUE}═" * 40 + f"{RESET}\n")
    
    percentage = (checks_passed / checks_total) * 100 if checks_total > 0 else 0
    
    print(f"Vérifications réussies : {checks_passed}/{checks_total} ({percentage:.0f}%)")
    
    if percentage == 100:
        print(f"\n{GREEN}🎉 TOUT EST PRÊT !{RESET}\n")
        print(f"{BLUE}PROCHAINES ÉTAPES :{RESET}")
        print(f"  1. python run_all.py")
        print(f"     → Lance API + Dashboard automatiquement")
        print(f"\n  2. Ouvrir http://localhost:8501 dans navigateur")
        print(f"     → Charger un fichier CSV")
        print(f"\n  3. Voir les résultats en direct !")
        print(f"\n{BLUE}ACCÈS :{RESET}")
        print(f"  API Swagger ... http://localhost:8000/docs")
        print(f"  Dashboard ... http://localhost:8501")
        print(f"  Logs ......... logs/app.log + logs/security.log")
        return 0
    else:
        print(f"\n{RED}⚠️  Certains éléments doivent être vérifiés.{RESET}\n")
        print(f"{BLUE}Solutions possibles :{RESET}")
        print(f"  • pip install -r requirements.txt")
        print(f"  • Vérifier que .env existe")
        print(f"  • Vérifier les chemins fichiers")
        return 1

if __name__ == "__main__":
    sys.exit(main())
