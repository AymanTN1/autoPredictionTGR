import io
import pytest
from fastapi.testclient import TestClient
import pandas as pd
import numpy as np

from main import app

client = TestClient(app)


def make_csv_bytes(dates, amounts):
    df = pd.DataFrame({'mois': pd.to_datetime(dates).strftime('%Y-%m-%d'), 'montant': amounts})
    return df.to_csv(index=False, sep=';').encode('utf-8')


def test_predict_by_code_coming_soon(valid_api_key):
    """Test that /predict/by-code returns 404 when code is not found"""
    # Create a CSV without the required code column
    csv_data = b"mois;montant\n2024-01-01;1000\n2024-02-01;2000"
    resp = client.post(
        "/predict/by-code",
        params={"code": "146014"},
        files={"file": ("test.csv", io.BytesIO(csv_data), "text/csv")},
        headers={"X-API-Key": valid_api_key}
    )
    # Should return 400 because file has no code_ordinateur column
    assert resp.status_code == 400
    data = resp.json()
    assert data.get('status') == 'error'


def test_predict_rejects_too_large_file(valid_api_key):
    # >50MB should be rejected by DataCleaner
    big = b"0" * (51 * 1024 * 1024)
    resp = client.post(
        "/predict",
        files={"file": ("big.csv", io.BytesIO(big), "text/csv")},
        headers={"X-API-Key": valid_api_key}
    )
    assert resp.status_code == 400


def test_predict_auto_returns_duration_info_for_sparse(sample_csv_sparse, valid_api_key):
    resp = client.post(
        "/predict/auto",
        files={"file": ("test.csv", io.BytesIO(sample_csv_sparse), "text/csv")},
        headers={"X-API-Key": valid_api_key}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert 'duration_info' in data
    assert data['duration_info']['validated_months'] == 3
    assert 'sparsity' in data['duration_info']['reason'].lower() or 'sparse' in data['duration_info']['reason'].lower()
