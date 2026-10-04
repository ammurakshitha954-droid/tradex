"""
Backtest & Experiment Research API endpoints.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi import APIRouter, Query, Body, HTTPException
from ...data.providers.mock_provider import MockDataProvider
from ...data.providers.yfinance_provider import YFinanceProvider
from ...backtest.engine import BacktestEngine, BacktestConfig, BacktestResult
from ...evaluation.ablation import AblationEngine, ExperimentReport

router = APIRouter(tags=["Research & Backtesting"])
mock_provider = MockDataProvider()
yf_provider = YFinanceProvider(fallback_provider=mock_provider)


@router.post("/backtest")
def run_interactive_backtest(config: BacktestConfig) -> Dict[str, Any]:
    now = datetime.now()
    start = now - timedelta(days=365)
    df = yf_provider.get_historical_ohlcv(config.symbol, start, now)
    if df.empty:
        raise HTTPException(status_code=400, detail=f"No data available for symbol {config.symbol}")

    res = BacktestEngine.run_backtest(df, config)
    return res.model_dump()


@router.get("/experiments/suite")
def get_research_experiment_suite(
    symbol: str = Query(default="SPY"),
    seed: int = Query(default=42)
) -> Dict[str, Any]:
    """Runs 8 Baselines and 8 Ablations (A through H) with standardized reproducible metrics."""
    now = datetime.now()
    start = now - timedelta(days=365)
    df = yf_provider.get_historical_ohlcv(symbol, start, now)
    if df.empty:
        raise HTTPException(status_code=400, detail=f"No data available for {symbol}")

    report = AblationEngine.run_full_experiment_suite(df, symbol=symbol, seed=seed)
    return report.model_dump()
