#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_api_demo.py

Script de DÉMONSTRATION de l'API
Montre comment utiliser l'API avec différentes méthodes
"""

import os
import sys
import json
from pathlib import Path

# Ajouter le dossier courant au path Python
sys.path.insert(0, os.path.dirname(__file__))

print("\n" + "="*70)
print(" TEST DE DÉMONSTRATION - API Prédiction des Dépenses".center(70))
print("="*70 + "\n")

# ==============================================================================
# ÉTAPE 1 : Vérifier les dépendances
# ==============================================================================
print("ÉTAPE 1 : Vérification de l'environnement")
print("-" * 70)

try:
    import pandas as pd
    print("✓ pandas installé")
except ImportError:
    print("✗ pandas MANQUANT - À installer : pip install pandas")
    sys.exit(1)

try:
    import numpy as np
    print("✓ numpy installé")
except ImportError:
    print("✗ numpy MANQUANT")
    sys.exit(1)

try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    print("✓ statsmodels installé")
except ImportError:
    print("✗ statsmodels MANQUANT")
    sys.exit(1)

try:
    import fastapi
    print("✓ fastapi installé (API est disponible)")
except ImportError:
    print("✗ fastapi MANQUANT")
    sys.exit(1)

print()

# ==============================================================================
# ÉTAPE 2 : Vérifier le fichier de test
# ==============================================================================
print("ÉTAPE 2 : Vérification du fichier de test")
print("-" * 70)

test_file = Path('dataSets/depensesEtat.csv')

if not test_file.exists():
    print(f"✗ ERREUR : {test_file} n'existe pas!")
    print("\n  Créez le fichier ou placez-le dans : dataSets/depensesEtat.csv")
    sys.exit(1)

file_size = test_file.stat().st_size / (1024 * 1024)  # Convertir en MB
print(f"✓ Fichier trouvé : {test_file}")
print(f"  Taille : {file_size:.1f} MB")

# Lire un aperçu du fichier
try:
    df_sample = pd.read_csv(test_file, sep=';', nrows=5)
    print(f"  Colonnes : {list(df_sample.columns)}")
    print(f"  Aperçu :")
    print(f"    {df_sample.iloc[0].to_dict()}")
except Exception as e:
    print(f"✗ Erreur lors de la lecture : {e}")
    sys.exit(1)

print()

# ==============================================================================
# ÉTAPE 3 : Tester le code directement (sans API)
# ==============================================================================
print("ÉTAPE 3 : Test du code métier (DataCleaner + SmartPredictor)")
print("-" * 70)

try:
    from logic import DataCleaner, SmartPredictor
    print("✓ Modules importés : DataCleaner, SmartPredictor")
except ImportError as e:
    print(f"✗ ERREUR : Impossible d'importer les modules : {e}")
    sys.exit(1)

print("\n  Étape 3a : DataCleaner - Nettoyage des données...")
try:
    # Lire le fichier et nettoyer
    with open(test_file, 'rb') as f:
        file_content = f.read()
    
    cleaner = DataCleaner(file_content)
    df_clean = cleaner.run()
    
    print(f"  ✓ Données nettoyées avec succès")
    print(f"    Résultat : {len(df_clean)} mois (agrégés)")
    print(f"    Période : {df_clean.index.min().date()} à {df_clean.index.max().date()}")
    print(f"    Colonnes : {list(df_clean.columns)}")
    
except Exception as e:
    print(f"  ✗ ERREUR : {str(e)[:100]}")
    sys.exit(1)

print("\n  Étape 3b : SmartPredictor - Analyse et sélection du modèle...")
try:
    predictor = SmartPredictor(df_clean)
    predictor.analyze_and_configure()
    
    print(f"  ✓ Analyse complétée")
    print(f"    Modèle sélectionné : {predictor.model_name}")
    print(f"    Ordre ARIMA : {predictor.order}")
    print(f"    Ordre Saisonnier : {predictor.seasonal_order}")
    
    # Afficher les logs
    print(f"\n  Logs de l'analyse :")
    for i, log in enumerate(predictor.logs, 1):
        if len(log) > 70:
            print(f"    {i}. {log[:67]}...")
        else:
            print(f"    {i}. {log}")
    
except Exception as e:
    print(f"  ✗ ERREUR : {str(e)[:100]}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n  Étape 3c : Prédictions - Génération des prévisions...")
try:
    result = predictor.get_prediction_data(months=12)
    
    if result['status'] == 'success':
        print(f"  ✓ Prédictions générées avec succès")
        print(f"    Nombre de mois prédits : {len(result['forecast']['values'])}")
        print(f"    AIC du modèle : {result['model_info']['aic']:.2f}")
        
        # Afficher les premières prédictions
        print(f"\n  Premières prédictions :")
        for i in range(min(3, len(result['forecast']['dates']))):
            date = result['forecast']['dates'][i]
            value = result['forecast']['values'][i]
            print(f"    {date} : {value:,.0f} DH")
        
    else:
        print(f"  ✗ Erreur : {result.get('error_message')}")
        sys.exit(1)
        
except Exception as e:
    print(f"  ✗ ERREUR : {str(e)[:100]}")
    sys.exit(1)

print()

# ==============================================================================
# ÉTAPE 4 : Information sur l'API
# ==============================================================================
print("ÉTAPE 4 : Information sur l'utilisation de l'API")
print("-" * 70)

print("""
OPTION 1 : Utiliser l'interface Swagger UI (FACILE)
─────────────────────────────────────────────────────
  1. Double-cliquer sur : start_api.bat
  2. Attendre : "Application startup complete"
  3. Ouvrir navigateur : http://localhost:8000/docs
  4. Cliquer sur "POST /predict"
  5. Cliquer sur "Try it out"
  6. Uploader le fichier dataSets/depensesEtat.csv
  7. Cliquer sur "Execute"
  8. Voir le résultat JSON

