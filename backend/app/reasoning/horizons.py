"""
Multi-Horizon Reasoning Engine: Evaluates trade candidate across Short-, Medium-, and Long-Term horizons.
Explicitly detects horizon agreement/disagreement, strongest/weakest horizon, and conflict impact.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from ..regime.types import MarketRegime


class HorizonSignal(BaseModel):
    timeframe: str  # "Short-Term (1-5d)", "Medium-Term (2-8w)", "Long-Term (3-12m)"
    action: str  # "BUY", "SELL", "HOLD", "NO_TRADE"
    conviction: float = Field(..., ge=0.0, le=1.0)
    drivers: List[str]
    risks: List[str]


class MultiHorizonAnalysis(BaseModel):
    symbol: str
    short_term: HorizonSignal
    medium_term: HorizonSignal
    long_term: HorizonSignal
    horizon_agreement: bool
    agreement_score: float = Field(..., ge=0.0, le=1.0)
    strongest_horizon: str
    weakest_horizon: str
    conflict_summary: str
    decision_impact: str


class MultiHorizonEngine:
    @classmethod
    def analyze(
        cls,
        symbol: str,
        tech_summary: Dict[str, Any],
        vol_summary: Dict[str, Any],
        vol_metrics: Dict[str, Any],
        regime: MarketRegime,
        fundamentals: Optional[Dict[str, Any]] = None,
        sentiment_score: float = 0.0,
    ) -> MultiHorizonAnalysis:
        """
        Synthesizes technical, regime, volume, and fundamental data across 3 horizons.
        """
        rsi = tech_summary.get("rsi_14", 50.0)
        trend = tech_summary.get("trend_score", 0)
        macd_hist = tech_summary.get("macd_hist", 0.0)
        dist_21 = tech_summary.get("dist_ema_21_pct", 0.0)
        dist_50 = tech_summary.get("dist_ema_50_pct", 0.0)
        dist_200 = tech_summary.get("dist_ema_200_pct", 0.0)
        rvol = vol_metrics.get("relative_volume_20", 1.0)
        is_vol_expanding = vol_summary.get("is_volatility_expanding", False)

        # 1. Short-Term Analysis (1-5 days)
        st_drivers = []
        st_risks = []
        st_score = 0.0  # -1.0 to 1.0

        if rsi < 35 and macd_hist > 0:
            st_score += 0.5
            st_drivers.append(f"RSI oversold rebound ({rsi:.1f}) with positive MACD divergence")
        elif rsi > 70:
            st_score -= 0.5
            st_risks.append(f"Short-term overbought exhaustion (RSI {rsi:.1f})")

        if dist_21 > 0:
            st_score += 0.3
            st_drivers.append(f"Price holding above 21-day EMA (+{dist_21:.1f}%)")
        else:
            st_score -= 0.3
            st_risks.append(f"Price trading below short-term 21 EMA ({dist_21:.1f}%)")

        if rvol > 1.4:
            st_drivers.append(f"Volume expansion confirms participation (RVOL {rvol:.2f}x)")
        elif rvol < 0.6:
            st_risks.append("Light liquidity / volume dry-up")

        if sentiment_score > 0.3:
            st_score += 0.2
            st_drivers.append("Positive breaking event sentiment")
        elif sentiment_score < -0.3:
            st_score -= 0.3
            st_risks.append("Negative headline pressure")

        st_action = "BUY" if st_score >= 0.25 else ("SELL" if st_score <= -0.25 else "HOLD")
        st_conviction = min(0.95, max(0.40, 0.50 + abs(st_score) * 0.4))
        short_term = HorizonSignal(
            timeframe="Short-Term (1-5d)",
            action=st_action,
            conviction=round(st_conviction, 2),
            drivers=st_drivers or ["Neutral short-term consolidation"],
            risks=st_risks or ["Normal intraday volatility"],
        )

        # 2. Medium-Term Analysis (2-8 weeks)
        mt_drivers = []
        mt_risks = []
        mt_score = 0.0

        if regime == MarketRegime.BULL_TRENDING:
            mt_score += 0.5
            mt_drivers.append("Macro/Market regime is BULL_TRENDING")
        elif regime in [MarketRegime.BEAR_TRENDING, MarketRegime.CRISIS_STRESS]:
            mt_score -= 0.6
            mt_risks.append(f"Unfavorable market regime: {regime.value}")

        if dist_50 > 0:
            mt_score += 0.3
            mt_drivers.append(f"Intermediate trend healthy (above 50 EMA by {dist_50:.1f}%)")
        else:
            mt_score -= 0.3
            mt_risks.append(f"Intermediate trend broken below 50 EMA ({dist_50:.1f}%)")

        if is_vol_expanding and regime == MarketRegime.HIGH_VOLATILITY:
            mt_risks.append("Volatility expansion increases medium-term path uncertainty")

        mt_action = "BUY" if mt_score >= 0.25 else ("SELL" if mt_score <= -0.25 else "HOLD")
        mt_conviction = min(0.95, max(0.40, 0.50 + abs(mt_score) * 0.4))
        medium_term = HorizonSignal(
            timeframe="Medium-Term (2-8w)",
            action=mt_action,
            conviction=round(mt_conviction, 2),
            drivers=mt_drivers or ["Balanced intermediate technical structure"],
            risks=mt_risks or ["Macro regime transition risk"],
        )

        # 3. Long-Term Analysis (3-12 months)
        lt_drivers = []
        lt_risks = []
        lt_score = 0.0

        if dist_200 > 0:
            lt_score += 0.4
            lt_drivers.append(f"Structural secular trend intact (above 200 EMA by {dist_200:.1f}%)")
        else:
            lt_score -= 0.5
            lt_risks.append(f"Structural secular downtrend (below 200 EMA by {dist_200:.1f}%)")

        pe = fundamentals.get("pe_ratio") if fundamentals else None
        if pe and pe > 40:
            lt_risks.append(f"Elevated valuation multiple (P/E {pe:.1f})")
        elif pe and pe < 18:
            lt_score += 0.2
            lt_drivers.append(f"Attractive relative valuation (P/E {pe:.1f})")

        lt_action = "BUY" if lt_score >= 0.25 else ("SELL" if lt_score <= -0.25 else "HOLD")
        lt_conviction = min(0.95, max(0.40, 0.50 + abs(lt_score) * 0.4))
        long_term = HorizonSignal(
            timeframe="Long-Term (3-12m)",
            action=lt_action,
            conviction=round(lt_conviction, 2),
            drivers=lt_drivers or ["Neutral secular equilibrium"],
            risks=lt_risks or ["Long-term valuation multiple compression"],
        )

        # Horizon Agreement / Disagreement Synthesis
        actions = [short_term.action, medium_term.action, long_term.action]
        unique_actions = set(actions)
        all_agree = len(unique_actions) == 1

        convictions = {
            "Short-Term": short_term.conviction,
            "Medium-Term": medium_term.conviction,
            "Long-Term": long_term.conviction,
        }
        strongest_horizon = max(convictions, key=convictions.get)
        weakest_horizon = min(convictions, key=convictions.get)

        if all_agree:
            agreement_score = 1.0
            conflict_summary = f"Complete multi-horizon alignment: All horizons indicate {actions[0]}."
            decision_impact = "High structural conviction across all time horizons allows normal target position sizing."
        elif len(unique_actions) == 2:
            agreement_score = 0.60
            conflict_summary = f"Partial horizon tension: Short-Term={short_term.action}, Medium-Term={medium_term.action}, Long-Term={long_term.action}."
            if short_term.action == "BUY" and (medium_term.action == "SELL" or long_term.action == "SELL"):
                decision_impact = "Tactical counter-trend rally inside higher-timeframe resistance. Risk Guardian requires reduced sizing or tighter trailing stops."
            elif short_term.action == "SELL" and (medium_term.action == "BUY" and long_term.action == "BUY"):
                decision_impact = "Short-term pullback inside structural secular uptrend. Wait for stabilization before deploying full capital."
            else:
                decision_impact = "Mixed signals across horizons mandate cautious position sizing and higher abstention scrutiny."
        else:
            agreement_score = 0.20
            conflict_summary = "Severe horizon divergence: Short-Term, Medium-Term, and Long-Term signals are all contradictory."
            decision_impact = "Severe time-horizon conflict elevates uncertainty significantly. Prime candidate for NO_TRADE abstention."

        return MultiHorizonAnalysis(
            symbol=symbol.upper(),
            short_term=short_term,
            medium_term=medium_term,
            long_term=long_term,
            horizon_agreement=all_agree,
            agreement_score=round(agreement_score, 2),
            strongest_horizon=strongest_horizon,
            weakest_horizon=weakest_horizon,
            conflict_summary=conflict_summary,
            decision_impact=decision_impact,
        )
