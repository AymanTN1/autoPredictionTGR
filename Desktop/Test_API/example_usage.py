"""
example_usage.py - Exemples d'utilisation de l'API

Montre différentes façons d'utiliser l'API :
1. Appel direct à logic.py (sans API)
2. Appel HTTP à l'API FastAPI
3. Utilisation avec un ordinateur/établissement spécifique
"""

import os
import pandas as pd
from logic import predict_from_file_content, DataCleaner, SmartPredictor
import json


# ==============================================================================
# EXEMPLE 1 : UTILISATION DIRECTE DE logic.py
# ==============================================================================
def example_1_direct_usage():
    """Exemple 1 : Utiliser directement les classes sans API."""
    
    print("\n" + "="*80)
    print("EXEMPLE 1 : Utilisation directe de logic.py")
    print("="*80)
    
    # Charger le fichier CSV
    file_path = os.path.join('dataSets', 'depensesEtat.csv')
    
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    # Méthode 1 : Utiliser la fonction complète
    print("\n--- Méthode 1 : Fonction d'orchestration complète ---")
    result = predict_from_file_content(file_content, months=24)
    
    if result['status'] == 'success':
        print(f"✓ Succès !")
        print(f"  Modèle choisi : {result['model_info']['name']}")
        print(f"  Nombre de prévisions : {len(result['forecast']['dates'])}")
    else:
        print(f"✗ Erreur : {result['error_message']}")
    
    # Méthode 2 : Étapes manuelles pour plus de contrôle
    print("\n--- Méthode 2 : Étapes manuelles ---")
    
    # Étape 1 : Nettoyage
    cleaner = DataCleaner(file_content)
    df_clean = cleaner.run()
    print(f"✓ Nettoyage : {len(df_clean)} mois")
    for log in cleaner.logs:
        print(f"  - {log}")
    
    # Étape 2 : Sélection du modèle
    predictor = SmartPredictor(df_clean)
    predictor.analyze_and_configure()
    print(f"✓ Modèle sélectionné : {predictor.model_name}")
    for log in predictor.logs:
        print(f"  - {log}")
    
    # Étape 3 : Prédiction
    result = predictor.get_prediction_data(months=24)
    print(f"✓ Prévisions générées")
    
    # Afficher les résultats
    print(f"\n--- Résultats de prédiction ---")
    for date, value, upper, lower in zip(
        result['forecast']['dates'][:3],
        result['forecast']['values'][:3],
        result['forecast']['confidence_upper'][:3],
        result['forecast']['confidence_lower'][:3]
    ):
        print(f"  {date}: {value:.2f} (IC: {lower:.2f} - {upper:.2f})")


# ==============================================================================
# EXEMPLE 2 : UTILISATION VIA L'API FASTAPI
# ==============================================================================
def example_2_api_usage():
    """Exemple 2 : Utiliser l'API FastAPI via des requêtes HTTP."""
    
    print("\n" + "="*80)
    print("EXEMPLE 2 : Utilisation de l'API FastAPI")
    print("="*80)
    
    try:
        import requests
        
        # Vérifier que le serveur est accessible
        try:
            response = requests.get('http://localhost:8000/health', timeout=2)
        except requests.exceptions.ConnectionError:
            print("⚠️  Serveur non accessible sur http://localhost:8000")
            print("    Pour lancer le serveur, exécutez :")
            print("    uvicorn main:app --reload")
            return
        
        print("\n--- Uploader un fichier et obtenir une prédiction ---")
        
        file_path = os.path.join('dataSets', 'depensesEtat.csv')
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                'http://localhost:8000/predict?months=12',
                files=files,
                timeout=30
            )
        
        result = response.json()
        
        if result['status'] == 'success':
            print(f"✓ Succès !")
            print(f"  Modèle : {result['model_info']['name']}")
            print(f"  Order : {result['model_info']['order']}")
            print(f"  Saisonnier : {result['model_info']['seasonal_order']}")
            print(f"  AIC : {result['model_info']['aic']:.2f}")
            
            print(f"\n--- Logs d'analyse ---")
            for log in result['explanations']:
                print(f"  - {log}")
            
            print(f"\n--- Aperçu des prévisions ---")
            for date, value in zip(
                result['forecast']['dates'][:3],
                result['forecast']['values'][:3]
            ):
                print(f"  {date}: {value:.2f}")
        
        else:
            print(f"✗ Erreur : {result['error_message']}")
    
    except ImportError:
        print("⚠️  Module 'requests' non installé")
        print("    Installez-le avec : pip install requests")
    except Exception as e:
        print(f"✗ Erreur : {str(e)}")


