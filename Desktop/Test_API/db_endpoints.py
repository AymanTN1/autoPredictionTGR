"""
db_endpoints.py - Endpoints pour persister les données avec SQLModel

Fournit des endpoints pour :
  1. Créer et gérer les utilisateurs (clés API)
  2. Tracker les fichiers uploadés
  3. Persister les résultats de prédiction
  4. Détecter et sauvegarder les anomalies
  5. Consulter l'historique et générer des stats

INTÉGRATION AVEC MAIN :
  Dans main.py, ajouter au démarrage :
    ```python
    from models.database import db_config
    from db_endpoints import router_db
    
    # Créer les tables
    db_config.create_tables()
    
    # Inclure les routes
    app.include_router(router_db, prefix="/api/db", tags=["Database 🗄️"])
    ```
"""

import json
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlmodel import Session, select
import hashlib
from datetime import datetime

from models.database import (
    db_config,
    get_session,
    User,
    UploadedFile,
    Prediction,
    Anomaly,
)

router_db = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════


def hash_file_content(file_content: bytes) -> str:
    """Calculer le SHA256 d'un contenu de fichier."""
    return hashlib.sha256(file_content).hexdigest()


def get_user_by_api_key(api_key: str, session: Session) -> Optional[User]:
    """Récupérer l'utilisateur correspondant à une clé API."""
    statement = select(User).where(User.api_key == api_key)
    return session.exec(statement).first()


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - UTILISATEURS
# ═══════════════════════════════════════════════════════════════════════════


