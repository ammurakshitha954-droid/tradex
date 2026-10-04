"""
Unified Decision Record Schemas.
Combines Quantitative, Regime, News, Uncertainty, Risk Guardian, and Counterfactual analysis
into a fully traceable, explainable schema.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from ..regime.types import MarketRegime
from ..reasoning.horizons import MultiHorizonAnalysis
from ..uncertainty.abstention import UncertaintyAssessment
from ..uncertainty.conflict_engine import EvidenceConflictAnalysis
from ..risk.guardian import RiskGuardianDecision
from ..reasoning.counterfactual import CounterfactualAnalysis
from ..models.council import ModelCouncilResult


class StructuredAIExplanation(BaseModel):
    summary: str
    why_this_decision: List[str]  # Dominant supporting evidence
    why_not: List[str]  # Downside risks, opposing evidence, why abstention was considered
    horizon_tension_analysis: str
    macro_regime_implication: str
    risk_governance_takeaway: str


class DecisionRecord(BaseModel):
    id: str
    symbol: str
    timestamp: str
    final_decision: str  # "BUY", "SELL", "HOLD", "NO_TRADE"
    calibrated_confidence: float = Field(..., ge=0.0, le=1.0)
    composite_uncertainty: float = Field(..., ge=0.0, le=1.0)
    approved_position_pct: float
    current_price: float
    expected_return_pct: float
    expected_risk_pct: float
    market_regime: MarketRegime
    regime_confidence: float

    # Core Reasoning Modules
    horizons: MultiHorizonAnalysis
    uncertainty: UncertaintyAssessment
    conflict: EvidenceConflictAnalysis
    risk_guardian: RiskGuardianDecision
    counterfactuals: CounterfactualAnalysis
    council: ModelCouncilResult
    explanation: StructuredAIExplanation

    # Provenance
    model_version: str = "v1.4-adaptive"
    execution_simulated: bool = False
