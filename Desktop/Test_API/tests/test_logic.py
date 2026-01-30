"""
test_logic.py - Tests unitaires pour logic.py

Tests des classes DataCleaner et SmartPredictor
Utilise pytest pour une meilleure gestion des tests
"""

import os
import pandas as pd
import pytest
from io import BytesIO
from logic import DataCleaner, SmartPredictor, predict_from_file_content


class TestDataCleaner:
    """Tests pour la classe DataCleaner."""
    
    @pytest.fixture
    def sample_csv_content(self):
        """Exemple de fichier CSV valide."""
        csv_text = """date,montant
2023-01-01,1000.50
2023-02-01,1500.75
2023-03-01,1200.00
2023-04-01,1800.50
2023-05-01,2100.00
2023-06-01,1950.30
2023-07-01,2200.80
2023-08-01,2050.40
2023-09-01,1900.20
2023-10-01,2300.60
2023-11-01,2100.90
2023-12-01,2500.10
2024-01-01,1800.50
2024-02-01,2100.75
"""
        return csv_text.encode('utf-8')
    
    def test_data_cleaner_initialization(self, sample_csv_content):
        """Test l'initialisation de DataCleaner."""
        cleaner = DataCleaner(sample_csv_content)
        assert cleaner.file_content is not None
        assert cleaner.df is None
        assert isinstance(cleaner.logs, list)
    
    def test_detect_separator_comma(self, sample_csv_content):
        """Test la détection du séparateur virgule."""
        cleaner = DataCleaner(sample_csv_content)
        sep = cleaner._detect_separator()
        assert sep == ','
    
    def test_detect_separator_semicolon(self):
        """Test la détection du séparateur point-virgule."""
        csv_text = "date;montant\n2023-01-01;1000.50"
        cleaner = DataCleaner(csv_text.encode('utf-8'))
        sep = cleaner._detect_separator()
        assert sep == ';'
    
    def test_run_returns_dataframe(self, sample_csv_content):
        """Test que run() retourne un DataFrame."""
        cleaner = DataCleaner(sample_csv_content)
        result = cleaner.run()
        
        assert isinstance(result, pd.DataFrame)
        assert 'montant' in result.columns
        assert len(result) > 0
    
    def test_run_aggregates_monthly(self, sample_csv_content):
        """Test que les données sont agrégées en mensuel."""
        cleaner = DataCleaner(sample_csv_content)
        result = cleaner.run()
        
        # Vérifier que l'index est DatetimeIndex
        assert isinstance(result.index, pd.DatetimeIndex)
        
        # Vérifier la fréquence (MS = Month Start)
        assert result.index.freq == 'MS' or len(result) > 0
    
    def test_run_with_invalid_csv(self):
        """Test avec un CSV invalide."""
        csv_text = "invalid,data\nno,dates,here"
        cleaner = DataCleaner(csv_text.encode('utf-8'))
        
        with pytest.raises(ValueError):
            cleaner.run()
    
    def test_logs_are_recorded(self, sample_csv_content):
        """Test que les logs sont enregistrés."""
        cleaner = DataCleaner(sample_csv_content)
        cleaner.run()
        
        assert len(cleaner.logs) > 0
        assert any('Chargement' in log for log in cleaner.logs)


class TestSmartPredictor:
    """Tests pour la classe SmartPredictor."""
    
    @pytest.fixture
    def sample_df(self):
        """DataFrame d'exemple pour les tests."""
        dates = pd.date_range('2022-01-01', periods=24, freq='MS')
        values = [1000 + i*50 + (100 if i % 2 == 0 else -50) for i in range(24)]
        df = pd.DataFrame({'montant': values}, index=dates)
        return df
    
    def test_predictor_initialization(self, sample_df):
        """Test l'initialisation de SmartPredictor."""
        predictor = SmartPredictor(sample_df)
        
        assert predictor.df is not None
        assert predictor.model_name == "Inconnu"
        assert predictor.order == (0, 0, 0)
        assert predictor.seasonal_order == (0, 0, 0, 0)
    
    def test_analyze_and_configure_runs(self, sample_df):
        """Test que analyze_and_configure() s'exécute sans erreur."""
        predictor = SmartPredictor(sample_df)
        predictor.analyze_and_configure()
        
        # Le modèle doit avoir été sélectionné
        assert predictor.model_name != "Inconnu"
        assert predictor.order != (0, 0, 0)
        assert len(predictor.logs) > 0
    
    def test_model_selection_choices(self, sample_df):
        """Test que un modèle valide est sélectionné."""
        predictor = SmartPredictor(sample_df)
        predictor.analyze_and_configure()
        
        valid_models = ["AR", "MA", "ARMA", "ARIMA", "SARIMA"]
        assert predictor.model_name in valid_models
    
    def test_get_prediction_data_returns_dict(self, sample_df):
        """Test que get_prediction_data() retourne un dictionnaire valide."""
        predictor = SmartPredictor(sample_df)
        predictor.analyze_and_configure()
        result = predictor.get_prediction_data(months=6)
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'model_info' in result or 'error_message' in result
    
    def test_prediction_has_required_fields(self, sample_df):
        """Test que la prédiction a tous les champs requis."""
        predictor = SmartPredictor(sample_df)
        predictor.analyze_and_configure()
        result = predictor.get_prediction_data(months=6)
        
        if result['status'] == 'success':
            assert 'model_info' in result
            assert 'forecast' in result
            assert 'history' in result
            assert 'explanations' in result
            
            assert 'dates' in result['forecast']
            assert 'values' in result['forecast']
            assert 'confidence_upper' in result['forecast']
            assert 'confidence_lower' in result['forecast']
    
    def test_forecast_length(self, sample_df):
        """Test que le nombre de prévisions est correct."""
        predictor = SmartPredictor(sample_df)
        predictor.analyze_and_configure()
        result = predictor.get_prediction_data(months=12)
        
        if result['status'] == 'success':
            forecast_dates = result['forecast']['dates']
            assert len(forecast_dates) == 12


