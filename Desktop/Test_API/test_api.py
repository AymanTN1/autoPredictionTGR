"""
test_api.py - Tests pour l'API

Ce script teste les deux approches :
1. Test direct de logic.py (sans API)
2. Test de l'API FastAPI (avec requêtes HTTP)
"""

import os
import pandas as pd
from logic import DataCleaner, SmartPredictor, predict_from_file_content
import json


def test_logic_direct():
    """Test direct des classes DataCleaner et SmartPredictor (sans API)."""
    
    print("\n" + "="*80)
    print("TEST 1 : LOGIC DIRECT (Sans API)")
    print("="*80)
    
    try:
        # Charger le fichier
        file_path = os.path.join('dataSets', 'depensesEtat.csv')
        
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        print(f"\n✓ Fichier chargé : {os.path.getsize(file_path)} bytes")
        
        # Tester avec 12 mois
        result = predict_from_file_content(file_content, months=12)
        
        print("\n✓ Prédiction réussie !")
        print(f"  - Statut : {result.get('status')}")
        print(f"  - Modèle : {result.get('model_info', {}).get('name')}")
        print(f"  - Ordre : {result.get('model_info', {}).get('order')}")
        print(f"  - Saisonnier : {result.get('model_info', {}).get('seasonal_order')}")
        print(f"  - Nombre de prévisions : {len(result.get('forecast', {}).get('dates', []))}")
        
        print("\n✓ Logs d'analyse :")
        for log in result.get('explanations', []):
            print(f"  - {log}")
        
        print("\n✓ Aperçu des prévisions :")
        forecast_dates = result.get('forecast', {}).get('dates', [])
        forecast_values = result.get('forecast', {}).get('values', [])
        for i, (date, value) in enumerate(zip(forecast_dates[:3], forecast_values[:3])):
            print(f"  - {date}: {value:.2f}")
        if len(forecast_dates) > 3:
            print(f"  ... et {len(forecast_dates) - 3} autres mois")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERREUR : {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """Test de l'API FastAPI avec des requêtes HTTP."""
    
    print("\n" + "="*80)
    print("TEST 2 : API FASTAPI (Avec requêtes HTTP)")
    print("="*80)
    
    try:
        import requests
        
        # Test 1 : Health check
        print("\n--- Test 1 : Health Check ---")
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print(f"✓ Health check OK : {response.json()}")
        else:
            print(f"✗ Health check échoué : {response.status_code}")
            return False
        
        # Test 2 : Info
        print("\n--- Test 2 : Info API ---")
        response = requests.get('http://localhost:8000/info', timeout=5)
        if response.status_code == 200:
            info = response.json()
            print(f"✓ Modèles disponibles : {info.get('models_available')}")
        else:
            print(f"✗ Info échouée : {response.status_code}")
        
        # Test 3 : Prédiction
        print("\n--- Test 3 : Prédiction par Upload ---")
        file_path = os.path.join('dataSets', 'depensesEtat.csv')
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                'http://localhost:8000/predict?months=12',
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Prédiction réussie !")
            print(f"  - Statut : {result.get('status')}")
            print(f"  - Modèle : {result.get('model_info', {}).get('name')}")
            print(f"  - Prévisions : {len(result.get('forecast', {}).get('values', []))} mois")
        else:
            print(f"✗ Prédiction échouée : {response.status_code}")
            print(f"  Réponse : {response.text}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n⚠️  L'API n'est pas accessible sur http://localhost:8000")
        print("    Pour tester l'API : lancez d'abord 'uvicorn main:app --reload'")
        return None
    except Exception as e:
        print(f"\n✗ ERREUR : {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*80)
    print(" 🧪 TESTS DE L'API PRÉDICTION DES DÉPENSES")
    print("="*80)
    
    # Test 1 : Logic direct
    result1 = test_logic_direct()
    
    # Test 2 : API
    result2 = test_api_endpoints()
    
    # Résumé
    print("\n" + "="*80)
    print(" 📊 RÉSUMÉ DES TESTS")
    print("="*80)
    print(f"\n✓ Logic direct : {'PASSÉ' if result1 else 'ÉCHOUÉ'}")
    
    if result2 is None:
        print(f"⚠️  API FastAPI : Non testé (serveur non accessible)")
    else:
        print(f"✓ API FastAPI : {'PASSÉ' if result2 else 'ÉCHOUÉ'}")
    
    if result1:
        print("\n✅ L'API est prête à être utilisée !")
        print("\nPour lancer le serveur :")
        print("  uvicorn main:app --reload")
        print("\nPour accéder à la documentation :")
        print("  http://localhost:8000/docs")
    else:
        print("\n❌ Des erreurs ont été détectées. Vérifiez les logs ci-dessus.")


if __name__ == "__main__":
    main()
