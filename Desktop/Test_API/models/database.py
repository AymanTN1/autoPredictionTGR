"""
models/database.py - Schémas SQLModel et configuration de la base de données

Structure de persistance pour l'API Prédiction des Dépenses :

┌─────────────────┐
│     User        │ (Utilisateurs / Clés API)
├─────────────────┤
│ user_id (PK)    │
│ api_key         │ → Unique, pour authentification
│ organization    │ → Nom de l'organisation (ex: "TGR")
│ created_at      │
│ last_used       │
└─────────────────┘
        │
        ├─→ ┌──────────────────┐
        │   │ UploadedFile     │ (Fichiers uploadés)
        │   ├──────────────────┤
        │   │ file_id (PK)     │
        │   │ user_id (FK)     │ → Qui a uploadé?
        │   │ filename         │
        │   │ file_hash        │ → SHA256 (détection doublons)
        │   │ row_count        │ → Nombre de lignes
        │   │ date_range       │ → "2020-01 à 2024-12"
        │   │ uploaded_at      │
        │   └──────────────────┘
        │
        ├─→ ┌──────────────────┐
        │   │ Prediction       │ (Résultats de prédiction)
        │   ├──────────────────┤
        │   │ pred_id (PK)     │
        │   │ user_id (FK)     │ → Qui a demandé?
        │   │ file_id (FK)     │ → Sur quel fichier?
        │   │ model_name       │ → "SARIMA", "ARIMA", etc.
        │   │ forecast_months  │ → Nombre de mois prédits
        │   │ model_aic        │ → Critère AIC
        │   │ forecast_json    │ → Prévisions (JSON)
        │   │ created_at       │
        │   └──────────────────┘
        │           │
        │           └─→ ┌──────────────────┐
        │               │ Anomaly          │ (Anomalies détectées)
        │               ├──────────────────┤
        │               │ anomaly_id (PK)  │
        │               │ pred_id (FK)     │ → Via quelle prédiction?
        │               │ date             │ → Date de l'anomalie
        │               │ actual_value     │ → Valeur réelle
        │               │ predicted_value  │ → Valeur prédite
        │               │ residual         │ → Écart (actual - predicted)
        │               │ std_deviations   │ → Combien de σ?
        │               │ severity         │ → "LOW", "MEDIUM", "HIGH"
        │               │ description      │ → "Mars 2023 dépense anormale"
        │               └──────────────────┘

"""

from datetime import datetime
from typing import Optional, List
from sqlmodel import (
    SQLModel,
    Field,
    select,
    Session as SQLModelSession,
)
from sqlalchemy.orm import relationship
import os
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION BASE DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════

# URL de connexion (SQLite local par défaut, PostgreSQL en production)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./tgr_api.db"  # ← Local development
)

# Variables d'environnement pour PostgreSQL production :
# DATABASE_URL=postgresql://user:password@localhost:5432/tgr_api


# ═══════════════════════════════════════════════════════════════════════════
# MODÈLES SQLModel - SCHÉMAS DE LA BD
# ═══════════════════════════════════════════════════════════════════════════


class User(SQLModel, table=True):
    """
    Modèle pour les utilisateurs de l'API.

    Chaque utilisateur/organisation reçoit une clé API unique.
    Utilisée pour l'authentification et le tracking des requêtes.

    Exemple :
        Organisation : TGR
        API Key : "tgr-secret-key-12345"
        → Peut uploader des fichiers, faire des prédictions
        → Toutes les requêtes sont trackées sous ce user_id
    """

    __tablename__ = "users"

    user_id: Optional[int] = Field(default=None, primary_key=True)
    api_key: str = Field(
        index=True,
        unique=True,
        description="Clé API unique pour authentification"
    )
    organization: str = Field(
        description="Nom de l'organisation (ex: TGR, Ministère Finance)"
    )
    email: Optional[str] = Field(default=None, description="Email de contact")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Date création du compte"
    )
    last_used: Optional[datetime] = Field(
        default=None,
        description="Dernière utilisation de l'API"
    )
    is_active: bool = Field(
        default=True,
        description="Compte actif? (pour désactiver une clé sans la supprimer)"
    )

    # Relations handled via SQLAlchemy relationships in runtime (omitted from
    # SQLModel field definitions to avoid SQL type mapping issues in tests)


class UploadedFile(SQLModel, table=True):
    """
    Modèle pour tracking des fichiers uploadés.

    Permet de savoir :
    - Quel fichier a été uploadé?
    - Par qui?
    - Quand?
    - Combien de lignes?
    - Couverture temporelle?

    Utile pour :
    - Générer des stats : "L'API a traité 500M de dirhams ce mois"
    - Détecter les doublons (file_hash)
    - Auditer les accès (compliance TGR)
    """

    __tablename__ = "uploaded_files"

    file_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id")
    filename: str = Field(description="Nom du fichier uploadé")
    file_hash: str = Field(
        index=True,
        description="SHA256 du contenu (détection doublons)"
    )
    row_count: int = Field(description="Nombre de lignes dans le CSV")
    date_range_start: Optional[str] = Field(
        default=None,
        description="Première date du fichier (YYYY-MM-DD)"
    )
    date_range_end: Optional[str] = Field(
        default=None,
        description="Dernière date du fichier (YYYY-MM-DD)"
    )
    uploaded_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp upload"
    )

    # Relations omitted from SQLModel fields for test compatibility


