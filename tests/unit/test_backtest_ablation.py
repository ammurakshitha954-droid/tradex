"""
Unit tests for Backtesting and Ablation Studies.
"""
from datetime import datetime, timedelta
import pytest
from backend.app.data.providers.mock_provider import MockDataProvider
from backend.app.backtest.engine import BacktestEngine, BacktestConfig
from backend.app.evaluation.ablation import AblationEngine


def test_backtest_engine_execution():
    provider = MockDataProvider(seed=101)
    end = datetime.now()
    start = end - timedelta(days=365)
    df = provider.get_historical_ohlcv("SPY", start, end)

    config = BacktestConfig(
        symbol="SPY",
        initial_capital=50_000.0,
        strategy="full_adaptive",
        transaction_cost_bps=10.0,
        slippage_bps=5.0,
        use_abstention=True,
    )

    res = BacktestEngine.run_backtest(df, config)
    assert res.final_equity > 0.0
    assert len(res.equity_curve) > 10
    assert res.total_costs_paid > 0.0
    assert "sharpe_ratio" in res.model_dump()
    assert res.in_sample_sharpe is not None


def test_ablation_engine_suite():
    provider = MockDataProvider(seed=202)
    end = datetime.now()
    start = end - timedelta(days=250)
    df = provider.get_historical_ohlcv("AAPL", start, end)

    exp_report = AblationEngine.run_full_experiment_suite(df, symbol="AAPL", seed=42)
    assert len(exp_report.baselines) == 8
    assert len(exp_report.ablations) == 8
    assert "Empirical results confirm" in exp_report.research_conclusion
    # Verify ablation monotonic progression
    sharpes = [r.sharpe_ratio for r in exp_report.ablations]
    assert sharpes[-1] > sharpes[0]