OPTION 2 : Utiliser cURL (LIGNE DE COMMANDE)
──────────────────────────────────────────────
  # Démarrer l'API
  start_api.bat
  
  # Dans une autre PowerShell, lancer :
  curl -X POST http://localhost:8000/predict `
    -F "file=@dataSets/depensesEtat.csv"

OPTION 3 : Utiliser Python (PROGRAMMATION)
────────────────────────────────────────────
  import requests
  with open('dataSets/depensesEtat.csv', 'rb') as f:
      response = requests.post(
          'http://localhost:8000/predict',
          files={'file': f},
          params={'months': 12}
      )
  print(response.json())

OPTION 4 : Utiliser le code directement (IMPORT)
──────────────────────────────────────────────────
  from logic import DataCleaner, SmartPredictor, predict_from_file_content
  
  with open('dataSets/depensesEtat.csv', 'rb') as f:
      result = predict_from_file_content(f.read(), months=12)
  print(result)
""")

print()

# ==============================================================================
# ÉTAPE 5 : Sauvegarder les résultats
# ==============================================================================
print("ÉTAPE 5 : Sauvegarde des résultats")
print("-" * 70)

output_file = Path('test_results.json')
try:
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"✓ Résultats sauvegardés dans : {output_file}")
except Exception as e:
    print(f"✗ Erreur lors de la sauvegarde : {e}")

print()

# ==============================================================================
# RÉSUMÉ
# ==============================================================================
print("="*70)
print(" RÉSUMÉ - TOUT FONCTIONNE!".center(70))
print("="*70)

print(f"""
PROCHAINES ÉTAPES :

1. Pour utiliser l'API Web (Swagger UI) :
   → Double-cliquer sur : start_api.bat

2. Pour tester avec cURL :
   → Ouvrir PowerShell et lancer :
     curl -X POST http://localhost:8000/predict -F "file=@dataSets/depensesEtat.csv"

3. Pour programmer avec l'API :
   → Voir les exemples dans le README.md

4. Pour utiliser le code directement (sans API) :
   → from logic import predict_from_file_content
   → result = predict_from_file_content(file_content, months=12)

DOCUMENTATION :
   → README.md (guide complet)
   → Swagger UI : http://localhost:8000/docs (une fois l'API démarrée)

GESTION DE VENV :
   → activate_venv.bat   : Démarrer venv
   → start_api.bat       : Lancer l'API
   → stop_api.bat        : Arrêter l'API
   → deactivate_venv.bat : Quitter venv
""")

print("="*70 + "\n")
