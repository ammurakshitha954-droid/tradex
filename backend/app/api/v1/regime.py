"""
Market Regime API routes: Regime detection and interactive historical timeline.
"""
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Query
from ...data.providers.mock_provider import MockDataProvider
from ...data.providers.yfinance_provider import YFinanceProvider
from ...regime.detector import MarketRegimeDetector

router = APIRouter(prefix="/regime", tags=["Market Regime Engine"])
mock_provider = MockDataProvider()
yf_provider = YFinanceProvider(fallback_provider=mock_provider)


@router.get("/current")
def get_current_regime(
    symbol: str = Query(default="SPY"),
    lookback_days: int = Query(default=250, ge=30, le=1000)
):
    clean_sym = symbol.upper()
    now = datetime.now()
    start = now - timedelta(days=lookback_days)
    df = yf_provider.get_historical_ohlcv(clean_sym, start, now)
    
    result = MarketRegimeDetector.detect_regime_from_series(df, clean_sym)
    return result.model_dump()


@router.get("/timeline")
def get_regime_timeline(
    symbol: str = Query(default="SPY"),
    lookback_days: int = Query(default=365, ge=60, le=1200)
):
    clean_sym = symbol.upper()
    now = datetime.now()
    start = now - timedelta(days=lookback_days)
    df = yf_provider.get_historical_ohlcv(clean_sym, start, now)
    
    result = MarketRegimeDetector.detect_regime_from_series(df, clean_sym)
    return {
        "symbol": clean_sym,
        "current_regime": result.current_regime.value,
        "timeline": [p.model_dump() for p in result.timeline],
    }
