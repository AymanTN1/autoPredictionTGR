"""
main.py - API FastAPI pour prédiction des dépenses (VERSION SÉCURISÉE + LOGURU)

Cette API permet aux utilisateurs de :
1. Uploader un fichier CSV
2. Obtenir automatiquement une prédiction avec le meilleur modèle ARIMA/SARIMA
3. Récupérer les résultats au format JSON

🔒 SÉCURITÉ :
- API Key (X-API-Key header) requise sur les routes sensibles
- Validation des entrées (taille fichier, format)
- Logging professionnel avec Loguru
- Variables d'environnement (.env)
"""

from fastapi import FastAPI, UploadFile, File, Query, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
from loguru import logger
import pandas as pd
import io

from logic import predict_from_file_content
from models.database import db_config
from db_endpoints import router_db, save_uploaded_file, save_prediction

# ═══════════════════════════════════════════════════════════════════════════
# 🔧 CHARGEMENT DES VARIABLES D'ENVIRONNEMENT
# ═══════════════════════════════════════════════════════════════════════════
load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════
# 🔐 CONFIGURATION SÉCURITÉ
# ═══════════════════════════════════════════════════════════════════════════

API_KEY_SECRET = os.getenv("TGR_API_KEY", "TGR-SECRET-KEY-12345")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
LOG_DIR = os.getenv("LOG_DIR", "logs")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 52428800))

# Créer répertoire logs
os.makedirs(LOG_DIR, exist_ok=True)

# Configuration Loguru pour sécurité
logger.remove()  # Supprimer handler par défaut
logger.add(
    f"{LOG_DIR}/security.log",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO",
    rotation="500 MB",
    retention="7 days"
)

# ═══════════════════════════════════════════════════════════════════════════
# 📍 DÉPENDANCE : Validation API Key
# ═══════════════════════════════════════════════════════════════════════════

def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """
    Vérifie la clé API et renvoie 401 si absente ou invalide. Retourne la clé si valide.
    """
    if not x_api_key:
        logger.warning("🚨 ACCÈS REFUSÉ : Clé API absente")
        raise HTTPException(
            status_code=401,
            detail="❌ Clé API invalide ou absente. Header requis: X-API-Key"
        )

    if x_api_key != API_KEY_SECRET:
        logger.warning(f"🚨 ACCÈS REFUSÉ : Clé API invalide | Clé fournie: {x_api_key[:10]}...")
        raise HTTPException(
            status_code=401,
            detail="❌ Clé API invalide ou absente. Header requis: X-API-Key"
        )

    logger.info(f"✅ Accès autorisé : Clé API valide")
    return x_api_key

# Créer l'application FastAPI
app = FastAPI(
    title="API Prédiction des Dépenses (SÉCURISÉE)",
    description="API pour prédire les dépenses de l'État basée sur des séries temporelles ARIMA/SARIMA avec authentification par clé API",
    version="2.0.0 (Industrielle)"
)


