"""
Model Council: Collects independent predictions and confidence scores from heterogeneous models:
1. Technical Rule Model
2. Quantitative ML Model (RandomForest / GradientBoosting classifier)
3. Statistical Mean-Reversion Model
4. Regime Specialist Model
5. News & Event Sentiment Model
"""
from typing import Dict, Any, List
from pydantic import BaseModel, Field
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from ..regime.types import MarketRegime


class ModelVote(BaseModel):
    model_name: str
    signal: str  # "BUY", "SELL", "HOLD", "NO_TRADE"
    conviction: float = Field(..., ge=0.0, le=1.0)
    primary_rationale: str
    weight: float = 1.0


class ModelCouncilResult(BaseModel):
    symbol: str
    votes: List[ModelVote]
    consensus_signal: str
    consensus_conviction: float
    vote_distribution: Dict[str, int]


class ModelCouncil:
    def __init__(self):
        # Lightweight baseline classifier pre-configured for quantitative features
        self.ml_classifier = RandomForestClassifier(n_estimators=30, max_depth=4, random_state=42)
        self._is_ml_fitted = False

    def evaluate_council(
        self,
        symbol: str,
        features_df: pd.DataFrame,
        regime: MarketRegime,
        news_sentiment: float,
        news_materiality: float,
    ) -> ModelCouncilResult:
        votes: List[ModelVote] = []

        last_row = features_df.iloc[-1]
        close = float(last_row["close"])
        rsi = float(last_row.get("rsi_14", 50.0))
        trend = float(last_row.get("trend_score", 0))
        macd_hist = float(last_row.get("macd_hist", 0.0))
        dist_200 = float(last_row.get("dist_ema_200_pct", 0.0))
        bb_pct = float(last_row.get("bb_pct", 0.5))

        # 1. Technical Rule Model
        if trend >= 50 and rsi < 72 and macd_hist > 0:
            tech_sig = "BUY"
            tech_conv = min(0.90, 0.55 + (trend / 200.0))
            tech_rat = f"Strong trend score (+{int(trend)}) with positive MACD histogram expansion."
        elif trend <= -50 and rsi > 28 and macd_hist < 0:
            tech_sig = "SELL"
            tech_conv = min(0.90, 0.55 + abs(trend / 200.0))
            tech_rat = f"Bearish trend score ({int(trend)}) and accelerating downward momentum."
        else:
            tech_sig = "HOLD"
            tech_conv = 0.50
            tech_rat = "Mixed technical indicators lacking clear directional momentum."
        votes.append(ModelVote(model_name="Technical Trend Model", signal=tech_sig, conviction=round(tech_conv, 2), primary_rationale=tech_rat, weight=1.2))

        # 2. Statistical Mean-Reversion Model
        if rsi < 30 and bb_pct < 0.10:
            mr_sig = "BUY"
            mr_conv = min(0.85, 0.50 + (30 - rsi) / 40.0)
            mr_rat = f"Statistical oversold extreme: RSI {rsi:.1f} at lower Bollinger Band ({bb_pct:.2f})."
        elif rsi > 70 and bb_pct > 0.90:
            mr_sig = "SELL"
            mr_conv = min(0.85, 0.50 + (rsi - 70) / 40.0)
            mr_rat = f"Statistical overbought extreme: RSI {rsi:.1f} at upper Bollinger Band ({bb_pct:.2f})."
        else:
            mr_sig = "HOLD"
            mr_conv = 0.50
            mr_rat = "Oscillators within normal 1-sigma dispersion bounds."
        votes.append(ModelVote(model_name="Statistical Mean-Reversion", signal=mr_sig, conviction=round(mr_conv, 2), primary_rationale=mr_rat, weight=1.0))

        # 3. Machine Learning Quantitative Model (RandomForest)
        # Train on recent historical windows if not already fitted
        ml_sig, ml_conv, ml_rat = self._predict_ml(features_df)
        votes.append(ModelVote(model_name="Quantitative ML (Random Forest)", signal=ml_sig, conviction=round(ml_conv, 2), primary_rationale=ml_rat, weight=1.1))

        # 4. Regime Specialist Model
        if regime == MarketRegime.BULL_TRENDING:
            reg_sig = "BUY"
            reg_conv = 0.75
            reg_rat = "Macro regime provides structural tailwind for risk-on positioning."
        elif regime in [MarketRegime.BEAR_TRENDING, MarketRegime.CRISIS_STRESS]:
            reg_sig = "SELL"
            reg_conv = 0.85 if regime == MarketRegime.CRISIS_STRESS else 0.70
            reg_rat = f"Adverse macro regime ({regime.value}) elevates systemic downside beta."
        elif regime == MarketRegime.HIGH_VOLATILITY:
            reg_sig = "HOLD"
            reg_conv = 0.65
            reg_rat = "High volatility regime mandates risk conservation."
        else:
            reg_sig = "HOLD"
            reg_conv = 0.50
            reg_rat = f"Neutral/Ranging regime ({regime.value}) offers no distinct statistical edge."
        votes.append(ModelVote(model_name="Regime Specialist", signal=reg_sig, conviction=round(reg_conv, 2), primary_rationale=reg_rat, weight=1.0))

        # 5. News & Event Intelligence Model
        effective_news_impact = news_sentiment * news_materiality
        if news_materiality >= 0.40:
            if effective_news_impact > 0.20:
                news_sig = "BUY"
                news_conv = min(0.85, 0.50 + abs(effective_news_impact))
                news_rat = f"High-materiality positive catalysts (Sentiment: {news_sentiment:+.2f})."
            elif effective_news_impact < -0.20:
                news_sig = "SELL"
                news_conv = min(0.85, 0.50 + abs(effective_news_impact))
                news_rat = f"High-materiality negative headline pressure (Sentiment: {news_sentiment:+.2f})."
            else:
                news_sig = "HOLD"
                news_conv = 0.50
                news_rat = "Moderate materiality news with balanced sentiment."
        else:
            news_sig = "HOLD"
            news_conv = 0.45
            news_rat = "Current news flow is largely noise with negligible financial materiality."
        votes.append(ModelVote(model_name="News & Event Intelligence", signal=news_sig, conviction=round(news_conv, 2), primary_rationale=news_rat, weight=0.9))

        # Calculate Consensus
        counts = {"BUY": 0, "SELL": 0, "HOLD": 0, "NO_TRADE": 0}
        weighted_scores = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0, "NO_TRADE": 0.0}

        for v in votes:
            counts[v.signal] = counts.get(v.signal, 0) + 1
            weighted_scores[v.signal] += v.conviction * v.weight

        consensus = max(weighted_scores, key=weighted_scores.get)
        total_weight = sum(v.weight for v in votes)
        consensus_conviction = min(0.95, weighted_scores[consensus] / total_weight)

        return ModelCouncilResult(
            symbol=symbol.upper(),
            votes=votes,
            consensus_signal=consensus,
            consensus_conviction=round(consensus_conviction, 2),
            vote_distribution=counts,
        )

    def _predict_ml(self, features_df: pd.DataFrame) -> tuple[str, float, str]:
        """Trains or evaluates Random Forest on historical features."""
        try:
            df = features_df.dropna().copy()
            if len(df) < 50:
                return "HOLD", 0.50, "Insufficient feature history for statistical ML model."

            # Construct training features: returns, RSI, MACD, distance from 50 EMA
            feature_cols = ["rsi_14", "trend_score", "macd_hist", "dist_ema_50_pct", "bb_bandwidth"]
            available_cols = [c for c in feature_cols if c in df.columns]
            
            # Target: forward 5-day return > 0 (1 for Up, 0 for Down)
            forward_ret = df["close"].shift(-5) / df["close"] - 1.0
            y = (forward_ret > 0.005).astype(int).iloc[:-5]
            X = df[available_cols].iloc[:-5]

            if len(X) > 40 and not self._is_ml_fitted:
                self.ml_classifier.fit(X, y)
                self._is_ml_fitted = True

            # Predict current state
            current_x = df[available_cols].iloc[[-1]]
            prob_up = float(self.ml_classifier.predict_proba(current_x)[0][1])

            if prob_up >= 0.58:
                return "BUY", prob_up, f"Random Forest probability of positive 5-day forward return is {prob_up * 100:.1f}%."
            elif prob_up <= 0.42:
                prob_down = 1.0 - prob_up
                return "SELL", prob_down, f"Random Forest probability of negative 5-day forward return is {prob_down * 100:.1f}%."
            else:
                return "HOLD", 0.50, f"Random Forest neutral probability ({prob_up * 100:.1f}%), within no-edge threshold."
        except Exception as e:
            return "HOLD", 0.50, f"ML model evaluation fallback: {e}"
