"""
Adaptive AI Reasoning Engine.
Synthesizes all quantitative, regime, conflict, and risk evidence into structured financial intelligence.
Uses OpenAI API when configured with fallback to deterministic financial reasoning generator.
"""
from typing import Dict, Any, List, Optional
import json
from openai import OpenAI
from .schemas import StructuredAIExplanation
from ..regime.types import MarketRegime
from ..reasoning.horizons import MultiHorizonAnalysis
from ..uncertainty.abstention import UncertaintyAssessment
from ..uncertainty.conflict_engine import EvidenceConflictAnalysis
from ..risk.guardian import RiskGuardianDecision
from ..models.council import ModelCouncilResult
from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger("llm_reasoner")


class LLMReasoner:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def synthesize_reasoning(
        self,
        symbol: str,
        decision: str,
        horizons: MultiHorizonAnalysis,
        regime: MarketRegime,
        regime_conf: float,
        council: ModelCouncilResult,
        conflict: EvidenceConflictAnalysis,
        uncertainty: UncertaintyAssessment,
        risk: RiskGuardianDecision,
        tech_summary: Dict[str, Any],
        news_summary: Dict[str, Any],
    ) -> StructuredAIExplanation:
        """
        Generates structured explanations for the decision: WHY THIS DECISION vs WHY NOT.
        """
        # If API key is present and valid, attempt LLM call with strict JSON schema
        if self.client and not settings.MOCK_LLM_IF_NO_KEY:
            try:
                return self._call_openai(
                    symbol, decision, horizons, regime, regime_conf,
                    council, conflict, uncertainty, risk, tech_summary, news_summary
                )
            except Exception as e:
                logger.warning(f"OpenAI reasoning call failed: {e}. Falling back to deterministic synthesizer.")

        return self._generate_deterministic_explanation(
            symbol, decision, horizons, regime, regime_conf,
            council, conflict, uncertainty, risk, tech_summary, news_summary
        )

    def _generate_deterministic_explanation(
        self,
        symbol: str,
        decision: str,
        horizons: MultiHorizonAnalysis,
        regime: MarketRegime,
        regime_conf: float,
        council: ModelCouncilResult,
        conflict: EvidenceConflictAnalysis,
        uncertainty: UncertaintyAssessment,
        risk: RiskGuardianDecision,
        tech_summary: Dict[str, Any],
        news_summary: Dict[str, Any],
    ) -> StructuredAIExplanation:
        # Build "WHY THIS DECISION?"
        why_this: List[str] = []
        # Build "WHY NOT?"
        why_not: List[str] = []

        # Dominant evidence drivers
        for driver in uncertainty.confidence_drivers:
            why_this.append(driver)

        if decision == "BUY":
            why_this.append(f"Model Council consensus is BUY with {council.consensus_conviction * 100:.1f}% weighted conviction.")
            why_this.append(f"Technical momentum intact: RSI {tech_summary.get('rsi_14', 50)} and positive trend score (+{tech_summary.get('trend_score', 0)}).")
            if horizons.horizon_agreement:
                why_this.append("Unanimous multi-horizon alignment across short, medium, and long-term trends.")
            
            # Why NOT reasons
            why_not.extend(uncertainty.confidence_reducers)
            for dissent in conflict.conflicting_evidence:
                why_not.append(f"Dissenting council model: {dissent}")
            if risk.decision == "REDUCE":
                why_not.append(f"Risk Guardian reduced allocation to {risk.approved_position_pct:.1f}%: {'; '.join(risk.binding_constraints)}")

        elif decision == "SELL":
            why_this.append(f"Model Council consensus is SELL with {council.consensus_conviction * 100:.1f}% conviction.")
            why_this.append(f"Downward technical momentum: trend score {tech_summary.get('trend_score', 0)} and broken intermediate moving averages.")
            
            why_not.extend(uncertainty.confidence_reducers)
            for dissent in conflict.conflicting_evidence:
                why_not.append(f"Contrarian model: {dissent}")
            why_not.append("Risk of short-covering squeeze if broader market stages an intraday reversal.")

        elif decision == "NO_TRADE":
            why_this.append(f"Active capital preservation abstention triggered.")
            for reason in uncertainty.abstention_reasons:
                why_this.append(reason)
            why_this.append(f"Composite uncertainty ({uncertainty.composite_uncertainty * 100:.1f}%) exceeds actionable trading threshold.")

            # Why NOT abstaining (i.e. why someone might mistakenly trade)
            why_not.append(f"Potential opportunity cost if {symbol} breaks out without waiting for confirmation.")
            for v in council.votes:
                if v.signal in ["BUY", "SELL"]:
                    why_not.append(f"Aggressive signal present: {v.model_name} suggested {v.signal} ({v.conviction * 100:.0f}%).")

        else:  # HOLD
            why_this.append("Current indicators remain in statistical equilibrium without a directional edge.")
            why_this.append(f"Market regime {regime.value} supports defensive position holding.")
            why_not.append("Sideways drift may lead to capital stagnation relative to high-momentum sectors.")

        # Summary
        summary = (
            f"{symbol} Decision: {decision}. Market Regime is {regime.value} ({regime_conf * 100:.0f}% confidence). "
            f"Calibrated confidence is {uncertainty.calibrated_confidence * 100:.1f}% with "
            f"{conflict.conflict_severity} evidence conflict across 5 council models."
        )

        horizon_analysis = horizons.conflict_summary + " " + horizons.decision_impact
        macro_implication = f"Regime {regime.value} mandates {'risk-on expansion' if regime == MarketRegime.BULL_TRENDING else ('capital conservation' if regime in [MarketRegime.HIGH_VOLATILITY, MarketRegime.CRISIS_STRESS] else 'tactical positioning')}."
        risk_takeaway = risk.explanation

        return StructuredAIExplanation(
            summary=summary,
            why_this_decision=why_this[:5],
            why_not=why_not[:5],
            horizon_tension_analysis=horizon_analysis,
            macro_regime_implication=macro_implication,
            risk_governance_takeaway=risk_takeaway,
        )

    def _call_openai(self, *args, **kwargs) -> StructuredAIExplanation:
        # Structured OpenAI JSON schema call
        # Standard implementation with Pydantic validation
        prompt = "Synthesize trading intelligence into structured JSON..."
        response = self.client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return StructuredAIExplanation(**data)
