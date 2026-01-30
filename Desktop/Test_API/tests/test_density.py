import pandas as pd
import numpy as np
import io
import pytest
from logic import DataCleaner, SmartPredictor


def make_csv_bytes(dates, amounts):
    df = pd.DataFrame({'mois': pd.to_datetime(dates).strftime('%Y-%m-%d'), 'montant': amounts})
    return df.to_csv(index=False, sep=';').encode('utf-8')


def test_smart_duration_dense():
    # 12 months all active -> active_months = 12 -> safe = 4
    # Use month-end dates to avoid accidental trimming of the last month
    dates = pd.date_range('2024-01-31', periods=12, freq='M')
    amounts = np.random.uniform(1000, 50000, len(dates))
    b = make_csv_bytes(dates, amounts)

    cleaner = DataCleaner(b)
    df_clean = cleaner.run()

    predictor = SmartPredictor(df_clean)
    duration = predictor.calculate_and_validate_duration(user_months=None)

    assert duration == 4


def test_smart_duration_sparse():
    # 72 months with 2 active -> safe should be clamped to 3
    dates = pd.date_range('2020-01-29', periods=72, freq='MS')
    amounts = [0.0] * 72
    amounts[0] = 50000.0
    amounts[50] = 75000.0
    b = make_csv_bytes(dates, amounts)

    cleaner = DataCleaner(b)
    df_clean = cleaner.run()

    predictor = SmartPredictor(df_clean)
    duration = predictor.calculate_and_validate_duration(user_months=None)

    assert duration == 3


def test_smart_duration_all_zero():
    # All zeros should still return minimum safe duration (3)
    dates = pd.date_range('2022-01-01', periods=24, freq='MS')
    amounts = [0.0] * 24
    b = make_csv_bytes(dates, amounts)

    cleaner = DataCleaner(b)
    df_clean = cleaner.run()

    predictor = SmartPredictor(df_clean)
    duration = predictor.calculate_and_validate_duration(user_months=None)

    assert duration == 3


def test_smart_duration_many_active_clamped_max():
    # Many active months -> raw safe_duration can exceed 24 but must be clamped to 24
    dates = pd.date_range('2010-01-01', periods=200, freq='MS')
    amounts = np.random.uniform(1000, 100000, len(dates))
    b = make_csv_bytes(dates, amounts)

    cleaner = DataCleaner(b)
    df_clean = cleaner.run()

    predictor = SmartPredictor(df_clean)
    duration = predictor.calculate_and_validate_duration(user_months=None)

    assert duration <= 24 and duration >= 3
