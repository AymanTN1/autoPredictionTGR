"""
models/__init__.py - Modèles SQLModel pour persistance des données
"""

from sqlmodel import SQLModel
from models.database import User, UploadedFile, Prediction, Anomaly

__all__ = [
    "User",
    "UploadedFile",
    "Prediction",
    "Anomaly",
    "SQLModel",
]
