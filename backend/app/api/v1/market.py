"""
Market Intelligence API routes: Market pulse, broad indices, market-wide uncertainty and regime.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Query
from ...data.providers.mock_provider import MockDataProvider
from ...data.providers.yfinance_provider import YFinanceProvider
from ...regime.detector import MarketRegimeDetector
from ...core.config import settings

router = APIRouter(prefix="/market", tags=["Market Intelligence"])
mock_provider = MockDataProvider()
yf_provider = YFinanceProvider(fallback_provider=mock_provider)


@router.get("/pulse")
def get_market_pulse():
    """
    Returns high-level AI market pulse: benchmark regime, broad index metrics,
    market-wide uncertainty, and watchlist summary.
    """
    # 1. Benchmark (SPY) analysis for overall regime
    now = datetime.now()
    start = now - timedelta(days=200)
    bench_df = yf_provider.get_historical_ohlcv(settings.PRIMARY_BENCHMARK, start, now)
    regime_res = MarketRegimeDetector.detect_regime_from_series(bench_df, settings.PRIMARY_BENCHMARK)

    # 2. Watchlist quotes
    watchlist = []
    for sym in settings.DEFAULT_SYMBOLS:
        quote = yf_provider.get_latest_price(sym)
        meta = yf_provider.get_asset_metadata(sym)
        watchlist.append({
            **quote,
            "name": meta.name,
            "sector": meta.sector,
            "exchange": meta.exchange,
        })

    # 3. Market-wide conviction index
    advancing = sum(1 for w in watchlist if w.get("change", 0) > 0)
    market_breadth_pct = round((advancing / len(watchlist)) * 100.0, 1)

    return {
        "benchmark": settings.PRIMARY_BENCHMARK,
        "market_regime": regime_res.current_regime.value,
        "regime_confidence": regime_res.regime_confidence,
        "stability_score": regime_res.stability_score,
        "key_macro_drivers": regime_res.key_drivers,
        "market_breadth_advance_pct": market_breadth_pct,
        "watchlist": watchlist,
        "timestamp": now.isoformat(),
    }


@router.get("/symbols")
def get_supported_symbols():
    """Returns list of supported assets and metadata."""
    symbols_data = []
    for sym in settings.DEFAULT_SYMBOLS:
        meta = yf_provider.get_asset_metadata(sym)
        symbols_data.append(meta.model_dump())
    return {"symbols": symbols_data}
