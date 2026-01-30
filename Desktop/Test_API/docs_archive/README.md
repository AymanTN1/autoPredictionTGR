# 📊 TEST_API - Version API FastAPI

## 🎯 Vue d'Ensemble

Version **API REST** du projet de prédiction des dépenses publiques.  
Transformation d'une architecture **modulaire** (PredictBudgets) en une **API web performante**.

---

## 🏗️ Architecture

```
DataCleaner (logic.py)        SmartPredictor (logic.py)      FastAPI (main.py)
     │                               │                              │
     ├─ Détecte séparateur CSV      ├─ Analyse saisonnalité        ├─ POST /predict
     ├─ Nettoie montants            ├─ Test stationnarité (ADF)    ├─ GET /health
     ├─ Parse dates                 ├─ Tournoi AIC (AR/MA/ARMA)   ├─ GET /info
     ├─ Agrège en mensuel           └─ Retourne JSON structuré     └─ Swagger docs
     └─ Retourne DataFrame clean
```

---

## 💡 Pourquoi venv ? (Python Virtual Environment)

**venv** = Environnement Python **isolé** pour ce projet.

✅ **Avantages :**
- ✓ Dépendances isolées (pas de conflit avec autres projets)
- ✓ Version Python stable et compatible
- ✓ Reproductibilité (même env pour l'encadrant)
- ✓ Sécurité (contrôle des packages installés)
- ✓ Facile à créer/détruire (pas d'empreinte système)

---

## 🚀 Démarrage Rapide

### Méthode Facile (Fichiers .bat)

**Sur Windows, double-cliquer :**

```
activate_venv.bat   → Lance venv
start_api.bat       → Démarre l'API (port 8000)
stop_api.bat        → Arrête l'API
deactivate_venv.bat → Ferme venv
```

### Méthode Manuelle (PowerShell)

```powershell
# 1. Activer venv
& .\venv\Scripts\Activate.ps1

# 2. Démarrer l'API
uvicorn main:app --reload

# 3. Accéder à l'API
# Swagger UI  : http://localhost:8000/docs
# ReDoc       : http://localhost:8000/redoc
# API Health  : http://localhost:8000/health

# 4. Désactiver venv
deactivate
```

---

## 📡 Utilisation de l'API

### 1️⃣ Via Swagger UI (le plus simple)

1. Démarrer l'API : `start_api.bat`
2. Ouvrir : http://localhost:8000/docs
3. Cliquer sur **POST /predict**
4. Cliquer sur **"Try it out"**
5. Uploader un fichier CSV
6. Cliquer sur **"Execute"**
7. Voir le résultat JSON

### 2️⃣ Via cURL (ligne de commande)

```bash
# Mode Auto (système calcule la durée)
curl -X POST http://localhost:8000/predict \
  -F "file=@dataSets/depensesEtat.csv"

# Avec durée spécifique (12 mois)
curl -X POST http://localhost:8000/predict \
  -F "file=@dataSets/depensesEtat.csv" \
  -F "months=12"

# Vérifier la santé de l'API
curl http://localhost:8000/health
```

### 3️⃣ Via Python (programmation)

```python
import requests
import json

# Lancer l'API en parallèle : start_api.bat

# Upload fichier et récupérer prédictions
with open('dataSets/depensesEtat.csv', 'rb') as f:
    files = {'file': f}
    params = {'months': 12}
    response = requests.post('http://localhost:8000/predict', files=files, params=params)

result = response.json()

# Afficher infos
print(f"Modèle utilisé : {result['model_info']['name']}")
print(f"Mois prédits : {len(result['forecast']['values'])}")
print(f"\nLogs (explications) :")
for log in result['explanations']:
    print(f"  • {log}")

# Sauvegarder résultats
with open('predictions.json', 'w') as f:
    json.dump(result, f, indent=2)
```

### 4️⃣ Via JavaScript/Node.js

```javascript
// Utiliser FormData pour upload
const formData = new FormData();
const fileInput = document.getElementById('csvFile');
formData.append('file', fileInput.files[0]);

// POST à l'API
fetch('http://localhost:8000/predict', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log("Modèle :", data.model_info.name);
    console.log("Prévisions :", data.forecast.values);
});
```

---

## 📊 Format des Données

### Fichier CSV d'Entrée

La colonne de **date** et **montant** sont **détectées automatiquement**.

Exemples acceptés :
```csv
date,montant
2020-01-01,1000.50
2020-01-02,1200.75

# OU
DATE_REGLEMENT,SUM(MONTANT_A_REGLER)
01/01/2020,1 000,50
01/02/2020,1 200,75

# OU
jour,amount
2020-01-01,1000
2020-01-02,1200
```

### Réponse JSON de l'API

```json
{
  "status": "success",
  "model_info": {
    "name": "SARIMA",
    "order": "(1, 1, 1)",
    "seasonal_order": "(1, 1, 1, 12)",
    "aic": 150.5
  },
  "explanations": [
    "📊 Chargement du fichier CSV...",
    "✓ Saisonnalité détectée",
    "Choix : SARIMA (Seasonal ARIMA)",
    "=== ANALYSE ET SÉLECTION DU MODÈLE ===",
    "..."
  ],
  "history": {
    "dates": ["2020-01-01", "2020-02-01", ...],
    "values": [1000.0, 1500.5, ...]
  },
  "forecast": {
    "dates": ["2026-01-01", "2026-02-01", ...],
    "values": [1400.0, 1450.0, ...],
    "confidence_upper": [1500.0, 1550.0, ...],
    "confidence_lower": [1300.0, 1350.0, ...]
  },
  "timestamp": "2026-01-29T10:30:45.123456"
}
```

---

## 🧪 Test avec depensesEtat.csv

**Fichier test fourni :** `dataSets/depensesEtat.csv` (28 MB, 390k lignes)

### Script de Test Rapide

1. Démarrer l'API : `start_api.bat`
2. Ouvrir une autre PowerShell et lancer :

```powershell
# Lancer le test Python
python test_api.py
```

Ou manuellement avec curl :
```bash
curl -X POST http://localhost:8000/predict `
  -F "file=@dataSets/depensesEtat.csv"
```

---

## 📁 Fichiers Clés

| Fichier | Rôle |
|---------|------|
| `logic.py` | Classes DataCleaner + SmartPredictor |
| `main.py` | API FastAPI avec endpoints |
| `requirements.txt` | Dépendances Python |
| `activate_venv.bat` | Démarrer l'environnement virtuel |
| `start_api.bat` | Démarrer l'API |
| `stop_api.bat` | Arrêter l'API |
| `deactivate_venv.bat` | Désactiver venv |
| `dataSets/depensesEtat.csv` | Dataset de test |

---

## 🔧 Dépendances

```
fastapi==0.104.0          # Framework API
uvicorn==0.24.0           # Serveur ASIR
pandas==2.1.0             # Manipulation données
numpy==1.24.0             # Calcul numérique
statsmodels==0.14.0       # Modèles statistiques
scipy==1.11.0             # Calcul scientifique
scikit-learn==1.3.0       # Machine learning
python-multipart==0.0.6   # Upload fichiers
```

---

## 📈 Algorithme de Sélection du Modèle

```
┌─────────────────────┐
│   Série Temporelle  │
└──────────┬──────────┘
           │
    ┌──────▼──────┐
    │ Saisonnalité│
    │  > 10% ?    │
    └──┬───────┬──┘
       │Oui    │Non
       │       │
       ▼       ▼
    SARIMA   Test ADF
             (p-value)
             │
        ┌────┴────┐
        │Non-stat?│
        │ p>0.05? │
        └────┬────┘
            │
      ┌─────┴──────┐
      │Oui         │Non
      │            │
      ▼            ▼
    ARIMA      Tournoi AIC
               AR vs MA
               vs ARMA
```

---

## 🎓 Différences clés : PredictBudgets vs TEST_API

| Aspect | PredictBudgets | TEST_API |
|--------|---|---|
| **Type** | Script Python modulaire | API REST |
| **Interface** | Ligne de commande / Python | HTTP / Swagger |
| **Scalabilité** | Local, batch | Serveur web, concurrent |
| **Format sortie** | JSON, dict Python | JSON HTTP |
| **Déploiement** | Ordinateur personnel | Cloud (Docker) |
| **Utilisateurs** | Développeurs | Tout le monde (web) |

---

## 🐳 Docker (Optionnel)

Pour déployer sur le cloud (AWS, Azure, etc.) :

```bash
# Construire l'image
docker build -t api-prediction .

# Lancer le conteneur
docker run -p 8000:8000 api-prediction

# Accéder : http://localhost:8000/docs
```

---

## 📝 Log d'Exécution Exemple

Lors d'un appel à `/predict` avec `depensesEtat.csv` :

```
📊 Chargement du fichier CSV...
Colonnes détectées : date='DATE_REGLEMENT', montant='SUM(MONTANT_A_REGLER)'
Données prêtes : 66 mois (de 2020-01-01 à 2025-06-01)
=== ANALYSE ET SÉLECTION DU MODÈLE ===
Détection de la saisonnalité...
✓ Saisonnalité détectée (amplitude = 42974024217.37 > 10%)
Choix : SARIMA (Seasonal ARIMA pour patterns mensuels)
Test stationnarité (ADF p=0.9865): d=1
✓ Résultat final : SARIMA | order=(1, 1, 1) | seasonal_order=(1, 1, 1, 12)
=== GÉNÉRATION DE PRÉVISIONS (SARIMA, 12 mois) ===
Entraînement SARIMAX | order=(1, 1, 1) | seasonal=(1, 1, 1, 12)
✓ Modèle entraîné (AIC=150.5)
```

---

## ⚡ Performance

- **Temps traitement** : ~5-10 secondes (dépend de la taille du CSV)
- **Mémoire** : ~200-300 MB (pour 390k lignes)
- **Requêtes simultanées** : Jusqu'à 10+ (uvicorn multi-worker)

---

## 🆘 Troubleshooting

| Problème | Solution |
|----------|----------|
| `venv ne s'active pas` | Vérifier chemin : `.\venv\Scripts\Activate.ps1` |
| `Port 8000 déjà utilisé` | `netstat -ano \| findstr :8000` puis tuer le process |
| `Module not found` | Relancer `pip install -r requirements.txt` |
| `Fichier CSV non reconnu` | Vérifier format (UTF-8, colonnes date/montant) |
| `SARIMAX error` | Dataset trop petit (< 24 mois) |

---

**Version :** 2.0 (API REST - FastAPI)  
**Date :** Janvier 2026  
**Branche Git :** `api-version`
