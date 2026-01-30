# 🚀 API Prédiction v2.0 - Améliorations Majeures

**Date** : 29 Janvier 2026  
**Version** : 2.0.0 (Niveau Industriel)  
**Status** : ✅ Prêt pour production

---

## 📋 Résumé des 3 Améliorations Majeures

### ✨ 1. SMART DURATION (Gestion Intelligente de la Sparsity)

**Le Problème Résolu :**
```
❌ AVANT : CSV avec dates du 29-01-2020 ET 29-01-2026
   • Différence brute : 2192 jours = ~72 mois
   • Réalité : SEULEMENT 2 jours de données
   • Prédictions générées : PEU FIABLES (surapprendissage)
   • Intervalles de confiance : ÉNORMES (incertitude très haute)

✅ APRÈS : Détection automatique de la densité réelle
   • Compte les mois ACTIFS (montant > 0) = 2 mois
   • Calcule durée sûre = 2 / 3 = 0.67 → clamped à 3 mois
   • Prévisions générées : FIABLES (rapport données:paramètres acceptable)
   • Intervalles de confiance : MAÎTRISÉS
```

**L'Algorithme (4 Étapes) :**

```
ÉTAPE A : Détecter la sparsity
├─ Compter les mois WHERE montant > 0 (n_active)
├─ Calculer densité = (n_active / total_mois) * 100%
└─ Si densité < 20% : ⚠️  Alerter utilisateur

ÉTAPE B : Calculer durée sûre
├─ Formula : safe_duration = int(n_active / 3)
├─ Ratio 1/3 = règle statistique (3 observations par paramètre SARIMAX)
└─ Exemple : n_active=72 → safe=24 mois

ÉTAPE C : Appliquer les bornes
├─ Minimum : 3 mois (sinon pas assez de données)
├─ Maximum : 24 mois (sinon prévisions unreliable)
└─ safe_duration = clamp(safe_duration, 3, 24)

ÉTAPE D : Décider selon user_months
├─ Si None (MODE AUTO) : Retourner safe_duration ✅
├─ Si user_months > safe_duration : Réduire + Log 🔶 (sécurité > demande)
└─ Si user_months <= safe_duration : Approuver ✅
```

**Code (dans `logic.py`) :**
```python
def calculate_and_validate_duration(self, user_months=None):
    """
    Détecte la sparsity et valide la durée demandée.
    Retourne une durée sûre (3-24 mois).
    """
    # ÉTAPE A
    total_months = len(self.df)
    active_months = (self.df['montant'] > 0).sum()
    data_density = (active_months / total_months) * 100
    
    # ÉTAPE B
    safe_duration = int(active_months / 3)
    
    # ÉTAPE C
    safe_duration = max(3, min(safe_duration, 24))
    
    # ÉTAPE D
    if user_months is None:
        return safe_duration  # MODE AUTO
    elif user_months > safe_duration:
        log("✂️  Durée réduite par sécurité")
        return safe_duration  # Sécurité statistique
    else:
        return user_months  # Approuver demande utilisateur
```

**Logs Détaillés Générés :**
```
📈 Période couverte : 72 mois
📊 Mois ACTIFS (montant > 0) : 24
📉 Densité : 33.3%
🔢 Durée brute (active_months / 3) : 24 / 3 = 8 mois
📏 Après clamping [3, 24] : 8 mois
✅ MODE AUTO : Durée sélectionnée = 8 mois

OU (si user_months=36)

⚠️  SÉCURITÉ STATISTIQUE ✂️  Durée réduite
   • Demande : 36 mois
   • Limite sûre : 8 mois
   • Raison : Données insuffisantes pour prédire 36 mois
   • Décision : Utiliser 8 mois (rejette 36)
```

---

### 🔐 2. API Key (Sécurité d'Accès)

**Configuration :**
- **Clé statique** : `TGR-SECRET-KEY-12345` (peut être changée via env var)
- **Header requis** : `X-API-Key: TGR-SECRET-KEY-12345`
- **Routes protégées** : `/predict`, `/predict/auto`, `/predict/by-code`
- **Routes publiques** : `/`, `/health`, `/info`

**Implémentation (dans `main.py`) :**
```python
from fastapi import Depends, HTTPException, Header

def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """Dépendance FastAPI pour vérifier la clé API."""
    if x_api_key != API_KEY_SECRET:
        security_logger.warning("🚨 ACCÈS REFUSÉ : Clé API invalide")
        raise HTTPException(
            status_code=401,
            detail="❌ Clé API invalide ou absente. Header requis: X-API-Key"
        )
    security_logger.info("✅ Accès autorisé : Clé API valide")
    return x_api_key

# Utilisation sur une route
@app.post("/predict")
async def predict_upload(
    file: UploadFile,
    api_key: str = Depends(verify_api_key)  # ← Validation automatique
):
    ...
```

