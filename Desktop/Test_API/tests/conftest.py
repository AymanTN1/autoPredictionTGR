import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def valid_api_key():
    return "TGR-SECRET-KEY-12345"

@pytest.fixture
def invalid_api_key():
    return "WRONG-KEY-12345"

@pytest.fixture
def sample_csv_dense():
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='MS')
    data = {
        'mois': dates.strftime('%Y-%m-%d'),
        'montant': np.random.uniform(1000, 50000, len(dates))
    }
    df = pd.DataFrame(data)
    return df.to_csv(index=False, sep=';').encode('utf-8')

@pytest.fixture
def sample_csv_sparse():
    dates = pd.date_range(start='2020-01-29', end='2026-01-29', freq='MS')
    amounts = [0.0] * len(dates)
    amounts[0] = 50000.0
    amounts[50] = 75000.0
    df = pd.DataFrame({'mois': dates.strftime('%Y-%m-%d'), 'montant': amounts})
    return df.to_csv(index=False, sep=';').encode('utf-8')

@pytest.fixture
def sample_csv_malformed():
    content = "date?valeur\n2024-XX-01?1000\n2024-01-02?2000"
    return content.encode('utf-8')
