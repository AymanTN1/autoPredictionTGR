import io
import pytest
from fastapi.testclient import TestClient
from main import app, verify_api_key

client = TestClient(app=app)


def test_api_key_case_insensitive_header(sample_csv_dense):
    # header lowercase should still work
    resp = client.post(
        "/predict",
        files={"file": ("test.csv", io.BytesIO(sample_csv_dense), "text/csv")},
        headers={"x-api-key": "TGR-SECRET-KEY-12345"}
    )
    assert resp.status_code == 200


def test_api_key_missing_header_returns_401(sample_csv_dense):
    resp = client.post(
        "/predict",
        files={"file": ("test.csv", io.BytesIO(sample_csv_dense), "text/csv")}
    )
    assert resp.status_code == 401


def test_verify_api_key_direct_call(valid_api_key):
    # calling the dependency function directly should return the key
    result = verify_api_key(x_api_key=valid_api_key)
    assert result == valid_api_key


def test_api_key_invalid_type(sample_csv_dense):
    # send a numeric header (TestClient will stringify it) but ensure it's rejected
    # HTTPX requires header values to be str; stringify numeric input to emulate a bad client
    resp = client.post(
        "/predict",
        files={"file": ("test.csv", io.BytesIO(sample_csv_dense), "text/csv")},
        headers={"X-API-Key": str(12345)}
    )
    assert resp.status_code == 401
