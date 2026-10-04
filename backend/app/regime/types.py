"""
Market Regime Type Definitions and Pydantic Schemas.
"""
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class MarketRegime(str, Enum):
    BULL_TRENDING = "BULL_TRENDING"
    BEAR_TRENDING = "BEAR_TRENDING"
    SIDEWAYS_RANGING = "SIDEWAYS_RANGING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY_COMPRESSION = "LOW_VOLATILITY_COMPRESSION"
    CRISIS_STRESS = "CRISIS_STRESS"
    TRANSITION_UNCERTAIN = "TRANSITION_UNCERTAIN"


class RegimeTimelinePoint(BaseModel):
    timestamp: str
    regime: MarketRegime
    confidence: float
    volatility_annualized: float
    close_price: float


class RegimeDetectionResult(BaseModel):
    symbol: str
    current_regime: MarketRegime
    regime_confidence: float = Field(..., ge=0.0, le=1.0)
    regime_probabilities: Dict[str, float]
    duration_days: int
    stability_score: float = Field(..., ge=0.0, le=1.0)  # Low stability = high transition likelihood
    key_drivers: List[str]
    timeline: List[RegimeTimelinePoint]
    timestamp: str