**Usage Client :**
```bash
# ✅ CORRECT (avec clé valide)
curl -X POST http://localhost:8000/predict \
  -H "X-API-Key: TGR-SECRET-KEY-12345" \
  -F "file=@data.csv"

# ❌ ERREUR (sans clé)
curl -X POST http://localhost:8000/predict \
  -F "file=@data.csv"
# → 401 Unauthorized

# ❌ ERREUR (clé invalide)
curl -X POST http://localhost:8000/predict \
  -H "X-API-Key: WRONG-KEY" \
  -F "file=@data.csv"
# → 401 Unauthorized
```

**Logging Sécurité :**
```
security.log :
2026-01-29 15:30:45 | INFO | ✅ Accès autorisé : Clé API valide
2026-01-29 15:31:12 | WARNING | 🚨 ACCÈS REFUSÉ : Clé API invalide
2026-01-29 15:31:45 | INFO | ✅ Prédiction réussie : SARIMA, 12 mois
```

---

### 📊 3. Mode AUTO vs MODE UTILISATEUR (API Hybride)

**Avant (v1.0) :**
```python
@app.post("/predict")
async def predict_upload(
    file: UploadFile,
    months: int = Query(12, ge=1, le=60)  # ← OBLIGATOIRE
):
    ...
```
❌ Problème : Utilisateur DOIT spécifier une durée

**Après (v2.0) :**
```python
@app.post("/predict")
async def predict_upload(
    file: UploadFile,
    months: Optional[int] = Query(None, ge=1, le=60),  # ← OPTIONNEL
    api_key: str = Depends(verify_api_key)
):
    # months peut être None (MODE AUTO) ou int (MODE UTILISATEUR)
    result = predict_from_file_content(file_content, months=months)
```

✅ Avantages :
- **MODE AUTO** : `months=None` → Système décide automatiquement
- **MODE UTILISATEUR** : `months=24` → Utilisateur contrôle, système valide

**3 Routes Disponibles :**

| Route | Paramètre `months` | Comportement |
|-------|-------------------|---|
| `POST /predict` | Optional[int] = None | **HYBRIDE** : Utilisateur peut spécifier OU laisser vide |
| `POST /predict/auto` | Aucun | **AUTO** : Toujours mode automatique |
| `POST /predict/by-code` | Optional[int] = None | **HYBRIDE** : (code='146014' requis) |

**Exemples d'Usage :**

```bash
# 1️⃣  MODE AUTO (recommandé pour démarrer)
curl -X POST http://localhost:8000/predict/auto \
  -H "X-API-Key: TGR-SECRET-KEY-12345" \
  -F "file=@data.csv"

# Réponse :
{
  "duration_info": {
    "requested_months": null,
    "validated_months": 12,
    "reason": "MODE AUTO"
  }
}

# 2️⃣  MODE UTILISATEUR (demande 24 mois)
curl -X POST http://localhost:8000/predict \
  -H "X-API-Key: TGR-SECRET-KEY-12345" \
  -F "file=@data.csv" \
  -F "months=24"

# Réponse :
{
  "duration_info": {
    "requested_months": 24,
    "validated_months": 12,  # ← Peut être réduit
    "reason": "USER OVERRIDE (24 → 12)"
  }
}

# 3️⃣  MODE HYBRIDE (utiliser /predict sans months = AUTO)
curl -X POST http://localhost:8000/predict \
  -H "X-API-Key: TGR-SECRET-KEY-12345" \
  -F "file=@data.csv"
  # SANS paramètre months → MODE AUTO par défaut
```

---

## 🛡️ Sécurité Bonus (Niveau Industriel)

### 1️⃣ Input Validation (Payload Limit)
```python
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB max

if len(file_content) > MAX_FILE_SIZE:
    raise ValueError(f"🚫 Fichier trop volumineux")
```

### 2️⃣ Logging de Sécurité
```python
# security.log enregistre :
# - Toutes les tentatives d'accès avec clé invalide
# - Toutes les prédictions réussies
# - Tous les fichiers rejetés
# - Toutes les erreurs système
```

### 3️⃣ Validation CSV Automatique
```python
# DataCleaner valide :
# - Présence colonnes date et montant
# - Format des dates (intelligemment : dayfirst=True pour français)
# - Conversion montants (virgule décimale → point)
# - Suppression NaN et valeurs invalides
```

