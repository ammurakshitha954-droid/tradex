"""
Deterministic Uncertainty Estimation and Abstention Engine.
Calculates calibrated confidence, composite uncertainty, and treats NO_TRADE as a first-class decision.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import numpy as np
from ..regime.types import MarketRegime
from .conflict_engine import EvidenceConflictAnalysis
from ..models.council import ModelCouncilResult


class ConfidenceBreakdown(BaseModel):
    technical_confidence: float
    news_confidence: float
    regime_confidence: float
    model_agreement_confidence: float
    volatility_quality_score: float
    data_quality_score: float


class UncertaintyAssessment(BaseModel):
    symbol: str
    composite_uncertainty: float = Field(..., ge=0.0, le=1.0)
    calibrated_confidence: float = Field(..., ge=0.0, le=1.0)
    should_abstain: bool
    recommended_action: str  # "BUY", "SELL", "HOLD", "NO_TRADE"
    abstention_reasons: List[str]
    confidence_drivers: List[str]
    confidence_reducers: List[str]
    breakdown: ConfidenceBreakdown


class UncertaintyEngine:
    MIN_CONFIDENCE_THRESHOLD = 0.55
    MAX_CONFLICT_THRESHOLD = 0.60
    MAX_UNCERTAINTY_FOR_ACTION = 0.55

    @classmethod
    def evaluate(
        cls,
        symbol: str,
        council_result: ModelCouncilResult,
        conflict_analysis: EvidenceConflictAnalysis,
        regime: MarketRegime,
        regime_confidence: float,
        vol_summary: Dict[str, Any],
        news_sentiment: float,
        news_materiality: float,
        data_quality_score: float = 1.0,
    ) -> UncertaintyAssessment:
        drivers: List[str] = []
        reducers: List[str] = []
        abstention_reasons: List[str] = []

        # 1. Base Council Conviction
        base_conviction = council_result.consensus_conviction
        consensus_action = council_result.consensus_signal

        # 2. Measurable Uncertainty Factors
        # A. Disagreement & Conflict Penalty
        conflict_penalty = conflict_analysis.disagreement_score * 0.40
        if conflict_analysis.disagreement_score > 0.40:
            reducers.append(f"Model disagreement elevated ({conflict_analysis.disagreement_score * 100:.1f}%), penalizing conviction")
        else:
            drivers.append(f"Solid model consensus ({conflict_analysis.agreement_score * 100:.1f}% agreement)")

        # B. Regime Uncertainty Penalty
        regime_penalty = (1.0 - regime_confidence) * 0.25
        if regime in [MarketRegime.TRANSITION_UNCERTAIN, MarketRegime.HIGH_VOLATILITY, MarketRegime.CRISIS_STRESS]:
            regime_penalty += 0.15
            reducers.append(f"Challenging market regime: {regime.value} reduces predictability")
        else:
            drivers.append(f"Stable regime environment: {regime.value} ({regime_confidence * 100:.1f}% confidence)")

        # C. Volatility Penalty
        vol_regime = vol_summary.get("volatility_regime", "NORMAL")
        is_vol_expanding = vol_summary.get("is_volatility_expanding", False)
        vol_penalty = 0.0
        if vol_regime in ["ELEVATED", "EXTREME"]:
            vol_penalty = 0.15 if vol_regime == "ELEVATED" else 0.30
            reducers.append(f"Volatility regime {vol_regime} widens expected outcome dispersion")
        if is_vol_expanding:
            vol_penalty += 0.05
            reducers.append("Expanding short-term volatility relative to 60-day baseline")

        # D. Data Quality Penalty
        data_penalty = (1.0 - data_quality_score) * 0.50
        if data_quality_score < 0.90:
            reducers.append("Data feed latency or missing tick imputation detected")

        # Composite Uncertainty Calculation [0.0 to 1.0]
        composite_uncertainty = float(np.clip(
            conflict_penalty + regime_penalty + vol_penalty + data_penalty,
            0.05,
            0.95
        ))

        # Calibrated Confidence = Base Conviction * (1 - Composite Uncertainty)
        calibrated_confidence = float(np.clip(
            base_conviction * (1.0 - 0.75 * composite_uncertainty),
            0.10,
            0.95
        ))

        # 3. Explicit First-Class Abstention Logic (NO_TRADE)
        should_abstain = False

        if calibrated_confidence < cls.MIN_CONFIDENCE_THRESHOLD and consensus_action in ["BUY", "SELL"]:
            should_abstain = True
            abstention_reasons.append(
                f"Calibrated confidence ({calibrated_confidence * 100:.1f}%) is below minimum threshold ({cls.MIN_CONFIDENCE_THRESHOLD * 100:.0f}%)."
            )

        if conflict_analysis.disagreement_score >= cls.MAX_CONFLICT_THRESHOLD:
            should_abstain = True
            abstention_reasons.append(
                f"Evidence conflict score ({conflict_analysis.disagreement_score * 100:.1f}%) exceeds safety ceiling ({cls.MAX_CONFLICT_THRESHOLD * 100:.0f}%)."
            )

        if regime == MarketRegime.CRISIS_STRESS and consensus_action == "BUY":
            should_abstain = True
            abstention_reasons.append("Abstaining from aggressive BUY action during active CRISIS_STRESS regime.")

        if vol_regime == "EXTREME" and consensus_action != "HOLD":
            should_abstain = True
            abstention_reasons.append("Extreme volatility regime triggered automatic liquidity preservation abstention.")

        # Determine Final Recommended Action
        if should_abstain:
            recommended_action = "NO_TRADE"
        else:
            recommended_action = consensus_action

        # Detailed breakdown
        breakdown = ConfidenceBreakdown(
            technical_confidence=round(float(next((v.conviction for v in council_result.votes if "Technical" in v.model_name), 0.5)), 2),
            news_confidence=round(float(0.5 + abs(news_sentiment * news_materiality) * 0.4), 2),
            regime_confidence=round(regime_confidence, 2),
            model_agreement_confidence=round(conflict_analysis.agreement_score, 2),
            volatility_quality_score=round(float(1.0 - vol_penalty), 2),
            data_quality_score=round(data_quality_score, 2),
        )

        return UncertaintyAssessment(
            symbol=symbol.upper(),
            composite_uncertainty=round(composite_uncertainty, 3),
            calibrated_confidence=round(calibrated_confidence, 3),
            should_abstain=should_abstain,
            recommended_action=recommended_action,
            abstention_reasons=abstention_reasons,
            confidence_drivers=drivers or ["Standard multi-factor equilibrium"],
            confidence_reducers=reducers or ["No major structural headwinds identified"],
            breakdown=breakdown,
        )