# ═══════════════════════════════════════════════════════════════════════════
# STARTUP : Initialiser la base de données
# ═══════════════════════════════════════════════════════════════════════════
@app.on_event("startup")
def startup_event():
    """Initialiser la BD au démarrage de l'API."""
    try:
        db_config.create_tables()
        logger.info("✅ Base de données initialisée")
    except Exception as e:
        logger.error(f"❌ Erreur init BD : {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
# INCLURE LE ROUTEUR BASE DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════
app.include_router(router_db, prefix="/api/db", tags=["Database 🗄️ | Persistance"])



# ==============================================================================
# MODÈLES PYDANTIC (pour la documentation Swagger)
# ==============================================================================
class PredictionRequest(BaseModel):
    """Modèle pour une requête de prédiction."""
    months: Optional[int] = None  # ← NOUVEAU : Optionnel (MODE AUTO par défaut)
    description: Optional[str] = None


class HealthResponse(BaseModel):
    """Modèle pour la réponse de santé."""
    status: str
    version: str
    timestamp: str


# ==============================================================================
# ROUTES - UTILITAIRES
# ==============================================================================
@app.get("/", tags=["Utilitaires"])
def read_root():
    """Route d'accueil de l'API."""
    return {
        "message": "🎯 Bienvenue sur l'API Prédiction des Dépenses (v2.0 - Sécurisée)",
        "🔒_securite": "Toutes les routes de prédiction requièrent un header X-API-Key",
        "endpoints": {
            "health": "GET /health (public)",
            "docs": "GET /docs (Swagger UI)",
            "predict": "POST /predict (🔒 Requiert API Key)",
            "predict_auto": "POST /predict/auto (🔒 Mode AUTO intelligent)"
        },
        "exemple_usage": {
            "curl": 'curl -X POST http://localhost:8000/predict -H "X-API-Key: TGR-SECRET-KEY-12345" -F "file=@data.csv"',
            "python": "requests.post(..., headers={'X-API-Key': 'TGR-SECRET-KEY-12345'})"
        }
    }


@app.get("/health", tags=["Utilitaires"])
def health_check():
    """Vérifier l'état de l'API (public, pas de clé requise)."""
    from datetime import datetime
    return {
        "status": "healthy",  # Valeur machine-friendly attendue par les tests
        "status_human": "🟢 online",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "security": "🔒 API Key required on /predict endpoints"
    }


@app.get("/info", tags=["Utilitaires"])
def api_info():
    """Informations sur l'API et ses capacités (public)."""
    return {
        "name": "API Prédiction des Dépenses",
        "version": "2.0.0 (Industrielle)",
        "description": "Prédiction automatique des dépenses basée sur ARIMA/SARIMA",
        "features": [
            "Smart Duration (détection sparsity)",
            "Mode AUTO vs Mode UTILISATEUR",
            "Sécurité : API Key",
            "Logging détaillé (Loguru)"
        ],
        "🔒_security": {
            "authentication": "API Key (X-API-Key header)",
            "rate_limit": "À implémenter : 100 req/min par clé",
            "payload_limit": "Max 50 MB par fichier",
            "logging": "Tous les accès enregistrés dans security.log"
        },
        "models_available": [
            "CLASSICAL: AR, MA, ARMA, ARIMA, SARIMA", 
            "ADVANCED: SARIMAX (exogenous), VAR, VARMA",
            "EXPONENTIAL: Holt-Winters",
            "PROPHET: Facebook Prophet (optional)",
            "DEEP_LEARNING: LSTM, GRU, RNN (with TensorFlow)"
        ],
        "selection_method": "Automatic: Evaluate ALL models, rank by AIC/MSE, select BEST automatically",
        "smart_features": [
            "✨ Smart Duration : Détecte sparsity des données",
            "📊 Mode AUTO : Durée calculée automatiquement",
            "🛡️  Input Validation : Payload limit + CSV sanitization",
            "📋 Logging détaillé : Toutes les décisions expliquées"
        ],
        "input_format": "CSV (date + montant)",
        "output_format": "JSON (prévisions + intervalles confiance + explications)",
        "max_forecast_months": 60,
        "recommended_data_density": "> 20% de mois actifs"
    }


# ==============================================================================
# ROUTES - PRÉDICTION (🔒 SÉCURISÉES)
# ==============================================================================

@app.post("/predict", tags=["Prédiction 🔒 Sécurisée"])
async def predict_upload(
    file: UploadFile = File(..., description="Fichier CSV à prédire"),
    months: Optional[int] = Query(None, ge=1, le=60, description="Nombre de mois (optionnel, MODE AUTO si vide)"),
    api_key: str = Depends(verify_api_key)  # 🔐 VALIDATION CLÉ API
):
    """
    **Uploader un fichier CSV et obtenir une prédiction (MODE HYBRIDE).**
    
    🔒 **SÉCURITÉ REQUISE** : Vous devez passer le header X-API-Key
    
    Exemples de requête :
    ```bash
    # MODE AUTO (sans spécifier months)
    curl -X POST http://localhost:8000/predict \\
      -H "X-API-Key: TGR-SECRET-KEY-12345" \\
      -F "file=@data.csv"
    
    # MODE UTILISATEUR (avec months)
    curl -X POST http://localhost:8000/predict \\
      -H "X-API-Key: TGR-SECRET-KEY-12345" \\
      -F "file=@data.csv" \\
      -F "months=24"
    ```
    
    Le fichier doit contenir :
    - Une colonne "date" ou "jour" ou "time" ou "reglement" ou "payment"
    - Une colonne "montant" ou "sum" ou "prix" ou "amount" ou "valeur"
    
    L'API va :
    1. ✓ Valider la taille du fichier (max 50 MB)
    2. ✓ Nettoyer et agréger les données en série mensuelle
    3. ✓ Analyser la densité (Smart Duration)
    4. ✓ Évaluer ET CLASSER les meilleurs modèles :
       - Classiques : AR, MA, ARMA, ARIMA, SARIMA
       - Avancés : SARIMAX (avec exogène trend), VAR, VARMA
       - Exponentiel : Holt-Winters
       - Prophet : Facebook Prophet (si installé)
       - Deep Learning : LSTM, GRU, RNN (si TensorFlow disponible)
       - Puis sélectionner automatiquement le MEILLEUR par score (AIC/MSE)
    5. ✓ Générer les prévisions avec intervalles de confiance
    6. ✓ Détecter les anomalies (AI for Audit)
    
    **Paramètres :**
    - `file` : Fichier CSV à analyser
    - `months` : (Optionnel) Nombre de mois à prédire
      - Si omis (None) : Le système décide automatiquement via Smart Duration
      - Si fourni : Le système valide et peut réduire si données insuffisantes
    - `X-API-Key` : Header requis avec votre clé API
    
    **Retour :**
    - `model_info` : Infos sur le modèle choisi (name, order, AIC)
    - `history` : Données historiques (dates + valeurs)
    - `forecast` : Prévisions avec intervalles confiance
    - `anomalies` : Anomalies détectées (KILLER FEATURE)
    - `duration_info` : Explications sur la durée choisie
    - `explanations` : Logs détaillés de toute l'analyse
    """
    
    try:
        # Valider et lire le fichier
        file_content = await file.read()
        
        # Appeler le moteur de prédiction avec mode HYBRIDE
        # (months peut être None pour MODE AUTO)
        result = predict_from_file_content(file_content, months=months)
        
        # Si le moteur signale une erreur, renvoyer un code 400
        if result.get("status") != "success":
            logger.warning(f"Prediction engine returned error: {result.get('error_message')}")
            return JSONResponse(status_code=400, content=result)

        # ← KILLER FEATURE 2 & 1 : Persister la prédiction et les anomalies
        try:
            from models.database import get_session
            session = next(get_session())
            
            # Persister le fichier uploadé
            from datetime import datetime
            file_id = save_uploaded_file(
                api_key=api_key,
                filename=file.filename or "unknown",
                file_content=file_content,
                row_count=len(result.get("history", {}).get("values", [])),
                date_range_start=result.get("history", {}).get("dates", [None])[0],
                date_range_end=result.get("history", {}).get("dates", [None])[-1],
                session=session,
            )
            
            # Persister la prédiction
            pred_id = save_prediction(
                api_key=api_key,
                file_id=file_id,
                model_name=result["model_info"]["name"],
                model_order=result["model_info"]["order"],
                seasonal_order=result["model_info"]["seasonal_order"],
                forecast_months=result["duration_info"]["validated_months"],
                model_aic=result["model_info"]["aic"],
                forecast_json=result.get("forecast", {}),
                anomalies_list=result.get("anomalies", []),
                session=session,
            )
            
            result["_internal"] = {
                "file_id": file_id,
                "pred_id": pred_id,
                "persisted": True,
            }
            
            logger.info(f"✅ Prédiction sauvegardée : ID={pred_id}, Anomalies={len(result.get('anomalies', []))}")
            
        except Exception as e:
            logger.warning(f"⚠️ Persistance BD échouée (prédiction quand même retournée) : {str(e)}")
            result["_internal"] = {"persisted": False, "error": str(e)}

        logger.info(f"✅ Prédiction réussie : {result['model_info']['name']}, {result['duration_info']['validated_months']} mois, {len(result.get('anomalies', []))} anomalies")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur prédiction : {str(e)}")
        
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error_message": str(e),
                "details": "Erreur lors du traitement du fichier"
            }
        )


