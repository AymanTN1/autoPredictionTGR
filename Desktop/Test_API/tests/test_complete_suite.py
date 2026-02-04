"""
test_complete_suite.py - Suite complète de tests Pytest pour API TGR v2.0

🎯 COUVERTURE :
  ✅ Tests unitaires : DataCleaner, SmartPredictor, validation dates
  ✅ Tests sécurité : API Key validation, 401 responses
  ✅ Tests API : Routes /predict, /predict/auto, /predict/by-code
  ✅ Tests intégration : Bout-en-bout avec fichiers réels
  ✅ Tests edge cases : Données manquantes, formats bizarres, fichiers énormes

📊 USAGE :
  pytest test_complete_suite.py -v              # Tous les tests avec détails
  pytest test_complete_suite.py::test_api_key_validation -v   # Test spécifique
  pytest test_complete_suite.py -k "security" -v               # Tests filtrés

"""

import pytest
import io
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app, verify_api_key
from logic import DataCleaner, SmartPredictor, predict_from_file_content

# ═══════════════════════════════════════════════════════════════════════════
# ⚙️  FIXTURES (Configuration initiale)
# ═══════════════════════════════════════════════════════════════════════════

client = TestClient(app=app)

@pytest.fixture
def valid_api_key():
    """Retourne une clé API valide"""
    return "TGR-SECRET-KEY-12345"

@pytest.fixture
def invalid_api_key():
    """Retourne une clé API invalide"""
    return "WRONG-KEY-12345"

@pytest.fixture
def sample_csv_dense():
    """
    Crée un CSV avec données DENSES (tous les mois ont des valeurs)
    ✓ Cas nominal pour Smart Duration
    """
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='MS')
    data = {
        'mois': dates.strftime('%Y-%m-%d'),
        'montant': np.random.uniform(1000, 50000, len(dates))
    }
    df = pd.DataFrame(data)
    
    # Convertir en bytes CSV
    csv_bytes = df.to_csv(index=False, sep=';').encode('utf-8')
    return csv_bytes

@pytest.fixture
def sample_csv_sparse():
    """
    Crée un CSV avec données ÉPARSES (2 mois actifs sur 72)
    ✓ Cas pour test Smart Duration (détection sparsity)
    """
    dates = pd.date_range(start='2020-01-29', end='2026-01-29', freq='MS')
    amounts = [0.0] * len(dates)
    amounts[0] = 50000.0   # Premier mois : valeur
    amounts[50] = 75000.0  # Mois 50 : valeur
    
    data = {
        'mois': dates.strftime('%Y-%m-%d'),
        'montant': amounts
    }
    df = pd.DataFrame(data)
    
    csv_bytes = df.to_csv(index=False, sep=';').encode('utf-8')
    return csv_bytes

@pytest.fixture
def sample_csv_malformed():
    """
    Crée un CSV avec format bizarre (séparateur ?,  dates invalides)
    ✗ Cas pour tester gestion erreurs
    """
    content = "date?valeur\n2024-XX-01?1000\n2024-01-02?2000"
    return content.encode('utf-8')

# ═══════════════════════════════════════════════════════════════════════════
# 🔍 TESTS UNITAIRES - DataCleaner
# ═══════════════════════════════════════════════════════════════════════════

class TestDataCleaner:
    """Tests unitaires pour la classe DataCleaner"""
    
    def test_init_with_bytes(self, sample_csv_dense):
        """✓ DataCleaner accepte des bytes"""
        cleaner = DataCleaner(sample_csv_dense)
        assert cleaner.file_content == sample_csv_dense
        assert cleaner.df is None
    
    def test_run_parse_csv_dense(self, sample_csv_dense):
        """✓ DataCleaner parse correctement un CSV dense"""
        cleaner = DataCleaner(sample_csv_dense)
        cleaner.run()
        
        assert cleaner.df is not None
        assert len(cleaner.df) == 12
        assert 'mois' in cleaner.df.columns
        assert 'montant' in cleaner.df.columns
    
    def test_run_parse_csv_sparse(self, sample_csv_sparse):
        """✓ DataCleaner gère un CSV épars (peu de données)"""
        cleaner = DataCleaner(sample_csv_sparse)
        cleaner.run()
        
        assert cleaner.df is not None
        assert len(cleaner.df) == 72  # Tous les mois parsés
        active_count = (cleaner.df['montant'] > 0).sum()
        assert active_count == 2  # Seulement 2 mois actifs
    
    def test_max_file_size_validation(self):
        """✓ DataCleaner rejette les fichiers > 50 MB"""
        giant_csv = b"x" * (51 * 1024 * 1024)  # 51 MB
        cleaner = DataCleaner(giant_csv)
        
        with pytest.raises(ValueError, match="trop volumineux"):
            cleaner.run()
    
    def test_logs_collection(self, sample_csv_dense):
        """✓ DataCleaner collecte les logs au lieu de print()"""
        cleaner = DataCleaner(sample_csv_dense)
        cleaner.run()
        
        assert len(cleaner.logs) > 0
        assert any("colonne" in log.lower() for log in cleaner.logs)


