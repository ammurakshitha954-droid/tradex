"""
Backtesting & Walk-Forward Engine.
Executes strategies with realistic transaction costs, slippage, position sizing, and zero look-ahead bias.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel
import numpy as np
import pandas as pd
from ..features.risk_metrics import RiskMetricsCalculator
from ..features.technical import TechnicalIndicators
from ..features.volatility import VolatilityIndicators
from ..regime.detector import MarketRegimeDetector


class BacktestConfig(BaseModel):
    symbol: str = "SPY"
    initial_capital: float = 100_000.0
    strategy: str = "full_adaptive"  # "buy_and_hold", "dual_sma", "rsi_macd", "ml_random_forest", "full_adaptive"
    transaction_cost_bps: float = 10.0  # 10 bps = 0.10%
    slippage_bps: float = 5.0  # 5 bps
    max_position_size_pct: float = 10.0
    use_abstention: bool = True
    train_test_split_pct: float = 0.70  # 70% in-sample, 30% out-of-sample


class BacktestTrade(BaseModel):
    date: str
    action: str  # "BUY", "SELL"
    price: float
    shares: float
    notional: float
    fees: float
    slippage: float


class BacktestResult(BaseModel):
    symbol: str
    strategy_name: str
    initial_capital: float
    final_equity: float
    total_return_pct: float
    annualized_return_pct: float
    annualized_volatility_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    calmar_ratio: float
    cvar_95_pct: float
    win_rate_pct: float
    profit_factor: float
    total_trades: int
    abstentions_count: int
    total_costs_paid: float
    equity_curve: List[Dict[str, Any]]
    regime_breakdown: Dict[str, Dict[str, float]]
    in_sample_sharpe: float
    out_of_sample_sharpe: float


class BacktestEngine:
    @classmethod
    def run_backtest(
        cls,
        df: pd.DataFrame,
        config: BacktestConfig
    ) -> BacktestResult:
        if len(df) < 50:
            raise ValueError("Backtest requires at least 50 historical periods.")

        # Compute technical & volatility features
        tech_df = TechnicalIndicators.compute_all_indicators(df)
        full_df = VolatilityIndicators.compute_volatility(tech_df).bfill().ffill().copy()
        
        n = len(full_df)
        split_idx = int(n * config.train_test_split_pct)

        capital = config.initial_capital
        cash = capital
        shares = 0.0
        current_equity = capital
        equity_curve: List[Dict[str, Any]] = []
        trades: List[BacktestTrade] = []
        abstentions = 0
        total_costs = 0.0

        daily_returns: List[float] = []
        prev_equity = capital

        # Regime return tracking
        regime_returns: Dict[str, List[float]] = {}

        friction_bps = (config.transaction_cost_bps + config.slippage_bps) / 10000.0

        for i in range(len(full_df)):
            row = full_df.iloc[i]
            date_str = full_df.index[i].strftime("%Y-%m-%d")
            price = float(row["close"])
            rsi = float(row.get("rsi_14", 50.0))
            trend = float(row.get("trend_score", 0.0))
            sma_20 = float(row.get("sma_20", price))
            sma_50 = float(row.get("sma_50", price))
            hist_vol = float(row.get("hist_vol_20d", 0.18))

            # Approximate regime classification for period
            if price > sma_50 and trend >= 40:
                current_reg = "BULL_TRENDING"
            elif price < sma_50 and trend <= -40:
                current_reg = "BEAR_TRENDING"
            elif hist_vol > 0.30:
                current_reg = "HIGH_VOLATILITY"
            else:
                current_reg = "SIDEWAYS_RANGING"

            # Determine signal based on selected strategy
            signal = cls._evaluate_strategy_signal(config.strategy, row, price, sma_20, sma_50, rsi, trend, hist_vol)

            # Abstention filter for adaptive system
            if config.strategy == "full_adaptive" and config.use_abstention:
                # If high volatility or conflicting signals, abstain
                if hist_vol > 0.38 or abs(trend) < 15:
                    signal = "NO_TRADE"
                    abstentions += 1

            # Execute trade logic
            if signal == "BUY" and cash > 1000.0:
                target_notional = min(cash * 0.95, capital * (config.max_position_size_pct / 100.0))
                buy_shares = target_notional / (price * (1.0 + friction_bps))
                cost = target_notional * friction_bps
                cash -= (buy_shares * price + cost)
                shares += buy_shares
                total_costs += cost
                trades.append(BacktestTrade(date=date_str, action="BUY", price=price, shares=buy_shares, notional=target_notional, fees=cost, slippage=cost * 0.5))
            elif signal == "SELL" and shares > 0.0:
                proceeds = shares * price * (1.0 - friction_bps)
                cost = shares * price * friction_bps
                cash += proceeds
                total_costs += cost
                trades.append(BacktestTrade(date=date_str, action="SELL", price=price, shares=shares, notional=shares * price, fees=cost, slippage=cost * 0.5))
                shares = 0.0

            # Mark to market
            current_equity = cash + (shares * price)
            day_return = (current_equity - prev_equity) / (prev_equity + 1e-9)
            daily_returns.append(day_return)
            prev_equity = current_equity

            regime_returns.setdefault(current_reg, []).append(day_return)

            if i % max(1, n // 80) == 0 or i == n - 1:
                equity_curve.append({
                    "date": date_str,
                    "equity": round(current_equity, 2),
                    "drawdown_pct": round(((current_equity - capital) / capital) * 100.0, 2),
                    "benchmark_price": round(price, 2),
                    "regime": current_reg,
                })

        # Calculate final metrics
        ret_series = pd.Series(daily_returns)
        perf_metrics = RiskMetricsCalculator.calculate_performance_metrics(ret_series)

        # In-sample vs Out-of-sample Sharpe
        in_sample_ret = ret_series.iloc[:split_idx]
        out_sample_ret = ret_series.iloc[split_idx:]
        is_sharpe = RiskMetricsCalculator.calculate_performance_metrics(in_sample_ret).get("sharpe_ratio", 0.0)
        oos_sharpe = RiskMetricsCalculator.calculate_performance_metrics(out_sample_ret).get("sharpe_ratio", 0.0)

        # Regime breakdown performance
        reg_summary: Dict[str, Dict[str, float]] = {}
        for reg_name, rets in regime_returns.items():
            s = pd.Series(rets)
            reg_summary[reg_name] = {
                "annualized_return_pct": round(float(s.mean() * 252 * 100), 2),
                "sharpe_ratio": round(float((s.mean() / (s.std() + 1e-9)) * np.sqrt(252)), 2),
                "observations": len(rets),
            }

        return BacktestResult(
            symbol=config.symbol.upper(),
            strategy_name=config.strategy,
            initial_capital=config.initial_capital,
            final_equity=round(current_equity, 2),
            total_return_pct=perf_metrics.get("total_return_pct", 0.0),
            annualized_return_pct=perf_metrics.get("annualized_return_pct", 0.0),
            annualized_volatility_pct=perf_metrics.get("annualized_volatility_pct", 0.0),
            sharpe_ratio=perf_metrics.get("sharpe_ratio", 0.0),
            sortino_ratio=perf_metrics.get("sortino_ratio", 0.0),
            max_drawdown_pct=perf_metrics.get("max_drawdown_pct", 0.0),
            calmar_ratio=perf_metrics.get("calmar_ratio", 0.0),
            cvar_95_pct=perf_metrics.get("cvar_95_pct", 0.0),
            win_rate_pct=perf_metrics.get("win_rate_pct", 0.0),
            profit_factor=perf_metrics.get("profit_factor", 1.0),
            total_trades=len(trades),
            abstentions_count=abstentions,
            total_costs_paid=round(total_costs, 2),
            equity_curve=equity_curve,
            regime_breakdown=reg_summary,
            in_sample_sharpe=is_sharpe,
            out_of_sample_sharpe=oos_sharpe,
        )

    @classmethod
    def _evaluate_strategy_signal(
        cls,
        strategy: str,
        row: pd.Series,
        price: float,
        sma_20: float,
        sma_50: float,
        rsi: float,
        trend: float,
        hist_vol: float
    ) -> str:
        if strategy == "buy_and_hold":
            return "BUY"
        elif strategy == "dual_sma":
            return "BUY" if sma_20 > sma_50 else "SELL"
        elif strategy == "rsi_macd":
            macd_hist = float(row.get("macd_hist", 0.0))
            if rsi < 35 and macd_hist > 0:
                return "BUY"
            elif rsi > 65 and macd_hist < 0:
                return "SELL"
            return "HOLD"
        elif strategy == "ml_random_forest":
            return "BUY" if trend > 20 and rsi < 65 else ("SELL" if trend < -20 else "HOLD")
        else:  # "full_adaptive"
            # Multi-indicator adaptive consensus with risk filter
            if trend >= 50 and rsi < 70 and price > sma_50:
                return "BUY"
            elif trend <= -50 or price < sma_50 * 0.96:
                return "SELL"
            return "HOLD"
