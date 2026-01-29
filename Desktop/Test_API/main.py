"""
main.py - API FastAPI pour prédiction des dépenses

Cette API permet aux utilisateurs de :
1. Uploader un fichier CSV
2. Obtenir automatiquement une prédiction avec le meilleur modèle ARIMA/SARIMA
3. Récupérer les résultats au format JSON
"""

from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import os

from logic import predict_from_file_content

# Créer l'application FastAPI
app = FastAPI(
    title="API Prédiction des Dépenses",
    description="API pour prédire les dépenses de l'État basée sur des séries temporelles ARIMA/SARIMA",
    version="1.0.0"
)


# ==============================================================================
# MODÈLES PYDANTIC (pour la documentation Swagger)
# ==============================================================================
class PredictionRequest(BaseModel):
    """Modèle pour une requête de prédiction."""
    months: int = 12
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
        "message": "Bienvenue sur l'API Prédiction des Dépenses",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "predict": "/predict"
        }
    }


@app.get("/health", tags=["Utilitaires"])
def health_check():
    """Vérifier l'état de l'API."""
    from datetime import datetime
    return {
        "status": "online",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/info", tags=["Utilitaires"])
def api_info():
    """Informations sur l'API et ses capacités."""
    return {
        "name": "API Prédiction des Dépenses",
        "version": "1.0.0",
        "description": "Prédiction automatique des dépenses basée sur ARIMA/SARIMA",
        "models_available": ["AR", "MA", "ARMA", "ARIMA", "SARIMA"],
        "selection_method": "AIC Tournament + Stationarity Test",
        "input_format": "CSV (date + montant)",
        "output_format": "JSON (prévisions + intervalles confiance)",
        "max_forecast_months": 60
    }


# ==============================================================================
# ROUTES - PRÉDICTION
# ==============================================================================
@app.post("/predict", tags=["Prédiction"])
async def predict_upload(
    file: UploadFile = File(..., description="Fichier CSV à prédire"),
    months: int = Query(12, ge=1, le=60, description="Nombre de mois à prédire (1-60)")
):
    """
    **Uploader un fichier CSV et obtenir une prédiction automatique.**
    
    Le fichier doit contenir :
    - Une colonne "date" ou "jour" ou "time" ou "reglement" ou "payment"
    - Une colonne "montant" ou "sum" ou "prix" ou "amount" ou "valeur"
    
    L'API va :
    1. ✓ Détecter automatiquement les colonnes
    2. ✓ Nettoyer et agréger les données en série mensuelle
    3. ✓ Choisir le meilleur modèle (AR, MA, ARMA, ARIMA ou SARIMA)
    4. ✓ Générer les prévisions avec intervalles de confiance
    
    **Paramètres :**
    - `file` : Fichier CSV à analyser
    - `months` : Nombre de mois à prédire (défaut: 12)
    
    **Retour :**
    - `model_info` : Infos sur le modèle choisi
    - `history` : Données historiques
    - `forecast` : Prévisions avec intervalles
    - `explanations` : Logs détaillés de l'analyse
    """
    
    try:
        # Lire le contenu du fichier
        file_content = await file.read()
        
        # Appeler le moteur de prédiction
        result = predict_from_file_content(file_content, months=months)
        
        return result
        
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error_message": str(e),
                "details": "Erreur lors du traitement du fichier"
            }
        )


@app.post("/predict/by-code", tags=["Prédiction"])
async def predict_by_ordinateur(
    code: str = Query(..., description="Code ordinateur/établissement"),
    months: int = Query(12, ge=1, le=60, description="Nombre de mois à prédire"),
    file: UploadFile = File(..., description="Fichier CSV contenant tous les ordinateurs")
):
    """
    **Prédiction pour un ordinateur/établissement spécifique.**
    
    Utile si vous avez un grand fichier groupé et voulez prédire pour
    un établissement particulier identifié par son code.
    
    **Paramètres :**
    - `code` : Code ordinateur/établissement (ex: "146014")
    - `months` : Nombre de mois à prédire
    - `file` : Fichier CSV complet
    
    **Note :** Cette version nécessite qu'il existe une colonne "code_ordinateur"
    dans le fichier d'entrée.
    """
    
    try:
        file_content = await file.read()
        # Pour cette implémentation, on utiliserait un filtre sur le code_ordinateur
        # avant d'appeler predict_from_file_content
        # À développer selon votre logique spécifique
        
        return {
            "status": "error",
            "message": "Cette fonctionnalité est en développement",
            "code": code
        }
        
    except Exception as e:
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
    return JSONResponse(
        status_code=400,
        content={"status": "error", "error_message": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_message": "Erreur interne du serveur",
            "details": str(exc)
        }
    )