#!/usr/bin/env python
"""
run_all.py - Démarrer l'API + Dashboard en une commande

🚀 USAGE :
  python run_all.py              # Lance API + Dashboard en parallèle
  
📊 RÉSULTAT :
  • Terminal 1 : Uvicorn API server (http://localhost:8000)
  • Terminal 2 : Streamlit dashboard (http://localhost:8501)

"""

import subprocess
import sys
import time
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║    🚀 DÉMARRAGE API TGR v2.0 + DASHBOARD STREAMLIT                        ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 TÂCHES À EFFECTUER :
  1. Vérifier le répertoire logs/
  2. Démarrer FastAPI (Uvicorn) sur port 8000
  3. Démarrer Streamlit Dashboard sur port 8501
  4. Afficher URLs d'accès
    
""")
    
    # Créer répertoire logs
    os.makedirs("logs", exist_ok=True)
    print("✅ Répertoire logs/ prêt")
    
    # Vérifier fichier .env
    if not os.path.exists(".env"):
        print("⚠️  Fichier .env non trouvé - créé avec valeurs par défaut")
        with open(".env", "w") as f:
            f.write("TGR_API_KEY=TGR-SECRET-KEY-12345\n")
            f.write("API_HOST=0.0.0.0\n")
            f.write("API_PORT=8000\n")
            f.write("LOG_LEVEL=INFO\n")
    else:
        print("✅ Fichier .env existant")
    
    print("\n" + "="*80)
    print("🔄 DÉMARRAGE API FASTAPI (Uvicorn)")
    print("="*80 + "\n")
    
    # Démarrer API
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", 
         "--host", "0.0.0.0", "--port", "8000", "--reload"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Attendre que l'API démarre
    time.sleep(3)
    
    print("⏳ API lancée sur http://localhost:8000")
    print("📚 Documentation Swagger: http://localhost:8000/docs")
    
    print("\n" + "="*80)
    print("🎨 DÉMARRAGE DASHBOARD STREAMLIT")
    print("="*80 + "\n")
    
    # Démarrer Streamlit
    dashboard_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "dashboard.py",
         "--logger.level=error"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(2)
    
    print("⏳ Dashboard lancé sur http://localhost:8501")
    
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                          ✅ SYSTÈME PRÊT                                  ║
╚════════════════════════════════════════════════════════════════════════════╝

🌐 ACCÈS :
  API FastAPI ........... http://localhost:8000
  Swagger UI ............ http://localhost:8000/docs
  Dashboard Streamlit ... http://localhost:8501

📊 FICHIERS IMPORTANTS :
  logs/app.log ................... Logs applicatifs
  logs/security.log .............. Logs sécurité

🔐 CLÉS API :
  Par défaut: TGR-SECRET-KEY-12345 (à changer en production)
  Modifier dans: .env ou TGR_API_KEY env var

🧪 TESTS :
  Pytest (tous) ........... pytest test_complete_suite.py -v
  Pytest (sécurité) ....... pytest test_complete_suite.py -k security -v
  cURL (exemple) .......... curl -H "X-API-Key: TGR-SECRET-KEY-12345" \\
                                 http://localhost:8000/health

💡 WORKFLOW TYPIQUE :
  1. Ouvrir http://localhost:8501 dans votre navigateur
  2. Charger un fichier CSV
  3. Sélectionner mode AUTO ou USER
  4. Voir les prédictions en temps réel + graphiques

⚠️  POUR ARRÊTER :
  - Appuyer sur Ctrl+C dans cette fenêtre
  - Les deux processus s'arrêteront proprement

═════════════════════════════════════════════════════════════════════════════
""")
    
    try:
        # Attendre les deux processus
        api_process.wait()
        dashboard_process.wait()
    
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt en cours...")
        api_process.terminate()
        dashboard_process.terminate()
        
        try:
            api_process.wait(timeout=3)
            dashboard_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            print("⚠️  Forcage de l'arrêt...")
            api_process.kill()
            dashboard_process.kill()
        
        print("✅ Système arrêté proprement")
        sys.exit(0)

if __name__ == "__main__":
    main()