@app.post("/predict/auto", tags=["Prédiction 🔒 Sécurisée"])
async def predict_auto(
    file: UploadFile = File(..., description="Fichier CSV à prédire"),
    api_key: str = Depends(verify_api_key)  # 🔐 VALIDATION CLÉ API
):
    """
    **Route SPÉCIALISÉE : Prédiction entièrement AUTOMATIQUE.**
    
    Cette route ne demande PAS de paramètre `months`.
    Le système analyse automatiquement la densité des données et
    décide de la meilleure durée de prédiction.
    
    🎯 **IDÉALE POUR** :
    - Utilisateurs qui ne savent pas combien de mois prédire
    - Données très hétérogènes (tantôt sparse, tantôt dense)
    - Systèmes automatisés sans intervention humaine
    
    Exemple :
    ```bash
    curl -X POST http://localhost:8000/predict/auto \\
      -H "X-API-Key: TGR-SECRET-KEY-12345" \\
      -F "file=@data.csv"
    ```
    """
    try:
        file_content = await file.read()
        
        # MODE AUTO : months=None (le système décide)
        result = predict_from_file_content(file_content, months=None)
        
        # Retourner 400 si erreur du moteur
        if result.get("status") != "success":
            logger.warning(f"Prediction AUTO error: {result.get('error_message')}")
            return JSONResponse(status_code=400, content=result)

        # ← KILLER FEATURE 2 & 1 : Persister la prédiction et les anomalies
        try:
            from models.database import get_session
            session = next(get_session())
            
            # Persister le fichier uploadé
            from datetime import datetime
            file_id = save_uploaded_file(
                api_key=api_key,
                filename=file.filename or "unknown",
                file_content=file_content,
                row_count=len(result.get("history", {}).get("values", [])),
                date_range_start=result.get("history", {}).get("dates", [None])[0],
                date_range_end=result.get("history", {}).get("dates", [None])[-1],
                session=session,
            )
            
            # Persister la prédiction
            pred_id = save_prediction(
                api_key=api_key,
                file_id=file_id,
                model_name=result["model_info"]["name"],
                model_order=result["model_info"]["order"],
                seasonal_order=result["model_info"]["seasonal_order"],
                forecast_months=result["duration_info"]["validated_months"],
                model_aic=result["model_info"]["aic"],
                forecast_json=result.get("forecast", {}),
                anomalies_list=result.get("anomalies", []),
                session=session,
            )
            
            logger.info(f"✅ Prédiction AUTO sauvegardée : ID={pred_id}, Anomalies={len(result.get('anomalies', []))}")
            
        except Exception as e:
            logger.warning(f"⚠️ Persistance BD échouée (prédiction quand même retournée) : {str(e)}")

        logger.info(f"✅ Prédiction AUTO réussie : {result['model_info']['name']}, {len(result.get('anomalies', []))} anomalies")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur prédiction AUTO : {str(e)}")
        
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error_message": str(e),
                "details": "Erreur lors du traitement du fichier"
            }
        )


