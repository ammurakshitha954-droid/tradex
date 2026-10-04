"""
Deterministic Market Regime Detection Engine.
Calculates quantifiable regime classifications, transition likelihoods, and historical timelines.
"""
from typing import List, Dict, Tuple
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from .types import MarketRegime, RegimeDetectionResult, RegimeTimelinePoint
from ..features.technical import TechnicalIndicators
from ..features.volatility import VolatilityIndicators


class MarketRegimeDetector:
    @classmethod
    def detect_regime_from_series(
        cls, 
        df: pd.DataFrame, 
        symbol: str = "BENCHMARK"
    ) -> RegimeDetectionResult:
        """
        Takes raw OHLCV DataFrame and computes regime probability distribution and timeline.
        """
        # 1. Compute features
        tech_df = TechnicalIndicators.compute_all_indicators(df)
        full_df = VolatilityIndicators.compute_volatility(tech_df)

        close = full_df["close"]
        n = len(full_df)
        if n < 30:
            # Fallback for very small window
            return cls._generate_default_regime(symbol, full_df)

        # 2. Compute historical regime points across timeline
        timeline: List[RegimeTimelinePoint] = []
        regimes_history: List[MarketRegime] = []

        step_size = max(1, n // 60)  # Downsample timeline to ~60 points for visualization
        for i in range(25, n):
            sub_slice = full_df.iloc[: i + 1]
            reg, conf, _ = cls._classify_single_snapshot(sub_slice)
            regimes_history.append(reg)

            if i % step_size == 0 or i == n - 1:
                row = sub_slice.iloc[-1]
                timeline.append(
                    RegimeTimelinePoint(
                        timestamp=sub_slice.index[-1].strftime("%Y-%m-%d"),
                        regime=reg,
                        confidence=round(conf, 3),
                        volatility_annualized=round(float(row.get("hist_vol_20d", 0.18)), 4),
                        close_price=round(float(row["close"]), 2),
                    )
                )

        # Current regime is the classification of the final snapshot
        current_regime, confidence, probs = cls._classify_single_snapshot(full_df)

        # Compute duration of current regime
        duration = 1
        for prev_reg in reversed(regimes_history[:-1]):
            if prev_reg == current_regime:
                duration += 1
            else:
                break

        # Compute stability index: ratio of days in current regime over last 20 days
        last_20_regimes = regimes_history[-20:] if len(regimes_history) >= 20 else regimes_history
        stability_score = float(sum(1 for r in last_20_regimes if r == current_regime) / len(last_20_regimes))

        # Key drivers explanation
        last_row = full_df.iloc[-1]
        dist_200 = float(last_row.get("dist_ema_200_pct", 0) * 100)
        vol_20 = float(last_row.get("hist_vol_20d", 0.18) * 100)
        bb_bw = float(last_row.get("bb_bandwidth", 0.05))

        key_drivers = []
        if dist_200 > 5.0:
            key_drivers.append(f"Price is {dist_200:+.1f}% above 200 EMA (Structural Bull structure)")
        elif dist_200 < -5.0:
            key_drivers.append(f"Price is {dist_200:+.1f}% below 200 EMA (Structural Bear structure)")
        else:
            key_drivers.append("Price oscillating near 200 EMA (Range-bound mean reversion)")

        if vol_20 > 30.0:
            key_drivers.append(f"Annualized volatility elevated at {vol_20:.1f}%")
        elif vol_20 < 12.0:
            key_drivers.append(f"Annualized volatility compressed at {vol_20:.1f}%")

        if bb_bw < 0.04:
            key_drivers.append("Bollinger Bandwidth compression suggests impending breakout/expansion")

        return RegimeDetectionResult(
            symbol=symbol.upper(),
            current_regime=current_regime,
            regime_confidence=round(confidence, 3),
            regime_probabilities={k: round(v, 3) for k, v in probs.items()},
            duration_days=duration,
            stability_score=round(stability_score, 3),
            key_drivers=key_drivers,
            timeline=timeline,
            timestamp=full_df.index[-1].isoformat(),
        )

    @classmethod
    def _classify_single_snapshot(
        cls, 
        df_slice: pd.DataFrame
    ) -> Tuple[MarketRegime, float, Dict[str, float]]:
        """
        Deterministic scoring function based on moving average structure, volatility, and drawdowns.
        """
        last = df_slice.iloc[-1]
        close = float(last["close"])
        ema_21 = float(last.get("ema_21", close))
        ema_50 = float(last.get("ema_50", close))
        ema_200 = float(last.get("ema_200", close))
        hist_vol = float(last.get("hist_vol_20d", 0.18))
        bb_bw = float(last.get("bb_bandwidth", 0.05))
        trend_score = float(last.get("trend_score", 0))

        # 252d Peak Drawdown
        rolling_high = df_slice["high"].rolling(window=min(252, len(df_slice))).max().iloc[-1]
        peak_dd = (close - rolling_high) / (rolling_high + 1e-9)

        # Initialize unnormalized logit scores for all 7 regimes
        scores: Dict[str, float] = {
            MarketRegime.BULL_TRENDING.value: 0.0,
            MarketRegime.BEAR_TRENDING.value: 0.0,
            MarketRegime.SIDEWAYS_RANGING.value: 0.0,
            MarketRegime.HIGH_VOLATILITY.value: 0.0,
            MarketRegime.LOW_VOLATILITY_COMPRESSION.value: 0.0,
            MarketRegime.CRISIS_STRESS.value: 0.0,
            MarketRegime.TRANSITION_UNCERTAIN.value: 0.0,
        }

        # 1. Bull checks
        if close > ema_50 > ema_200 and trend_score >= 50:
            scores[MarketRegime.BULL_TRENDING.value] += 3.0
            if hist_vol < 0.22:
                scores[MarketRegime.BULL_TRENDING.value] += 1.5

        # 2. Bear checks
        if close < ema_50 < ema_200 and trend_score <= -50:
            scores[MarketRegime.BEAR_TRENDING.value] += 3.0
            if hist_vol > 0.25:
                scores[MarketRegime.BEAR_TRENDING.value] += 1.0

        # 3. Crisis / Stress checks
        if peak_dd < -0.18 and hist_vol > 0.35:
            scores[MarketRegime.CRISIS_STRESS.value] += 4.5
        elif peak_dd < -0.12 and hist_vol > 0.30:
            scores[MarketRegime.CRISIS_STRESS.value] += 2.5

        # 4. High Volatility checks
        if hist_vol > 0.32:
            scores[MarketRegime.HIGH_VOLATILITY.value] += 3.5
        elif hist_vol > 0.25:
            scores[MarketRegime.HIGH_VOLATILITY.value] += 1.5

        # 5. Low Volatility Compression checks
        if bb_bw < 0.045 and hist_vol < 0.14:
            scores[MarketRegime.LOW_VOLATILITY_COMPRESSION.value] += 3.5
        elif hist_vol < 0.12:
            scores[MarketRegime.LOW_VOLATILITY_COMPRESSION.value] += 2.0

        # 6. Sideways / Ranging checks
        if abs(close - ema_50) / ema_50 < 0.02 and abs(trend_score) < 30:
            scores[MarketRegime.SIDEWAYS_RANGING.value] += 3.0

        # 7. Transition / Uncertain checks (conflicting indicators, e.g. close > 200 but close < 21)
        if (close > ema_200 and close < ema_21) or (close < ema_200 and close > ema_21):
            scores[MarketRegime.TRANSITION_UNCERTAIN.value] += 2.5

        # Softmax conversion to probabilities
        logit_array = np.array(list(scores.values()), dtype=np.float64)
        # Shift for numerical stability
        exp_logits = np.exp(logit_array - np.max(logit_array))
        probs = exp_logits / np.sum(exp_logits)

        prob_dict = {reg: float(probs[i]) for i, reg in enumerate(scores.keys())}
        best_regime_str = max(prob_dict, key=prob_dict.get)
        confidence = prob_dict[best_regime_str]

        return MarketRegime(best_regime_str), confidence, prob_dict

    @classmethod
    def _generate_default_regime(cls, symbol: str, df: pd.DataFrame) -> RegimeDetectionResult:
        now_str = datetime.now(timezone.utc).isoformat()
        probs = {r.value: 1.0 / len(MarketRegime) for r in MarketRegime}
        probs[MarketRegime.SIDEWAYS_RANGING.value] = 0.40
        return RegimeDetectionResult(
            symbol=symbol.upper(),
            current_regime=MarketRegime.SIDEWAYS_RANGING,
            regime_confidence=0.40,
            regime_probabilities=probs,
            duration_days=5,
            stability_score=0.50,
            key_drivers=["Limited history available; default sideways ranging baseline applied."],
            timeline=[],
            timestamp=now_str,
        )