@router_db.post("/users/register", tags=["Users"])
def register_user(
    organization: str = Query(..., description="Nom de l'organisation"),
    email: Optional[str] = Query(None, description="Email de contact"),
    session: Session = Depends(get_session),
):
    """
    **Créer un nouvel utilisateur et obtenir une clé API.**

    Chaque organisation reçoit une clé API unique pour authentifier ses requêtes.

    **Paramètres :**
    - `organization` : Nom de l'entité (ex: "TGR", "Ministère Finance")
    - `email` : Email de contact (optionnel)

    **Retour :**
    - `user_id` : Identifiant unique
    - `api_key` : Clé API à passer en header `X-API-Key`
    - `created_at` : Timestamp création

    **Exemple :**
    ```bash
    curl -X POST "http://localhost:8000/api/db/users/register?organization=TGR&email=api@tgr.gov.ma"
    ```
    """
    try:
        # Générer une clé API unique
        import secrets

        api_key = f"tgr-{secrets.token_hex(16)}"

        # Créer l'utilisateur
        user = User(
            api_key=api_key,
            organization=organization,
            email=email,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        return {
            "status": "success",
            "user_id": user.user_id,
            "api_key": api_key,
            "organization": organization,
            "email": email,
            "created_at": user.created_at.isoformat(),
            "message": "✅ Utilisateur créé. Gardez cette clé API en sécurité !",
        }

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur création utilisateur : {str(e)}")


@router_db.get("/users/info", tags=["Users"])
def get_user_info(
    api_key: str = Query(..., description="Clé API"),
    session: Session = Depends(get_session),
):
    """
    **Récupérer les informations d'un utilisateur.**

    Args:
        api_key: Clé API

    Returns:
        Information utilisateur + stats d'utilisation
    """
    user = get_user_by_api_key(api_key, session)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # Compter les ressources de cet utilisateur
    files_count = session.exec(select(UploadedFile).where(UploadedFile.user_id == user.user_id)).all()
    predictions_count = session.exec(select(Prediction).where(Prediction.user_id == user.user_id)).all()
    anomalies_count = session.exec(
        select(Anomaly)
        .join(Prediction)
        .where(Prediction.user_id == user.user_id)
    ).all()

    return {
        "user_id": user.user_id,
        "organization": user.organization,
        "email": user.email,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
        "last_used": user.last_used.isoformat() if user.last_used else None,
        "stats": {
            "files_uploaded": len(files_count),
            "predictions_made": len(predictions_count),
            "anomalies_detected": len(anomalies_count),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - FICHIERS UPLOADÉS
# ═══════════════════════════════════════════════════════════════════════════


def save_uploaded_file(
    api_key: str,
    filename: str,
    file_content: bytes,
    row_count: int,
    date_range_start: Optional[str],
    date_range_end: Optional[str],
    session: Session,
) -> int:
    """
    Persister informations d'un fichier uploadé.

    Returns:
        file_id (pour tracking dans Prediction)
    """
    user = get_user_by_api_key(api_key, session)
    if not user:
        raise ValueError("Utilisateur non trouvé")

    file_hash = hash_file_content(file_content)

    uploaded_file = UploadedFile(
        user_id=user.user_id,
        filename=filename,
        file_hash=file_hash,
        row_count=row_count,
        date_range_start=date_range_start,
        date_range_end=date_range_end,
    )
    session.add(uploaded_file)
    session.commit()
    session.refresh(uploaded_file)

    return uploaded_file.file_id


@router_db.get("/files/list", tags=["Files"])
def list_user_files(
    api_key: str = Query(..., description="Clé API"),
    session: Session = Depends(get_session),
):
    """
    **Lister tous les fichiers uploadés par l'utilisateur.**

    Returns:
        Liste des fichiers avec métadonnées
    """
    user = get_user_by_api_key(api_key, session)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    statement = select(UploadedFile).where(UploadedFile.user_id == user.user_id)
    files = session.exec(statement).all()

    return {
        "user_id": user.user_id,
        "total_files": len(files),
        "files": [
            {
                "file_id": f.file_id,
                "filename": f.filename,
                "file_hash": f.file_hash[:12] + "...",  # Tronquer pour lisibilité
                "row_count": f.row_count,
                "date_range": f"from {f.date_range_start} to {f.date_range_end}",
                "uploaded_at": f.uploaded_at.isoformat(),
            }
            for f in files
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - PRÉDICTIONS
# ═══════════════════════════════════════════════════════════════════════════


def save_prediction(
    api_key: str,
    file_id: int,
    model_name: str,
    model_order: str,
    seasonal_order: str,
    forecast_months: int,
    model_aic: float,
    forecast_json: dict,
    anomalies_list: List[dict],
    session: Session,
) -> int:
    """
    Persister une prédiction et ses anomalies associées.

    Returns:
        pred_id
    """
    user = get_user_by_api_key(api_key, session)
    if not user:
        raise ValueError("Utilisateur non trouvé")

    # Créer l'enregistrement de prédiction
    prediction = Prediction(
        user_id=user.user_id,
        file_id=file_id,
        model_name=model_name,
        model_order=model_order,
        seasonal_order=seasonal_order,
        forecast_months=forecast_months,
        model_aic=model_aic,
        forecast_json=json.dumps(forecast_json),  # Stringify le JSON
    )
    session.add(prediction)
    session.commit()
    session.refresh(prediction)

    pred_id = prediction.pred_id

    # Ajouter les anomalies détectées
    for anomaly_data in anomalies_list:
        anomaly = Anomaly(
            pred_id=pred_id,
            anomaly_date=anomaly_data["date"],
            actual_value=anomaly_data["actual_value"],
            predicted_value=anomaly_data["predicted_value"],
            residual=anomaly_data["residual"],
            std_deviations=anomaly_data["std_deviations"],
            severity=anomaly_data["severity"],
            description=anomaly_data["description"],
        )
        session.add(anomaly)

    session.commit()

    return pred_id


@router_db.get("/predictions/list", tags=["Predictions"])
def list_predictions(
    api_key: str = Query(..., description="Clé API"),
    session: Session = Depends(get_session),
):
    """
    **Lister toutes les prédictions effectuées par l'utilisateur.**

    Returns:
        Historique des prédictions
    """
    user = get_user_by_api_key(api_key, session)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    statement = select(Prediction).where(Prediction.user_id == user.user_id)
    predictions = session.exec(statement).all()

    return {
        "user_id": user.user_id,
        "total_predictions": len(predictions),
        "predictions": [
            {
                "pred_id": p.pred_id,
                "model": p.model_name,
                "order": p.model_order,
                "forecast_months": p.forecast_months,
                "aic": p.model_aic,
                "created_at": p.created_at.isoformat(),
            }
            for p in predictions
        ],
    }


@router_db.get("/predictions/{pred_id}", tags=["Predictions"])
def get_prediction_detail(
    pred_id: int,
    api_key: str = Query(..., description="Clé API"),
    session: Session = Depends(get_session),
):
    """
    **Récupérer les détails d'une prédiction spécifique.**

    Returns:
        Prédiction + anomalies associées
    """
    user = get_user_by_api_key(api_key, session)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    statement = select(Prediction).where(
        (Prediction.pred_id == pred_id) & (Prediction.user_id == user.user_id)
    )
    prediction = session.exec(statement).first()

    if not prediction:
        raise HTTPException(status_code=404, detail="Prédiction non trouvée")

    # Récupérer les anomalies
    anomalies = session.exec(
        select(Anomaly).where(Anomaly.pred_id == pred_id)
    ).all()

    return {
        "pred_id": prediction.pred_id,
        "model": prediction.model_name,
        "order": prediction.model_order,
        "seasonal_order": prediction.seasonal_order,
        "forecast_months": prediction.forecast_months,
        "aic": prediction.model_aic,
        "forecast": json.loads(prediction.forecast_json),  # Parse JSON
        "anomalies_count": len(anomalies),
        "anomalies": [
            {
                "date": a.anomaly_date,
                "actual": a.actual_value,
                "predicted": a.predicted_value,
                "residual": a.residual,
                "std_deviations": a.std_deviations,
                "severity": a.severity,
                "description": a.description,
            }
            for a in anomalies
        ],
        "created_at": prediction.created_at.isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - ANOMALIES & STATS
# ═══════════════════════════════════════════════════════════════════════════


@router_db.get("/anomalies/list", tags=["Anomalies"])
def list_anomalies(
    api_key: str = Query(..., description="Clé API"),
    severity: Optional[str] = Query(None, description="Filtrer par sévérité : LOW, MEDIUM, HIGH"),
    session: Session = Depends(get_session),
):
    """
    **Lister toutes les anomalies détectées pour l'utilisateur.**

    Args:
        api_key: Clé API
        severity: Filtrer par sévérité (optionnel)

    Returns:
        Liste des anomalies, optionnellement filtrées
    """
    user = get_user_by_api_key(api_key, session)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    statement = select(Anomaly).join(Prediction).where(Prediction.user_id == user.user_id)

    if severity:
        statement = statement.where(Anomaly.severity == severity)

    anomalies = session.exec(statement).all()

    return {
        "user_id": user.user_id,
        "total_anomalies": len(anomalies),
        "filter": {"severity": severity} if severity else None,
        "anomalies": [
            {
                "anomaly_id": a.anomaly_id,
                "date": a.anomaly_date,
                "actual": a.actual_value,
                "predicted": a.predicted_value,
                "residual": a.residual,
                "std_deviations": a.std_deviations,
                "severity": a.severity,
                "description": a.description,
            }
            for a in anomalies
        ],
    }


@router_db.get("/stats/overview", tags=["Statistics"])
def get_stats_overview(
    api_key: str = Query(..., description="Clé API"),
    session: Session = Depends(get_session),
):
    """
    **Obtenir un aperçu des statistiques d'utilisation.**

    Returns:
        Stats globales pour l'utilisateur
    """
    user = get_user_by_api_key(api_key, session)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # Compter les ressources
    files = session.exec(select(UploadedFile).where(UploadedFile.user_id == user.user_id)).all()
    predictions = session.exec(select(Prediction).where(Prediction.user_id == user.user_id)).all()
    anomalies = session.exec(
        select(Anomaly).join(Prediction).where(Prediction.user_id == user.user_id)
    ).all()

    # Calculer les totaux
    total_rows = sum(f.row_count for f in files)
    high_anomalies = sum(1 for a in anomalies if a.severity == "HIGH")
    medium_anomalies = sum(1 for a in anomalies if a.severity == "MEDIUM")

    # Modèles les plus utilisés
    model_counts = {}
    for p in predictions:
        model_counts[p.model_name] = model_counts.get(p.model_name, 0) + 1

    models_top = sorted(model_counts.items(), key=lambda x: x[1], reverse=True)[:3]

    return {
        "organization": user.organization,
        "period": {
            "created_at": user.created_at.isoformat(),
            "last_used": user.last_used.isoformat() if user.last_used else None,
        },
        "usage": {
            "files_uploaded": len(files),
            "predictions_made": len(predictions),
            "total_rows_processed": total_rows,
            "anomalies_detected": len(anomalies),
        },
        "anomalies_breakdown": {
            "HIGH": high_anomalies,
            "MEDIUM": medium_anomalies,
            "LOW": len(anomalies) - high_anomalies - medium_anomalies,
        },
        "models_used": [{"model": m[0], "uses": m[1]} for m in models_top],
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT - INITIALISATION BASE DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════


@router_db.post("/init", tags=["Admin"])
def init_database():
    """
    **Initialiser la base de données (créer les tables).**

    ⚠️ Admin only - À appeler une fois au démarrage.

    Warning: Cette opération n'écrase rien, elle crée juste les tables
    s'elles n'existent pas.
    """
    try:
        db_config.create_tables()
        return {
            "status": "success",
            "message": "✅ Base de données initialisée",
            "database_url": str(db_config.database_url),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur init BD : {str(e)}")
