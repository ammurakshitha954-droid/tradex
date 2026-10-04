"""
Deterministic Quantitative Engine: Technical & Trend Indicators.
Implemented strictly in deterministic Python using Pandas and NumPy.
"""
from typing import Dict, Any
import numpy as np
import pandas as pd


class TechnicalIndicators:
    @staticmethod
    def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Takes raw validated OHLCV DataFrame and appends technical features.
        Returns a new DataFrame without mutating original.
        """
        res = df.copy()
        close = res["close"]
        high = res["high"]
        low = res["low"]
        volume = res["volume"]

        # 1. Returns
        res["return_1d"] = close.pct_change(1)
        res["return_5d"] = close.pct_change(5)
        res["return_20d"] = close.pct_change(20)
        res["log_return_1d"] = np.log(close / close.shift(1))

        # 2. Moving Averages (SMA & EMA)
        res["sma_20"] = close.rolling(window=20).mean()
        res["sma_50"] = close.rolling(window=50).mean()
        res["sma_200"] = close.rolling(window=200).mean()

        res["ema_9"] = close.ewm(span=9, adjust=False).mean()
        res["ema_21"] = close.ewm(span=21, adjust=False).mean()
        res["ema_50"] = close.ewm(span=50, adjust=False).mean()
        res["ema_200"] = close.ewm(span=200, adjust=False).mean()

        # Distance from moving averages
        res["dist_ema_21_pct"] = (close - res["ema_21"]) / res["ema_21"]
        res["dist_ema_50_pct"] = (close - res["ema_50"]) / res["ema_50"]
        res["dist_ema_200_pct"] = (close - res["ema_200"]) / res["ema_200"]

        # 3. MACD (12, 26, 9)
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        res["macd"] = ema_12 - ema_26
        res["macd_signal"] = res["macd"].ewm(span=9, adjust=False).mean()
        res["macd_hist"] = res["macd"] - res["macd_signal"]

        # 4. RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0.0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        res["rsi_14"] = 100.0 - (100.0 / (1.0 + rs))

        # 5. Bollinger Bands (20-day, 2-std)
        bb_std = close.rolling(window=20).std()
        res["bb_upper"] = res["sma_20"] + (2.0 * bb_std)
        res["bb_lower"] = res["sma_20"] - (2.0 * bb_std)
        res["bb_bandwidth"] = (res["bb_upper"] - res["bb_lower"]) / (res["sma_20"] + 1e-9)
        res["bb_pct"] = (close - res["bb_lower"]) / ((res["bb_upper"] - res["bb_lower"]) + 1e-9)

        # 6. ATR (Average True Range, 14)
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        res["atr_14"] = true_range.rolling(window=14).mean()
        res["atr_pct"] = res["atr_14"] / close

        # 7. Momentum & Breakout Levels
        res["momentum_10d"] = close / close.shift(10) - 1.0
        res["momentum_20d"] = close / close.shift(20) - 1.0
        res["high_20d"] = high.rolling(window=20).max()
        res["low_20d"] = low.rolling(window=20).min()
        res["breakout_high_20d"] = close >= res["high_20d"].shift(1)
        res["breakout_low_20d"] = close <= res["low_20d"].shift(1)

        # 8. Trend Strength Score (-100 to +100)
        # Combines moving average alignment + MACD + RSI
        trend_score = np.zeros(len(res))
        trend_score += np.where(close > res["ema_21"], 25, -25)
        trend_score += np.where(res["ema_21"] > res["ema_50"], 25, -25)
        trend_score += np.where(res["ema_50"] > res["ema_200"], 25, -25)
        trend_score += np.where(res["macd_hist"] > 0, 25, -25)
        res["trend_score"] = trend_score

        return res

    @staticmethod
    def get_latest_signal_summary(df_with_features: pd.DataFrame) -> Dict[str, Any]:
        """Extracts the latest row as a clean structured summary dictionary."""
        if df_with_features.empty:
            return {}
        last = df_with_features.iloc[-1]
        
        # Rule-based signal assessment
        rsi = float(last.get("rsi_14", 50))
        trend = float(last.get("trend_score", 0))
        macd_hist = float(last.get("macd_hist", 0))
        dist_200 = float(last.get("dist_ema_200_pct", 0))

        if trend >= 50 and rsi < 70 and macd_hist > 0:
            technical_signal = "BUY"
            signal_conviction = min(0.90, 0.50 + (trend / 200.0))
        elif trend <= -50 and rsi > 30 and macd_hist < 0:
            technical_signal = "SELL"
            signal_conviction = min(0.90, 0.50 + abs(trend / 200.0))
        else:
            technical_signal = "HOLD"
            signal_conviction = 0.50

        return {
            "close": round(float(last["close"]), 2),
            "rsi_14": round(rsi, 2),
            "trend_score": int(trend),
            "dist_ema_21_pct": round(float(last.get("dist_ema_21_pct", 0) * 100), 2),
            "dist_ema_50_pct": round(float(last.get("dist_ema_50_pct", 0) * 100), 2),
            "dist_ema_200_pct": round(float(dist_200 * 100), 2),
            "macd": round(float(last.get("macd", 0)), 3),
            "macd_signal": round(float(last.get("macd_signal", 0)), 3),
            "macd_hist": round(float(macd_hist), 3),
            "bb_bandwidth": round(float(last.get("bb_bandwidth", 0)), 4),
            "bb_pct": round(float(last.get("bb_pct", 0.5)), 2),
            "atr_14": round(float(last.get("atr_14", 0)), 2),
            "atr_pct": round(float(last.get("atr_pct", 0) * 100), 2),
            "breakout_high_20d": bool(last.get("breakout_high_20d", False)),
            "breakout_low_20d": bool(last.get("breakout_low_20d", False)),
            "technical_signal": technical_signal,
            "signal_conviction": round(signal_conviction, 3),
            "timestamp": df_with_features.index[-1].isoformat(),
        }
