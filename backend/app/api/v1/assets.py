"""
Asset Analysis API routes: OHLCV candlestick data, technical indicators, and fundamentals.
"""
from typing import Optional
from datetime import datetime, timedelta
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from ...data.providers.mock_provider import MockDataProvider
from ...data.providers.yfinance_provider import YFinanceProvider
from ...features.technical import TechnicalIndicators
from ...features.volatility import VolatilityIndicators
from ...features.volume import VolumeIndicators
from ...features.risk_metrics import RiskMetricsCalculator

router = APIRouter(prefix="/assets", tags=["Asset Analysis"])
mock_provider = MockDataProvider()
yf_provider = YFinanceProvider(fallback_provider=mock_provider)


@router.get("/{symbol}")
def get_asset_overview(symbol: str):
    clean_sym = symbol.upper()
    meta = yf_provider.get_asset_metadata(clean_sym)
    quote = yf_provider.get_latest_price(clean_sym)
    fundamentals = yf_provider.get_fundamentals(clean_sym)
    return {
        "metadata": meta.model_dump(),
        "quote": quote,
        "fundamentals": fundamentals,
    }


@router.get("/{symbol}/chart")
def get_asset_chart_data(
    symbol: str,
    days: int = Query(default=180, ge=30, le=1000),
    timeframe: str = Query(default="1d")
):
    """
    Returns time-series OHLCV formatted for TradingView Lightweight Charts,
    along with calculated technical overlays (EMA 21, 50, 200, Bollinger Bands, Volume).
    """
    clean_sym = symbol.upper()
    now = datetime.now()
    start = now - timedelta(days=days)
    
    df = yf_provider.get_historical_ohlcv(clean_sym, start, now, timeframe)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No market data found for {clean_sym}")

    tech_df = TechnicalIndicators.compute_all_indicators(df)
    vol_df = VolatilityIndicators.compute_volatility(tech_df)
    full_df = VolumeIndicators.compute_volume_metrics(vol_df).bfill().ffill()

    candles = []
    ema_21_line = []
    ema_50_line = []
    ema_200_line = []
    bb_upper_line = []
    bb_lower_line = []
    volume_bars = []

    for idx, row in full_df.iterrows():
        t_str = idx.strftime("%Y-%m-%d")
        o, h, l, c = float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])
        v = int(row["volume"])

        candles.append({
            "time": t_str,
            "open": round(o, 2),
            "high": round(h, 2),
            "low": round(l, 2),
            "close": round(c, 2),
        })

        color = "#10b981" if c >= o else "#ef4444"
        volume_bars.append({
            "time": t_str,
            "value": v,
            "color": color,
        })

        if "ema_21" in row and not pd.isna(row["ema_21"]):
            ema_21_line.append({"time": t_str, "value": round(float(row["ema_21"]), 2)})
        if "ema_50" in row and not pd.isna(row["ema_50"]):
            ema_50_line.append({"time": t_str, "value": round(float(row["ema_50"]), 2)})
        if "ema_200" in row and not pd.isna(row["ema_200"]):
            ema_200_line.append({"time": t_str, "value": round(float(row["ema_200"]), 2)})
        if "bb_upper" in row and not pd.isna(row["bb_upper"]):
            bb_upper_line.append({"time": t_str, "value": round(float(row["bb_upper"]), 2)})
            bb_lower_line.append({"time": t_str, "value": round(float(row["bb_lower"]), 2)})

    # Calculate performance metrics over this window
    returns = full_df["close"].pct_change()
    metrics = RiskMetricsCalculator.calculate_performance_metrics(returns)

    return {
        "symbol": clean_sym,
        "candles": candles,
        "volume": volume_bars,
        "overlays": {
            "ema_21": ema_21_line,
            "ema_50": ema_50_line,
            "ema_200": ema_200_line,
            "bb_upper": bb_upper_line,
            "bb_lower": bb_lower_line,
        },
        "performance_metrics": metrics,
    }