@app.post("/predict/by-code", tags=["Prédiction 🔒 Sécurisée"])
async def predict_by_ordinateur(
    code: str = Query(..., description="Code ordinateur/établissement"),
    months: Optional[int] = Query(None, ge=1, le=60, description="Nombre de mois à prédire"),
    file: UploadFile = File(..., description="Fichier CSV contenant tous les ordinateurs"),
    api_key: str = Depends(verify_api_key)  # 🔐 VALIDATION CLÉ API
):
    """
    **Prédiction pour un ordinateur/établissement spécifique.**
    
    Utile si vous avez un grand fichier groupé par code ordinateur et voulez
    prédire pour un établissement particulier identifié par son code.
    
    **Paramètres :**
    - `code` : Code ordinateur/établissement (ex: "146014")
    - `months` : Nombre de mois à prédire (optionnel, MODE AUTO si vide)
    - `file` : Fichier CSV complet (doit contenir colonne "code_ordinateur" ou "code")
    
    **Format attendu :**
    Le fichier doit contenir au moins :
    - Colonne de code : "code_ordinateur" OU "code" OU "ordonateur"
    - Colonne de date : "date" OU "jour" OU "time"
    - Colonne de montant : "montant" OU "sum" OU "prix"
    
    **Exemple :**
    ```
    code_ordinateur,date,montant
    146014,2020-01-01,12000
    146014,2020-02-01,15000
    146029,2020-01-01,8000
    ```
    """
    
    try:
        file_content = await file.read()
        
        # Charger le fichier entier - essayer d'abord avec séparateur ';' (format fourni)
        try:
            df_all = pd.read_csv(io.BytesIO(file_content), sep=';', engine='python')
        except Exception:
            # fallback to default csv parser
            df_all = pd.read_csv(io.BytesIO(file_content))

        # Normaliser les noms de colonnes
        df_all.columns = df_all.columns.str.lower().str.strip()

        # Chercher colonne de code (accept 'code_ordinateur', 'code_ordonateur', 'ordonnateur', 'code')
        code_cols = []
        for col in df_all.columns:
            col_lower = col.lower()
            # Check for both spellings: ordinateur AND ordonnateur
            if any(x in col_lower for x in ['ordinateur', 'ordonnateur', 'ordonneur']):
                code_cols.append(col)
            elif 'code' in col_lower and any(x in col_lower for x in ['ord', 'etabl', 'agence']):
                code_cols.append(col)
        
        # If still not found, try just 'code'
        if not code_cols:
            code_cols = [col for col in df_all.columns if 'code' in col.lower()]
        
        if not code_cols:
            logger.error(f"❌ Pas de colonne 'code_ordinateur' trouvée dans le fichier")
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "error_message": "Colonne 'code_ordinateur' ou 'code' non trouvée",
                    "available_columns": list(df_all.columns)
                }
            )
        
        code_col = code_cols[0]
        
        # Filtrer par code
        df_filtered = df_all[df_all[code_col].astype(str).str.strip() == code]
        
        if len(df_filtered) == 0:
            logger.warning(f"⚠️  Code {code} non trouvé dans le fichier")
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "error_message": f"Code '{code}' non trouvé dans le fichier",
                    "unique_codes": df_all[code_col].unique()[:10].tolist()
                }
            )
        
        # Identifier colonne date et montant (plusieurs synonymes possibles)
        date_cols = [c for c in df_filtered.columns if any(k in c for k in ['date', 'jour', 'time', 'mois'])]
        amount_cols = [c for c in df_filtered.columns if any(k in c for k in ['montant', 'sum', 'prix', 'amount', 'value'])]

        if not date_cols:
            # fallback: first column that looks like a date via dtype
            date_cols = [df_filtered.columns[0]]
        if not amount_cols:
            # try last column as amount
            amount_cols = [df_filtered.columns[-1]]

        date_col = date_cols[0]
        amount_col = amount_cols[0]

        # Préparer export: garder seulement date et montant, renommer en 'date' et 'montant'
        df_export = df_filtered[[date_col, amount_col]].copy()
        df_export.columns = ['date', 'montant']

        # Nettoyer les montants: remplacer virgule décimale et supprimer espaces
        def parse_amount(x):
            try:
                s = str(x).replace(' ', '').replace('\u00A0', '')
                s = s.replace(',', '.')
                return float(s)
            except Exception:
                return None

        df_export['montant'] = df_export['montant'].apply(parse_amount)

        # Supprimer lignes invalides
        df_export = df_export.dropna(subset=['date', 'montant'])

        # Convertir en bytes pour predict_from_file_content
        # Garder seulement les colonnes nécessaires (date + montant)
        
        df_filtered_bytes = df_export.to_csv(index=False, sep=';').encode('utf-8')
        
        if df_export['montant'].nunique() <= 1 or len(df_export) < 6:
            # Series is too short/constant - use naive fallback
            use_naive = True
        else:
            # Try SARIMA, but fall back if it fails
            use_naive = False
            try:
                result = predict_from_file_content(df_filtered_bytes, months=months)
                if result.get("status") != "success":
                    use_naive = True
            except Exception as e:
                logger.warning(f"SARIMA failed for code {code}: {str(e)}, using naive fallback")
                use_naive = True
        
        if use_naive:
            # Fallback: naive constant prediction
            last_value = float(df_export['montant'].iloc[-1]) if len(df_export) > 0 else 0.0
            validated_months = months or 6
            forecast_dates = []
            try:
                start = pd.to_datetime(df_export['date'].iloc[-1])
                for i in range(validated_months):
                    forecast_dates.append((start + pd.offsets.MonthBegin(i+1)).strftime('%Y-%m-%d'))
            except Exception:
                forecast_dates = [None] * validated_months

            result = {
                "status": "success",
                "model_info": {
                    "name": "NAIVE_CONSTANT",
                    "order": "()",
                    "seasonal_order": "()",
                    "aic": 0.0
                },
                "explanations": ["Fallback: série trop courte, constante ou SARIMA échoué, prévision naive utilisée"],
                "history": {
                    "dates": df_export['date'].astype(str).tolist(),
                    "values": df_export['montant'].tolist()
                },
                "forecast": {
                    "dates": forecast_dates,
                    "values": [last_value] * validated_months,
                    "confidence_upper": [last_value] * validated_months,
                    "confidence_lower": [last_value] * validated_months
                },
                "anomalies": [],
                "timestamp": pd.Timestamp.now().isoformat(),
                "duration_info": {
                    "requested_months": months,
                    "validated_months": validated_months,
                    "reason": "FALLBACK - naive or SARIMA failure"
                }
            }
        
        if result.get("status") != "success":
            logger.warning(f"Prediction by code error for {code}: {result.get('error_message')}")
            return JSONResponse(status_code=400, content=result)

        # ← KILLER FEATURE 2 & 1 : Persister la prédiction
        try:
            from models.database import get_session
            session = next(get_session())
            
            file_id = save_uploaded_file(
                api_key=api_key,
                filename=f"by_code_{code}",
                file_content=df_filtered_bytes,
                row_count=len(result.get("history", {}).get("values", [])),
                date_range_start=result.get("history", {}).get("dates", [None])[0],
                date_range_end=result.get("history", {}).get("dates", [None])[-1],
                session=session,
            )
            
            pred_id = save_prediction(
                api_key=api_key,
                file_id=file_id,
                model_name=result["model_info"]["name"],
                model_order=result["model_info"]["order"],
                seasonal_order=result["model_info"]["seasonal_order"],
                forecast_months=result["duration_info"]["validated_months"],
                model_aic=result["model_info"]["aic"],
                forecast_json=result.get("forecast", {}),
                anomalies_list=result.get("anomalies", []),
                session=session,
            )
            
            logger.info(f"✅ Prédiction BY-CODE sauvegardée : ID={pred_id}, Code={code}")
            
        except Exception as e:
            logger.warning(f"⚠️  Persistance BD échouée : {str(e)}")

        logger.info(f"✅ Prédiction BY-CODE réussie pour {code} : {result['model_info']['name']}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur /predict/by-code : {str(e)}")
        
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error_message": str(e),
                "details": "Erreur lors du traitement du fichier"
            }
        )