---

## 📊 Réponse JSON v2.0 (Enrichie)

**Succès (200) :**
```json
{
  "status": "success",
  "model_info": {
    "name": "SARIMA",
    "order": "(1, 1, 1)",
    "seasonal_order": "(1, 1, 1, 12)",
    "aic": 1909.31
  },
  "duration_info": {
    "requested_months": null,
    "validated_months": 12,
    "reason": "MODE AUTO"
  },
  "history": {
    "dates": ["2020-01-01", "2020-02-01", ...],
    "values": [1000.0, 1500.5, ...]
  },
  "forecast": {
    "dates": ["2025-01-01", "2025-02-01", ...],
    "values": [1400.0, 1450.0, ...],
    "confidence_upper": [1500.0, 1550.0, ...],
    "confidence_lower": [1300.0, 1350.0, ...]
  },
  "explanations": [
    "✓ Validation taille : 26.5 MB (< 50 MB)",
    "📈 Période couverte : 72 mois",
    "📊 Densité : 33.3%",
    "✂️  Durée réduite par sécurité",
    "✓ Saisonnalité détectée",
    "✓ Choix : SARIMA",
    "✓ Modèle entraîné (AIC=1909.31)"
  ],
  "timestamp": "2026-01-29T15:30:45.123456"
}
```

**Erreur Authentification (401) :**
```json
{
  "detail": "❌ Clé API invalide ou absente. Header requis: X-API-Key"
}
```

**Erreur Traitement (400) :**
```json
{
  "status": "error",
  "error_message": "Impossible de trouver colonnes Date/Montant",
  "details": "Erreur lors du traitement du fichier"
}
```

---

## 🧪 Tests & Démonstration

**Script de test complet :**
```bash
python test_v2_smart_duration.py
```

**Tests inclus :**
1. ✨ MODE AUTO (Smart Duration automatique)
2. 🔐 MODE UTILISATEUR (avec validation)
3. 🔒 Sécurité API Key (clé invalide)
4. 🏥 Health Check (public)
5. 📊 Comparaison AUTO vs UTILISATEUR

---

## 🚀 Déploiement

**Démarrer l'API :**
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Swagger UI (pour tester) :**
```
http://localhost:8000/docs
```

**Documentation OpenAPI :**
```
http://localhost:8000/openapi.json
```

---

## 📚 Prochaines Améliorations (Roadmap)

| Étape | Feature | Impact | Effort |
|-------|---------|--------|--------|
| ⭐ | Rate Limiting (SlowAPI) | Prévient abus | 2h |
| ⭐⭐ | JWT Tokens (avec expiration) | Sécurité avancée | 4h |
| ⭐⭐ | Base de données (historique) | Auditabilité | 8h |
| ⭐⭐⭐ | Prédictions par code_ordinateur | Multi-entités | 6h |
| ⭐⭐⭐ | Retraining automatique | ML-Ops | 12h |

---

## 🎯 Résumé pour le Rapport de Stage

**Points clés à mentionner :**

✨ **Intelligence Métier (Smart Duration)**
- Détection automatique de la sparsity des données
- Calcul d'une durée sûre basée sur la densité réelle
- Protection contre les prédictions sur-paramétrées

🔐 **Sécurité (API Key)**
- Authentification par clé API via header HTTP
- Logging détaillé de toutes les tentatives d'accès
- Protection des routes sensibles contre l'accès non-autorisé

📊 **Flexibilité (Mode AUTO/UTILISATEUR)**
- MODE AUTO : Système décide automatiquement (idéal pour l'automatisation)
- MODE UTILISATEUR : Contrôle utilisateur, validé par sécurité statistique
- Routes hybrides : Même endpoint peut fonctionner dans les deux modes

🛡️ **Validation Robuste**
- Limite de taille fichier (50 MB)
- Détection automatique des colonnes
- Conversion intelligente des formats (français : virgule → point)
- Suppression automatique des données invalides

---

## 📖 Documentation Complète

Voir les docstrings détaillés dans :
- `logic.py` : Classe `SmartPredictor.calculate_and_validate_duration()`
- `main.py` : Dépendance `verify_api_key()` et routes `/predict`
- `test_v2_smart_duration.py` : Exemples d'usage complet

---

**Version** : 2.0.0  
**Auteur** : TGR API Team  
**Date de Publication** : 29 Janvier 2026  
**Statut** : ✅ Production Ready
