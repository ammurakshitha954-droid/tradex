"""
Unit tests for Deterministic Quantitative Features: Technical, Volatility, Volume, and Risk Metrics.
"""
from datetime import datetime, timedelta, timezone
import pytest
import numpy as np
import pandas as pd
from backend.app.data.providers.mock_provider import MockDataProvider
from backend.app.data.validator import MarketDataValidator
from backend.app.features.technical import TechnicalIndicators
from backend.app.features.volatility import VolatilityIndicators
from backend.app.features.volume import VolumeIndicators
from backend.app.features.risk_metrics import RiskMetricsCalculator


def test_mock_provider_and_validator():
    provider = MockDataProvider(seed=123)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=120)
    df = provider.get_historical_ohlcv("AAPL", start, end)

    is_valid, errors = MarketDataValidator.validate_ohlcv(df)
    assert is_valid, f"Validation failed: {errors}"
    assert len(df) > 30
    assert "close" in df.columns
    assert (df["high"] >= df["low"]).all()


def test_technical_indicators_deterministic():
    provider = MockDataProvider(seed=42)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=250)
    df = provider.get_historical_ohlcv("MSFT", start, end)
    
    features = TechnicalIndicators.compute_all_indicators(df)
    assert "rsi_14" in features.columns
    assert "macd" in features.columns
    assert "ema_200" in features.columns
    assert "trend_score" in features.columns
    
    # RSI bounded between 0 and 100
    valid_rsi = features["rsi_14"].dropna()
    assert (valid_rsi >= 0.0).all() and (valid_rsi <= 100.0).all()

    summary = TechnicalIndicators.get_latest_signal_summary(features)
    assert summary["technical_signal"] in ["BUY", "SELL", "HOLD"]
    assert 0.0 <= summary["signal_conviction"] <= 1.0


def test_volatility_indicators():
    provider = MockDataProvider(seed=99)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=100)
    df = provider.get_historical_ohlcv("NVDA", start, end)
    
    vol_df = VolatilityIndicators.compute_volatility(df)
    assert "hist_vol_20d" in vol_df.columns
    assert "parkinson_vol_20d" in vol_df.columns
    
    vol_summary = VolatilityIndicators.get_latest_volatility_summary(vol_df)
    assert vol_summary["volatility_regime"] in ["LOW", "NORMAL", "ELEVATED", "EXTREME"]
    assert vol_summary["hist_vol_20d_pct"] > 0


def test_volume_indicators():
    provider = MockDataProvider(seed=7)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=80)
    df = provider.get_historical_ohlcv("SPY", start, end)
    
    vol_df = VolumeIndicators.compute_volume_metrics(df)
    assert "rvol_20" in vol_df.columns
    assert "obv" in vol_df.columns
    
    summary = VolumeIndicators.get_latest_volume_summary(vol_df)
    assert summary["obv_trend"] in ["ACCUMULATION", "DISTRIBUTION"]


def test_risk_metrics_calculator():
    np.random.seed(42)
    daily_returns = pd.Series(np.random.normal(0.0008, 0.015, 252))
    bench_returns = pd.Series(np.random.normal(0.0005, 0.012, 252))
    
    metrics = RiskMetricsCalculator.calculate_performance_metrics(daily_returns, bench_returns)
    assert "sharpe_ratio" in metrics
    assert "sortino_ratio" in metrics
    assert "max_drawdown_pct" in metrics
    assert "cvar_95_pct" in metrics
    assert "beta" in metrics
    assert metrics["sample_size_days"] == 252
    assert metrics["max_drawdown_pct"] <= 0.0  # Max drawdown is negative or 0
