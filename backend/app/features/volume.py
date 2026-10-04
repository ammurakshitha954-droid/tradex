"""
Deterministic Quantitative Engine: Volume & Liquidity Indicators.
"""
from typing import Dict, Any
import numpy as np
import pandas as pd


class VolumeIndicators:
    @staticmethod
    def compute_volume_metrics(df: pd.DataFrame) -> pd.DataFrame:
        res = df.copy()
        close = res["close"]
        volume = res["volume"]

        # 1. Volume moving averages
        res["volume_sma_20"] = volume.rolling(window=20).mean()
        res["volume_sma_50"] = volume.rolling(window=50).mean()

        # 2. Relative Volume (RVOL)
        res["rvol_20"] = volume / (res["volume_sma_20"] + 1e-9)

        # 3. Abnormal Volume Flag (> 2.0x 20d SMA)
        res["abnormal_volume"] = res["rvol_20"] > 2.0

        # 4. On-Balance Volume (OBV)
        direction = np.sign(close.diff()).fillna(0)
        res["obv"] = (direction * volume).cumsum()
        res["obv_ema_21"] = res["obv"].ewm(span=21, adjust=False).mean()

        # 5. Volume Trend Score
        res["volume_trend"] = np.where(res["obv"] > res["obv_ema_21"], 1, -1)

        return res

    @staticmethod
    def get_latest_volume_summary(df_with_vol: pd.DataFrame) -> Dict[str, Any]:
        if df_with_vol.empty:
            return {}
        last = df_with_vol.iloc[-1]
        
        rvol = float(last.get("rvol_20", 1.0))
        abnormal = bool(last.get("abnormal_volume", False))
        vol_trend = int(last.get("volume_trend", 0))

        return {
            "current_volume": int(last["volume"]),
            "volume_sma_20": int(last.get("volume_sma_20", last["volume"])),
            "relative_volume_20": round(rvol, 2),
            "is_abnormal_volume": abnormal,
            "obv_trend": "ACCUMULATION" if vol_trend > 0 else "DISTRIBUTION",
        }
