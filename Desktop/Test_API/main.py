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

from logic import predict_from_file_content

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
        "models_available": ["AR", "MA", "ARMA", "ARIMA", "SARIMA"],
        "selection_method": "AIC Tournament + Stationarity Test",
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
    4. ✓ Choisir le meilleur modèle (AR, MA, ARMA, ARIMA ou SARIMA)
    5. ✓ Générer les prévisions avec intervalles de confiance
    
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
    - `duration_info` : Explications sur la durée choisie
    - `explanations` : Logs détaillés de toute l'analyse
    """
    
    try:
        # Valider et lire le fichier
        file_content = await file.read()
        
        # Appeler le moteur de prédiction avec mode HYBRIDE
        # (months peut être None pour MODE AUTO)
        result = predict_from_file_content(file_content, months=months)
        
        # Si le moteur signale une erreur, renvoyer un code 400 pour que les tests
        # et les clients puissent réagir correctement.
        if result.get("status") != "success":
            logger.warning(f"Prediction engine returned error: {result.get('error_message')}")
            return JSONResponse(status_code=400, content=result)

        # Log sécurité en cas de succès
        logger.info(f"✅ Prédiction réussie : {result['model_info']['name']}, {result['duration_info']['validated_months']} mois")
        
        return result
        
    except Exception as e:
        # Log erreur en sécurité
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

        logger.info(f"✅ Prédiction AUTO réussie : {result['model_info']['name']}")
        
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
    
    Utile si vous avez un grand fichier groupé et voulez prédire pour
    un établissement particulier identifié par son code.
    
    **Paramètres :**
    - `code` : Code ordinateur/établissement (ex: "146014")
    - `months` : Nombre de mois à prédire (optionnel)
    - `file` : Fichier CSV complet
    
    **Note :** Cette version nécessite qu'il existe une colonne "code_ordinateur"
    dans le fichier d'entrée.
    """
    
    try:
        file_content = await file.read()
        logger.info(f"ℹ️  Prédiction par code non encore implémentée : {code}")
        
        return {
            "status": "coming_soon",
            "message": "Prédiction par code ordinateur en développement",
            "code": code,
            "requested_months": months
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur /predict/by-code : {str(e)}")
        
        return JSONResponse(
            status_code=400,
            content={"status": "error", "error_message": str(e)}
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