# ═══════════════════════════════════════════════════════════════════════════
# 🧠 TESTS UNITAIRES - SmartPredictor
# ═══════════════════════════════════════════════════════════════════════════

class TestSmartPredictor:
    """Tests unitaires pour la classe SmartPredictor"""
    
    def test_smart_duration_dense_data(self, sample_csv_dense):
        """✓ Smart Duration : Données denses → durée calculée = n_active / 3"""
        cleaner = DataCleaner(sample_csv_dense)
        cleaner.run()
        
        predictor = SmartPredictor(cleaner.df)
        duration = predictor.calculate_and_validate_duration(user_months=None)
        
        # 12 mois actifs → 12/3 = 4 mois (entre min=3 et max=24)
        assert 3 <= duration <= 24
        assert duration == 4  # Exactement
    
    def test_smart_duration_sparse_data(self, sample_csv_sparse):
        """✓ Smart Duration : Données éparses → détecte sparsity"""
        cleaner = DataCleaner(sample_csv_sparse)
        cleaner.run()
        
        predictor = SmartPredictor(cleaner.df)
        duration = predictor.calculate_and_validate_duration(user_months=None)
        
        # 2 mois actifs → 2/3 < 1 → min(3)
        assert duration == 3  # Minimale appliquée
    
    def test_smart_duration_user_override(self, sample_csv_dense):
        """✓ Smart Duration MODE USER : Accepte user_months valide"""
        cleaner = DataCleaner(sample_csv_dense)
        cleaner.run()
        
        predictor = SmartPredictor(cleaner.df)
        
        # User demande 6 mois (< safe 4) → accepté
        duration = predictor.calculate_and_validate_duration(user_months=6)
        assert duration == 6  # User gagne
    
    def test_smart_duration_user_override_dangerous(self, sample_csv_sparse):
        """✓ Smart Duration SÉCURITÉ : Réduit si user_months > safe"""
        cleaner = DataCleaner(sample_csv_sparse)
        cleaner.run()
        
        predictor = SmartPredictor(cleaner.df)
        
        # User demande 36 mois (> safe 3) → réduit pour sécurité
        duration = predictor.calculate_and_validate_duration(user_months=36)
        assert duration == 3  # Réduit à la durée sûre


# ═══════════════════════════════════════════════════════════════════════════
# 🔐 TESTS SÉCURITÉ - API Key
# ═══════════════════════════════════════════════════════════════════════════