# ==============================================================================
# EXEMPLE 3 : PRÉDICTION POUR PLUSIEURS ORDINATEURS
# ==============================================================================
def example_3_multiple_ordonateurs():
    """Exemple 3 : Boucler sur plusieurs fichiers ordonateurs."""
    
    print("\n" + "="*80)
    print("EXEMPLE 3 : Prédiction pour plusieurs établissements")
    print("="*80)
    
    ordonateurs_dir = os.path.join('dataSets', 'ordonateurs')
    
    if not os.path.exists(ordonateurs_dir):
        print(f"⚠️  Répertoire non trouvé : {ordonateurs_dir}")
        return
    
    # Récupérer les 3 premiers fichiers
    csv_files = [f for f in os.listdir(ordonateurs_dir) if f.endswith('.csv')][:3]
    
    print(f"\n--- Traitement de {len(csv_files)} établissements ---\n")
    
    results_summary = []
    
    for csv_file in csv_files:
        file_path = os.path.join(ordonateurs_dir, csv_file)
        code = csv_file.replace('.csv', '')
        
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            result = predict_from_file_content(file_content, months=12)
            
            if result['status'] == 'success':
                summary = {
                    'code': code,
                    'modele': result['model_info']['name'],
                    'aic': result['model_info']['aic'],
                    'derniere_prevision': result['forecast']['values'][-1]
                }
                results_summary.append(summary)
                print(f"✓ {code}: {result['model_info']['name']} (AIC={result['model_info']['aic']:.2f})")
            else:
                print(f"✗ {code}: Erreur - {result['error_message']}")
        
        except Exception as e:
            print(f"✗ {code}: Exception - {str(e)}")
    
    # Afficher un résumé
    if results_summary:
        print(f"\n--- Résumé des prédictions ---")
        for r in results_summary:
            print(f"  {r['code']}: {r['modele']:6s} | Dernière prévision: {r['derniere_prevision']:.2f}")


# ==============================================================================
# EXEMPLE 4 : SAUVEGARDER LES RÉSULTATS
# ==============================================================================
def example_4_save_results():
    """Exemple 4 : Sauvegarder les résultats en JSON et CSV."""
    
    print("\n" + "="*80)
    print("EXEMPLE 4 : Sauvegarder les résultats")
    print("="*80)
    
    file_path = os.path.join('dataSets', 'depensesEtat.csv')
    
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    result = predict_from_file_content(file_content, months=12)
    
    if result['status'] == 'success':
        # Sauvegarder en JSON
        json_path = 'predictions_result.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✓ Résultat JSON sauvegardé : {json_path}")
        
        # Sauvegarder les prévisions en CSV
        df_forecast = pd.DataFrame({
            'date': result['forecast']['dates'],
            'prediction': result['forecast']['values'],
            'confidence_lower': result['forecast']['confidence_lower'],
            'confidence_upper': result['forecast']['confidence_upper']
        })
        
        csv_path = 'predictions_forecast.csv'
        df_forecast.to_csv(csv_path, index=False)
        print(f"✓ Prévisions CSV sauvegardées : {csv_path}")
        
        # Sauvegarder l'historique en CSV
        df_history = pd.DataFrame({
            'date': result['history']['dates'],
            'value': result['history']['values']
        })
        
        history_path = 'predictions_history.csv'
        df_history.to_csv(history_path, index=False)
        print(f"✓ Historique CSV sauvegardé : {history_path}")


# ==============================================================================
# MAIN
# ==============================================================================
def main():
    print("\n" + "="*80)
    print("🎯 EXEMPLES D'UTILISATION DE L'API PRÉDICTION")
    print("="*80)
    
    # Choisir l'exemple à exécuter
    print("\nQuel exemple exécuter ?")
    print("  1. Utilisation directe de logic.py")
    print("  2. Utilisation de l'API FastAPI")
    print("  3. Prédiction pour plusieurs établissements")
    print("  4. Sauvegarder les résultats")
    print("  A. Tous les exemples")
    print("  Q. Quitter")
    
    choice = input("\nChoix (1-4, A, ou Q) : ").strip().upper()
    
    if choice == '1':
        example_1_direct_usage()
    elif choice == '2':
        example_2_api_usage()
    elif choice == '3':
        example_3_multiple_ordonateurs()
    elif choice == '4':
        example_4_save_results()
    elif choice == 'A':
        example_1_direct_usage()
        example_2_api_usage()
        example_3_multiple_ordonateurs()
        example_4_save_results()
    elif choice == 'Q':
        print("Au revoir !")
        return
    else:
        print("Choix invalide")
        return
    
    print("\n✅ Exemple terminé !")


if __name__ == "__main__":
    main()