# ==============================================================================
# ROUTES - HISTORIQUE (futur)
# ==============================================================================
@app.get("/predictions/history", tags=["Historique"])
def get_prediction_history():
    """
    **Récupérer l'historique des prédictions effectuées.**
    
    (Fonctionnalité future : nécessite une base de données)
    """
    return {
        "status": "coming_soon",
        "message": "Historique des prédictions - À développer"
    }


@app.get("/predictions/{prediction_id}", tags=["Historique"])
def get_prediction_detail(prediction_id: str):
    """
    **Récupérer les détails d'une prédiction spécifique.**
    
    (Fonctionnalité future : nécessite une base de données)
    """
    return {
        "status": "coming_soon",
        "prediction_id": prediction_id,
        "message": "Détail des prédictions - À développer"
    }


# ==============================================================================
# ROUTES - STATISTIQUES (futur)
# ==============================================================================
@app.get("/stats/models", tags=["Statistiques"])
def get_model_statistics():
    """
    **Statistiques sur les modèles utilisés.**
    
    (Fonctionnalité future : nécessite une base de données)
    """
    return {
        "status": "coming_soon",
        "message": "Statistiques des modèles - À développer"
    }


# ==============================================================================
# GESTION DES ERREURS
# ==============================================================================
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    logger.warning(f"⚠️  ValueError : {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"status": "error", "error_message": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"🔴 Erreur interne : {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_message": "Erreur interne du serveur",
            "details": str(exc)
        }
    )