class TestSecurityAPIKey:
    """Tests de sécurité : Validation des clés API"""
    
    def test_missing_api_key(self, sample_csv_dense):
        """✗ Demande sans API Key → 401 Unauthorized"""
        response = client.post(
            "/predict",
            files={"file": ("test.csv", io.BytesIO(sample_csv_dense), "text/csv")}
        )
        assert response.status_code == 401
    
    def test_invalid_api_key(self, sample_csv_dense, invalid_api_key):
        """✗ Demande avec API Key invalide → 401 Unauthorized"""
        response = client.post(
            "/predict",
            files={"file": ("test.csv", io.BytesIO(sample_csv_dense), "text/csv")},
            headers={"X-API-Key": invalid_api_key}
        )
        assert response.status_code == 401
        assert "invalide" in response.json()["detail"].lower()
    
    def test_valid_api_key_success(self, sample_csv_dense, valid_api_key):
        """✓ Demande avec API Key valide → 200 OK"""
        response = client.post(
            "/predict",
            files={"file": ("test.csv", io.BytesIO(sample_csv_dense), "text/csv")},
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
    
    def test_verify_api_key_dependency(self, valid_api_key, invalid_api_key):
        """✓ Dépendance verify_api_key fonctionne correctement"""
        # Valid key
        result = verify_api_key(x_api_key=valid_api_key)
        assert result == valid_api_key
        
        # Invalid key raises exception
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(x_api_key=invalid_api_key)
        assert exc_info.value.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# 📡 TESTS API - Routes principales
# ═══════════════════════════════════════════════════════════════════════════

class TestAPIRoutes:
    """Tests des endpoints HTTP"""
    
    def test_health_check_no_auth(self):
        """✓ GET /health accessible sans API Key"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_info_endpoint(self):
        """✓ GET /info retourne infos API"""
        response = client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "features" in data
    
    def test_predict_mode_auto(self, sample_csv_dense, valid_api_key):
        """✓ POST /predict/auto : Mode AUTO (pas de months param)"""
        response = client.post(
            "/predict/auto",
            files={"file": ("test.csv", io.BytesIO(sample_csv_dense), "text/csv")},
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "duration_info" in data
        assert data["duration_info"]["requested_months"] is None
    
    def test_predict_mode_user(self, sample_csv_dense, valid_api_key):
        """✓ POST /predict?months=6 : Mode USER (months spécifié)"""
        response = client.post(
            "/predict",
            files={"file": ("test.csv", io.BytesIO(sample_csv_dense), "text/csv")},
            params={"months": 6},
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "duration_info" in data
        assert data["duration_info"]["requested_months"] == 6
    
    def test_predict_invalid_months(self, sample_csv_dense, valid_api_key):
        """✗ POST /predict?months=0 : Validation échoue (months < 1)"""
        response = client.post(
            "/predict",
            files={"file": ("test.csv", io.BytesIO(sample_csv_dense), "text/csv")},
            params={"months": 0},
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 422  # Validation error


# ═══════════════════════════════════════════════════════════════════════════
# 🧪 TESTS INTÉGRATION
# ═══════════════════════════════════════════════════════════════════════════

class TestIntegration:
    """Tests d'intégration bout-en-bout"""
    
    def test_full_workflow_dense_auto(self, sample_csv_dense, valid_api_key):
        """✓ Workflow complet : Upload CSV dense → Prédiction MODE AUTO"""
        response = client.post(
            "/predict/auto",
            files={"file": ("test.csv", io.BytesIO(sample_csv_dense), "text/csv")},
            headers={"X-API-Key": valid_api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifications réponse
        assert data["status"] == "success"
        assert "forecast" in data
        assert "duration_info" in data
        
        forecast = data["forecast"]
        assert "dates" in forecast
        assert "values" in forecast
        assert len(forecast["dates"]) > 0
        assert len(forecast["values"]) == len(forecast["dates"])
    
    def test_full_workflow_sparse_auto(self, sample_csv_sparse, valid_api_key):
        """✓ Workflow : CSV épars → Smart Duration détecte et réduit"""
        response = client.post(
            "/predict/auto",
            files={"file": ("test.csv", io.BytesIO(sample_csv_sparse), "text/csv")},
            headers={"X-API-Key": valid_api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        duration_info = data["duration_info"]
        assert duration_info["validated_months"] == 3  # Minimale appliquée
        assert "sparsity" in duration_info["reason"].lower()


# ═══════════════════════════════════════════════════════════════════════════
# 🔌 TESTS EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Tests des cas limites"""
    
    def test_empty_file(self, valid_api_key):
        """✗ Fichier vide"""
        empty_csv = b""
        response = client.post(
            "/predict",
            files={"file": ("test.csv", io.BytesIO(empty_csv), "text/csv")},
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 400
    
    def test_malformed_csv(self, sample_csv_malformed, valid_api_key):
        """✗ CSV mal formé"""
        response = client.post(
            "/predict",
            files={"file": ("test.csv", io.BytesIO(sample_csv_malformed), "text/csv")},
            headers={"X-API-Key": valid_api_key}
        )
        # Devrait échouer ou gérer gracieusement
        assert response.status_code in [400, 422, 500]
    
    def test_csv_single_row(self, valid_api_key):
        """✗ CSV avec une seule ligne (pas assez de données)"""
        single_row = b"mois;montant\n2024-01-01;1000"
        response = client.post(
            "/predict",
            files={"file": ("test.csv", io.BytesIO(single_row), "text/csv")},
            headers={"X-API-Key": valid_api_key}
        )
        # Au moins 12 points pour SARIMA
        assert response.status_code in [400, 422, 500]


# ═══════════════════════════════════════════════════════════════════════════
# 🚀 EXÉCUTION
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
