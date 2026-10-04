"""
Deterministic Quantitative Engine: Volatility & Dispersion Indicators.
Calculates historical rolling volatility, Parkinson volatility, and downside deviation.
"""
from typing import Dict, Any
import numpy as np
import pandas as pd


class VolatilityIndicators:
    @staticmethod
    def compute_volatility(df: pd.DataFrame) -> pd.DataFrame:
        res = df.copy()
        close = res["close"]
        high = res["high"]
        low = res["low"]

        # Daily returns
        ret = close.pct_change()

        # 1. Realized Rolling Volatility (annualized, 252 trading days)
        res["hist_vol_20d"] = ret.rolling(window=20).std() * np.sqrt(252)
        res["hist_vol_60d"] = ret.rolling(window=60).std() * np.sqrt(252)

        # 2. Parkinson Volatility (uses High/Low range for higher statistical efficiency)
        hl_ratio = np.log(high / low)
        parkinson_factor = 1.0 / (4.0 * np.log(2.0))
        res["parkinson_vol_20d"] = np.sqrt(
            hl_ratio.pow(2).rolling(window=20).mean() * parkinson_factor * 252
        )

        # 3. Downside Deviation (Semi-variance for Sortino computation)
        negative_returns = ret.clip(upper=0)
        res["downside_dev_20d"] = np.sqrt(
            negative_returns.pow(2).rolling(window=20).mean() * 252
        )

        # 4. Volatility Ratio (Short-term 20d vs Long-term 60d)
        res["vol_ratio_20_60"] = res["hist_vol_20d"] / (res["hist_vol_60d"] + 1e-9)

        return res

    @staticmethod
    def get_latest_volatility_summary(df_with_vol: pd.DataFrame) -> Dict[str, Any]:
        if df_with_vol.empty:
            return {}
        last = df_with_vol.iloc[-1]
        
        hist_vol_20 = float(last.get("hist_vol_20d", 0.20))
        vol_ratio = float(last.get("vol_ratio_20_60", 1.0))
        downside_dev = float(last.get("downside_dev_20d", 0.15))

        if hist_vol_20 < 0.15:
            vol_regime = "LOW"
        elif hist_vol_20 <= 0.28:
            vol_regime = "NORMAL"
        elif hist_vol_20 <= 0.45:
            vol_regime = "ELEVATED"
        else:
            vol_regime = "EXTREME"

        return {
            "hist_vol_20d_pct": round(hist_vol_20 * 100, 2),
            "hist_vol_60d_pct": round(float(last.get("hist_vol_60d", 0.20)) * 100, 2),
            "parkinson_vol_20d_pct": round(float(last.get("parkinson_vol_20d", hist_vol_20)) * 100, 2),
            "downside_dev_pct": round(downside_dev * 100, 2),
            "vol_ratio_20_60": round(vol_ratio, 2),
            "volatility_regime": vol_regime,
            "is_volatility_expanding": bool(vol_ratio > 1.25),
        }