class Prediction(SQLModel, table=True):
    """
    Modèle pour persister les résultats de prédiction.

    Chaque appel à /predict génère un enregistrement :
    - Quel modèle a été choisi?
    - Quel AIC?
    - Quelles prévisions?
    - Quelles anomalies détectées?

    Utile pour :
    - Audit et compliance
    - Statistiques d'utilisation
    - Rejouer une prédiction (reproducibilité)
    """

    __tablename__ = "predictions"

    pred_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id")
    file_id: int = Field(foreign_key="uploaded_files.file_id")
    model_name: str = Field(
        description="Modèle choisi (SARIMA, ARIMA, AR, MA, ARMA)"
    )
    model_order: str = Field(
        description="Paramètres du modèle, ex: (1, 1, 1)"
    )
    seasonal_order: str = Field(
        default="(0, 0, 0, 0)",
        description="Paramètres saisonniers, ex: (1, 1, 1, 12)"
    )
    forecast_months: int = Field(description="Nombre de mois prédits")
    model_aic: float = Field(description="Critère AIC du modèle")
    forecast_json: str = Field(
        description="Données brutes de prévisions (JSON stringifié)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp de la prédiction"
    )

    # Relations omitted from SQLModel fields for test compatibility


class Anomaly(SQLModel, table=True):
    """
    Modèle pour persister les anomalies détectées.

    Chaque anomalie détectée via la "Killer Feature" est enregistrée :
    - Date de l'anomalie
    - Valeur réelle vs prédite
    - Écart (résidu)
    - Sévérité (LOW, MEDIUM, HIGH)

    Exemple :
        Date: 2023-03-01
        Valeur réelle: 5000000 DH
        Valeur prédite: 3000000 DH
        Écart: 2000000 DH
        Écart-types: 2.5σ (anormal)
        Sévérité: HIGH
        Description: "Mars 2023 : Dépense 67% supérieure à la normale"

    Utile pour :
    - Audit des fraudes potentielles
    - Alertes automatiques
    - Rapports à la TGR
    """

    __tablename__ = "anomalies"

    anomaly_id: Optional[int] = Field(default=None, primary_key=True)
    pred_id: int = Field(foreign_key="predictions.pred_id")
    anomaly_date: str = Field(
        index=True,
        description="Date de l'anomalie (YYYY-MM-DD)"
    )
    actual_value: float = Field(
        description="Valeur réelle observée"
    )
    predicted_value: float = Field(
        description="Valeur prédite par le modèle"
    )
    residual: float = Field(
        description="Écart = actual - predicted"
    )
    std_deviations: float = Field(
        description="Nombre d'écarts-types (σ) : |residual| / std(residuals)"
    )
    severity: str = Field(
        default="MEDIUM",
        description="Sévérité : LOW (1σ), MEDIUM (2σ), HIGH (3σ+)"
    )
    description: str = Field(
        description="Explication lisible (ex: 'Dépense 50% supérieure à la normale')"
    )
    detected_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp de la détection"
    )

    # Relations omitted from SQLModel fields for test compatibility


# ═══════════════════════════════════════════════════════════════════════════
# GESTION DE LA BASE DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════


class DatabaseConfig:
    """Classe pour gérer la configuration et les opérations BD."""

    def __init__(self, database_url: str = DATABASE_URL):
        self.database_url = database_url
        self.engine = None

    def get_engine(self):
        """Créer ou retourner l'engine SQLAlchemy."""
        if self.engine is None:
            from sqlalchemy import create_engine

            # Pour SQLite, créer le fichier s'il n'existe pas
            if self.database_url.startswith("sqlite"):
                self.engine = create_engine(
                    self.database_url,
                    connect_args={"check_same_thread": False},
                    echo=False  # Mettre à True pour déboguer les queries
                )
            else:
                # PostgreSQL ou autre
                self.engine = create_engine(
                    self.database_url,
                    pool_pre_ping=True,
                    echo=False
                )
        return self.engine

    def create_tables(self):
        """Créer toutes les tables de la BD."""
        engine = self.get_engine()
        SQLModel.metadata.create_all(engine)

    def get_session(self):
        """Créer une nouvelle session BD avec support SQLModel (.exec())."""
        engine = self.get_engine()
        return SQLModelSession(engine)

    def drop_all_tables(self):
        """⚠️ DANGER : Supprimer toutes les tables (pour tests uniquement)."""
        engine = self.get_engine()
        SQLModel.metadata.drop_all(engine)


# Singleton global
db_config = DatabaseConfig(DATABASE_URL)

# FastAPI Dependency
def get_session():
    """Dépendance FastAPI pour obtenir une session BD."""
    with db_config.get_session() as session:
        yield session
