"""
Deterministic Quantitative Engine: Risk & Performance Metrics.
Calculates Sharpe, Sortino, Max Drawdown, Calmar, VaR (95%/99%), CVaR, Beta, and Alpha.
"""
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd


class RiskMetricsCalculator:
    TRADING_DAYS_PER_YEAR = 252

    @classmethod
    def calculate_drawdown_series(cls, cumulative_returns: pd.Series) -> pd.DataFrame:
        """
        Calculates high-water mark, drawdown series, and maximum drawdown.
        cumulative_returns: Series of cumulative return values (1.0 + r).cumprod()
        """
        hwm = cumulative_returns.cummax()
        drawdown = (cumulative_returns - hwm) / hwm
        return pd.DataFrame({
            "hwm": hwm,
            "drawdown": drawdown
        })

    @classmethod
    def calculate_performance_metrics(
        cls,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None,
        risk_free_rate: float = 0.04
    ) -> Dict[str, Any]:
        """
        Deterministic calculations for risk and return characteristics.
        returns: Daily percentage returns series (e.g. 0.01 for 1%).
        """
        clean_ret = returns.dropna()
        n = len(clean_ret)
        if n < 5:
            return {
                "error": "Insufficient data to calculate risk metrics (minimum 5 observations needed)."
            }

        daily_rf = (1.0 + risk_free_rate) ** (1.0 / cls.TRADING_DAYS_PER_YEAR) - 1.0

        # Cumulative performance
        cum_ret_series = (1.0 + clean_ret).cumprod()
        total_return = float(cum_ret_series.iloc[-1] - 1.0)
        annualized_return = float((1.0 + total_return) ** (cls.TRADING_DAYS_PER_YEAR / max(1, n)) - 1.0)

        # Volatility
        daily_vol = float(clean_ret.std())
        annualized_vol = daily_vol * np.sqrt(cls.TRADING_DAYS_PER_YEAR)

        # Sharpe Ratio
        excess_returns = clean_ret - daily_rf
        mean_excess = float(excess_returns.mean())
        sharpe_ratio = float((mean_excess / (daily_vol + 1e-9)) * np.sqrt(cls.TRADING_DAYS_PER_YEAR)) if daily_vol > 0 else 0.0

        # Sortino Ratio (downside risk only)
        downside_returns = clean_ret[clean_ret < daily_rf] - daily_rf
        downside_dev = float(np.sqrt(np.mean(downside_returns ** 2))) if len(downside_returns) > 0 else daily_vol
        sortino_ratio = float((mean_excess / (downside_dev + 1e-9)) * np.sqrt(cls.TRADING_DAYS_PER_YEAR)) if downside_dev > 0 else 0.0

        # Drawdowns
        dd_df = cls.calculate_drawdown_series(cum_ret_series)
        max_drawdown = float(dd_df["drawdown"].min())  # negative float
        current_drawdown = float(dd_df["drawdown"].iloc[-1])

        # Calmar Ratio (annualized return / abs(max drawdown))
        calmar_ratio = float(annualized_return / (abs(max_drawdown) + 1e-9)) if abs(max_drawdown) > 0 else 0.0

        # Value at Risk (VaR 95% and 99% - 1-day historical)
        var_95 = float(np.percentile(clean_ret, 5))
        var_99 = float(np.percentile(clean_ret, 1))

        # Conditional VaR (CVaR / Expected Shortfall - 95%)
        cvar_95 = float(clean_ret[clean_ret <= var_95].mean()) if len(clean_ret[clean_ret <= var_95]) > 0 else var_95

        # Win Rate & Profit Factor
        winning_trades = clean_ret[clean_ret > 0]
        losing_trades = clean_ret[clean_ret < 0]
        win_rate = float(len(winning_trades) / n) if n > 0 else 0.0
        gross_profit = float(winning_trades.sum())
        gross_loss = float(abs(losing_trades.sum()))
        profit_factor = float(gross_profit / (gross_loss + 1e-9)) if gross_loss > 0 else 1.0

        # Benchmark metrics (Beta, Correlation, Alpha)
        beta = 1.0
        correlation = 1.0
        alpha = 0.0
        if benchmark_returns is not None:
            aligned = pd.concat([clean_ret, benchmark_returns], axis=1).dropna()
            if len(aligned) > 5:
                asset_r = aligned.iloc[:, 0]
                bench_r = aligned.iloc[:, 1]
                cov_mat = np.cov(asset_r, bench_r)
                bench_var = cov_mat[1, 1]
                if bench_var > 0:
                    beta = float(cov_mat[0, 1] / bench_var)
                corr_val = np.corrcoef(asset_r, bench_r)[0, 1]
                if not np.isnan(corr_val):
                    correlation = float(corr_val)
                bench_annual_ret = float((1.0 + bench_r.mean()) ** cls.TRADING_DAYS_PER_YEAR - 1.0)
                alpha = float(annualized_return - (risk_free_rate + beta * (bench_annual_ret - risk_free_rate)))

        return {
            "total_return_pct": round(total_return * 100, 2),
            "annualized_return_pct": round(annualized_return * 100, 2),
            "annualized_volatility_pct": round(annualized_vol * 100, 2),
            "sharpe_ratio": round(sharpe_ratio, 3),
            "sortino_ratio": round(sortino_ratio, 3),
            "max_drawdown_pct": round(max_drawdown * 100, 2),
            "current_drawdown_pct": round(current_drawdown * 100, 2),
            "calmar_ratio": round(calmar_ratio, 3),
            "var_95_pct": round(abs(var_95) * 100, 2),
            "var_99_pct": round(abs(var_99) * 100, 2),
            "cvar_95_pct": round(abs(cvar_95) * 100, 2),
            "win_rate_pct": round(win_rate * 100, 2),
            "profit_factor": round(profit_factor, 2),
            "beta": round(beta, 3),
            "correlation": round(correlation, 3),
            "alpha_pct": round(alpha * 100, 2),
            "sample_size_days": n,
        }