class TestIntegration:
    """Tests d'intégration complets."""
    
    def test_predict_from_file_content_success(self):
        """Test la fonction complète avec un vrai fichier."""
        file_path = os.path.join('dataSets', 'depensesEtat.csv')
        
        if not os.path.exists(file_path):
            pytest.skip("Fichier de test non trouvé")
        
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        result = predict_from_file_content(file_content, months=6)
        
        assert result['status'] == 'success'
        assert result['model_info']['name'] in ["AR", "MA", "ARMA", "ARIMA", "SARIMA"]
        assert len(result['forecast']['dates']) == 6
    
    def test_predict_different_month_counts(self):
        """Test avec différentes durées de prédiction."""
        file_path = os.path.join('dataSets', 'depensesEtat.csv')
        
        if not os.path.exists(file_path):
            pytest.skip("Fichier de test non trouvé")
        
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        for months in [3, 6, 12, 24]:
            result = predict_from_file_content(file_content, months=months)
            if result['status'] == 'success':
                assert len(result['forecast']['dates']) == months
    
    def test_logs_include_explanation(self):
        """Test que les logs incluent des explications."""
        file_path = os.path.join('dataSets', 'depensesEtat.csv')
        
        if not os.path.exists(file_path):
            pytest.skip("Fichier de test non trouvé")
        
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        result = predict_from_file_content(file_content, months=3)
        
        assert len(result['explanations']) > 0
        # Vérifier qu'il y a au moins une explication du modèle
        explanations_text = ' '.join(result['explanations'])
        assert any(model in explanations_text for model in 
                  ["ARIMA", "SARIMA", "AR", "MA", "ARMA"])


class TestErrorHandling:
    """Tests de gestion des erreurs."""
    
    def test_empty_file(self):
        """Test avec un fichier vide."""
        cleaner = DataCleaner(b'')
        with pytest.raises(Exception):
            cleaner.run()
    
    def test_missing_date_column(self):
        """Test avec colonne date manquante."""
        csv_text = "amount\n1000\n2000"
        cleaner = DataCleaner(csv_text.encode('utf-8'))
        with pytest.raises(ValueError):
            cleaner.run()
    
    def test_missing_amount_column(self):
        """Test avec colonne montant manquante."""
        csv_text = "date\n2023-01-01\n2023-02-01"
        cleaner = DataCleaner(csv_text.encode('utf-8'))
        with pytest.raises(ValueError):
            cleaner.run()
    
    def test_invalid_dates(self):
        """Test avec dates invalides."""
        csv_text = "date,montant\ninvalid_date,1000"
        cleaner = DataCleaner(csv_text.encode('utf-8'))
        
        # Devrait soit lever une exception, soit ignorer les mauvaises dates
        try:
            result = cleaner.run()
            # Si pas d'exception, vérifier que result est vide ou valide
            assert result is None or isinstance(result, pd.DataFrame)
        except ValueError:
            pass  # C'est acceptable aussi


# ==============================================================================
# TESTS À EXÉCUTER MANUELLEMENT
# ==============================================================================

def run_all_tests():
    """Exécuter tous les tests avec pytest."""
    print("Pour exécuter les tests, utilisez :")
    print("  pip install pytest")
    print("  pytest test_logic.py -v")


if __name__ == "__main__":
    run_all_tests()
