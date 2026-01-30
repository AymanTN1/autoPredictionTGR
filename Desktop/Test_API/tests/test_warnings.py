import warnings
from statsmodels.tools.sm_exceptions import ConvergenceWarning
import io
import pytest
from logic import DataCleaner, SmartPredictor


def test_no_convergence_warning_on_predict(sample_csv_dense):
    cleaner = DataCleaner(sample_csv_dense)
    df_clean = cleaner.run()
    predictor = SmartPredictor(df_clean)
    predictor.analyze_and_configure()

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        predictor.get_prediction_data(months=6)
        assert not any(isinstance(item.message, ConvergenceWarning) for item in w)


def test_no_userwarning_on_malformed_dates(sample_csv_malformed):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        try:
            cleaner = DataCleaner(sample_csv_malformed)
            # run may raise ValueError for malformed content, which is acceptable
            cleaner.run()
        except ValueError:
            pass
        # Ensure the specific pandas parse warnings are NOT present
        assert not any('Could not infer format' in str(item.message) or 'Parsing dates in' in str(item.message) for item in w)
