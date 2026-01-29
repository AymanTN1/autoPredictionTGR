# 📊 PredictBudgets - Évolution du Code

## 🎯 Vue d'ensemble

Ce projet démontre la **transformation d'un script Jupyter monolithique** (basé sur un seul dataset) en une **architecture modulaire et flexible** capable de traiter **plusieurs datasets simultanément**.

---

## 📝 Avant → Après

### ❌ **Code Original (Notebook Colab)**
```python
# Script statique - Hardcodé sur 1 dataset
df = pd.read_csv('./sample_data/depensesEtat.csv', sep=';')  # ← Chemin fixe

# 390 000 lignes → ~60 lignes (agrégation manuelle)
df_mensuel = df_journalier['montant'].resample('MS').sum()

# Prédiction fixe avec paramètres hardcodés
model = SARIMAX(train_data['montant'], 
                order=(1, 1, 1),              # ← Paramètres figés
                seasonal_order=(1, 1, 1, 12))

# Affichage graphique (pas de résultats structurés)
plt.show()
```

**Limitations :**
- ❌ Fonctionnement sur 1 seul dataset
- ❌ Pas de réutilisabilité du code
- ❌ Pas de gestion d'erreurs robuste
- ❌ Sortie graphique (pas d'intégration API)
- ❌ Lent pour traiter plusieurs fichiers CSV

---

### ✅ **Code Transformé (Architecture Modulaire)**

#### **1. Structure du Projet**
```
PredictBudgets/
├── autoPrediction.py          # Classe SmartPredictor pour prédictions
├── dataSetPreduction.py       # Classe DataCleaner pour nettoyage
├── split_by_ordonateur.py     # Utilitaire : traitement par code
└── dataSets/                  # Dossier de données (flexible)
    ├── depensesEtat.csv
    └── ordonateurs/           # Sous-datasets par établissement
        ├── 146014.csv
        ├── 146029.csv
        └── ...
```

#### **2. Classe DataCleaner : Flexibilité d'Entrée**

**Avant :**
```python
df = pd.read_csv('./sample_data/depensesEtat.csv', sep=';')  # Chemin fixe
```

**Après :**
```python
class DataCleaner:
    def __init__(self, file_path):
        """Accepte n'importe quel fichier CSV"""
        self.file_path = file_path
    
    def run(self):
        """Pipeline flexible de nettoyage"""
        # 1️⃣ Détection auto du séparateur (';' ou ',')
        sep = self._detect_separator()
        
        # 2️⃣ Lecture flexible
        df = pd.read_csv(self.file_path, sep=sep)
        
        # 3️⃣ Nettoyage robuste
        df = self._clean_amounts()
        df = self._parse_dates()
        
        # 4️⃣ Agrégation intelligente
        df_monthly = self._aggregate_to_monthly()
        
        return df_monthly
```

**Avantages :**
- ✅ Accepte n'importe quel CSV (structure flexible)
- ✅ Détection auto du séparateur
- ✅ Gestion d'erreurs structurée
- ✅ Réutilisable pour tout dataset

#### **3. Classe SmartPredictor : Sélection Automatique du Modèle**

**Avant :**
```python
# Modèle hardcodé, pas d'analyse
model = SARIMAX(train_data['montant'], 
                order=(1, 1, 1),
                seasonal_order=(1, 1, 1, 12))
```

**Après :**
```python
class SmartPredictor:
    def analyze_and_configure(self):
        """Sélectionne le MEILLEUR modèle automatiquement"""
        
        # 1️⃣ TEST SAISONNALITÉ
        decomp = seasonal_decompose(self.df['montant'], period=12)
        has_seasonality = self._detect_seasonality(decomp)
        
        if has_seasonality:
            self.model_name = "SARIMA"
            self.order = (1, 1, 1)
            self.seasonal_order = (1, 1, 1, 12)
        else:
            # 2️⃣ TEST STATIONNARITÉ (ADF)
            p_value = adfuller(self.df['montant'])[1]
            
            if p_value > 0.05:
                # Non-stationnaire → ARIMA
                self.model_name = "ARIMA"
                self.order = (1, 1, 1)
            else:
                # 3️⃣ TOURNOI AR/MA/ARMA (AIC)
                # Compare les 3 et choisit le meilleur
                best_model = self._tournament_aic()
                self.model_name = best_model
    
    def get_prediction_data(self, months=12):
        """Retourne les données structurées (prêtes pour API/JSON)"""
        return {
            "model": self.model_name,
            "forecast": {
                "dates": [...],
                "values": [...],
                "confidence_upper": [...],
                "confidence_lower": [...]
            }
        }
```

**Avantages :**
- ✅ Choix du modèle **basé sur les données** (pas hardcodé)
- ✅ Saisonnalité ? → SARIMA
- ✅ Non-stationnaire ? → ARIMA
- ✅ Stationnaire ? → Tournoi AR/MA/ARMA
- ✅ Résultats structurés (JSON-ready)

---

## 🚀 Impact Pratique

### Cas d'usage : Traiter 100 fichiers CSV

**❌ Avec le code original :**
```python
# 100 fois copier-coller et modifier le chemin...
df = pd.read_csv('./depenses_2020.csv')
# ... traitement ...
df = pd.read_csv('./depenses_2021.csv')
# ... traitement ...
# (manuel, lent, erreur-prone)
```

**✅ Avec le code transformé :**
```python
import os
from dataSetPreduction import DataCleaner
from autoPrediction import SmartPredictor

# Boucle automatique sur tous les fichiers
for file in os.listdir('dataSets/ordonateurs/'):
    # Nettoyage automatique
    cleaner = DataCleaner(f'dataSets/ordonateurs/{file}')
    df_clean = cleaner.run()
    
    # Prédiction automatique
    predictor = SmartPredictor(df_clean)
    predictor.analyze_and_configure()
    result = predictor.get_prediction_data(months=12)
    
    # Sauvegarde structurée
    save_result(file, result)
```

**Gain :**
- ⏱️ **Automatisé** (pas de copier-coller)
- 📊 **Traitement par batch** (100 fichiers = 1 commande)
- 🔧 **Maintenable** (1 bug fix = 100 fichiers corrigés)

---

## 📐 Architecture Logique

```
┌─────────────────────┐
│   Fichier CSV       │
│   (n'importe lequel)│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│     DataCleaner.run()                   │
│  • Détecte séparateur                   │
│  • Nettoie montants (virgule → point)   │
│  • Parse dates (intelligent)            │
│  • Agrège journalier → mensuel          │
│  • Résultat : DataFrame propre          │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  SmartPredictor.analyze_and_configure() │
│  • Détecte saisonnalité ?               │
│  • Teste stationnarité (ADF) ?          │
│  • Tournoi AIC (AR vs MA vs ARMA) ?     │
│  • Résultat : Model choisi + ordre      │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ SmartPredictor.get_prediction_data()    │
│  • Entraîne le modèle final             │
│  • Génère prévisions + IC 95%           │
│  • Format JSON (structuré)              │
│  • Résultat : Dict{dates, values, ...}  │
└─────────────────────────────────────────┘
```

---

## 💾 Données vs Code

### Format de Sortie

**Avant :**
```python
# Graphique uniquement (pas de données)
plt.show()  # Fenêtre graphique
```

**Après :**
```python
{
    "model_info": {
        "name": "SARIMA",
        "order": "(1, 1, 1)",
        "seasonal_order": "(1, 1, 1, 12)"
    },
    "explanations": [
        "✓ Saisonnalité détectée",
        "Choix : SARIMA"
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
    }
}
```

**Avantages :**
- ✅ Données brutes (réutilisables)
- ✅ Format JSON (API-compatible)
- ✅ Transparence (explications incluses)

---

## 🔄 Évolution Future : TEST_API

Ce code sera transformé en **API REST** (FastAPI) dans la version `TEST_API` :

```python
from fastapi import FastAPI, UploadFile, File

app = FastAPI()

@app.post("/predict")
async def predict(file: UploadFile = File(...), months: int = 12):
    """
    POST /predict (Upload CSV)
    └─→ DataCleaner.run()
    └─→ SmartPredictor.analyze_and_configure()
    └─→ SmartPredictor.get_prediction_data()
    └─→ return JSON
    """
    file_content = await file.read()
    cleaner = DataCleaner(file_content)
    df_clean = cleaner.run()
    predictor = SmartPredictor(df_clean)
    predictor.analyze_and_configure()
    return predictor.get_prediction_data(months)
```

**Passage de PredictBudgets à TEST_API :**
- ✅ Même logique métier (DataCleaner + SmartPredictor)
- ✅ Interface HTTP (au lieu de console)
- ✅ Authentification (API Key)
- ✅ Prêt pour production (Docker, Cloud)

---

## 📊 Résumé des Améliorations

| Aspect | Avant (Notebook) | Après (Modulaire) |
|--------|---|---|
| **Flexibilité** | 1 dataset fixe | N datasets dynamiques |
| **Réutilisabilité** | Code dupliqué | Classes réutilisables |
| **Choix du modèle** | Hardcodé (SARIMA) | Auto-détecte + Tournoi AIC |
| **Gestion erreurs** | Aucune | Try/except robuste |
| **Format sortie** | Graphique (plt.show) | JSON structuré |
| **Performance** | 1 fichier = 5 min | Batch = parallélisable |
| **API-ready** | ❌ | ✅ (prête pour TEST_API) |

---

## 🛠️ Installation & Utilisation

```bash
# Clone le repo
git clone https://github.com/AymanTN1/autoPredictionTGR.git
cd PredictBudgets

# Installation dépendances
pip install -r requirements.txt

# Utilisation simple
from dataSetPreduction import DataCleaner
from autoPrediction import SmartPredictor

cleaner = DataCleaner('dataSets/depensesEtat.csv')
df = cleaner.run()

predictor = SmartPredictor(df)
predictor.analyze_and_configure()
result = predictor.get_prediction_data(months=12)

print(result)
```

---

## 📖 Fichiers Clés

- **`dataSetPreduction.py`** : Classe DataCleaner (nettoyage flexible)
- **`autoPrediction.py`** : Classe SmartPredictor (prédictions intelligentes)
- **`split_by_ordonateur.py`** : Utilitaire pour traiter par code établissement
- **`dataSets/`** : Dossier de données (structure flexible)

---

## 🎓 Conclusion

Ce projet démontre le passage d'un **script analytique** (Jupyter) à une **architecture logicielle** :
- ✅ Modulaire (réutilisable)
- ✅ Flexible (scalable)
- ✅ Robuste (gestion d'erreurs)
- ✅ API-ready (JSON output)

**Prochaine étape :** Transformation en **API REST** (version TEST_API) pour accès web et déploiement cloud.

---

**Version :** 1.0 (Transformation de code statique → Modulaire)  
**Date :** Janvier 2026  
**Objectif :** Préparation pour API REST et déploiement production
