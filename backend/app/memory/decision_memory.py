"""
Contextual Decision Memory & Self-Correction Engine.
Separates Decision Quality from Outcome Luck, attributes errors, and maintains validated memory records.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from ..regime.types import MarketRegime


class MemoryRecord(BaseModel):
    id: str
    symbol: str
    timestamp: str
    decision: str
    confidence: float
    uncertainty: float
    regime: MarketRegime
    dominant_evidence: str
    risk_status: str
    approved_size_pct: float

    # Outcome evaluation (populated when evaluated after forward window)
    realized_return_pct: Optional[float] = None
    realized_drawdown_pct: Optional[float] = None
    decision_quality_label: str  # "GOOD_DECISION_GOOD_OUTCOME", "GOOD_DECISION_BAD_OUTCOME", "BAD_DECISION_GOOD_OUTCOME", "BAD_DECISION_BAD_OUTCOME", "PENDING"
    error_attribution: Optional[str] = None  # "DATA_ERROR", "REASONING_ERROR", "REGIME_ERROR", "EXECUTION_ERROR", "RISK_ERROR", "UNEXPECTED_EVENT", "NONE"
    validated_lesson: Optional[str] = None
    validation_status: str = "PENDING"  # "OBSERVED", "INFERRED", "VALIDATED_LEARNING"


class DecisionMemoryEngine:
    def __init__(self):
        self._memory_store: List[MemoryRecord] = []
        self._populate_seed_memories()

    def store_decision(
        self,
        decision_id: str,
        symbol: str,
        decision: str,
        confidence: float,
        uncertainty: float,
        regime: MarketRegime,
        dominant_evidence: str,
        risk_status: str,
        approved_size_pct: float,
        timestamp: Optional[str] = None,
    ) -> MemoryRecord:
        record = MemoryRecord(
            id=decision_id,
            symbol=symbol.upper(),
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
            decision=decision,
            confidence=round(confidence, 3),
            uncertainty=round(uncertainty, 3),
            regime=regime,
            dominant_evidence=dominant_evidence,
            risk_status=risk_status,
            approved_size_pct=approved_size_pct,
            realized_return_pct=None,
            realized_drawdown_pct=None,
            decision_quality_label="PENDING",
            error_attribution=None,
            validated_lesson=None,
            validation_status="OBSERVED",
        )
        self._memory_store.append(record)
        return record

    def evaluate_outcome(
        self,
        memory_id: str,
        realized_return_pct: float,
        realized_drawdown_pct: float,
    ) -> Optional[MemoryRecord]:
        rec = next((r for r in self._memory_store if r.id == memory_id), None)
        if not rec:
            return None

        rec.realized_return_pct = round(realized_return_pct, 2)
        rec.realized_drawdown_pct = round(realized_drawdown_pct, 2)

        is_good_decision = (rec.confidence >= 0.55 and rec.uncertainty <= 0.45 and rec.risk_status == "APPROVE")
        is_good_outcome = (realized_return_pct > 0.0) if rec.decision == "BUY" else (
            (realized_return_pct < 0.0) if rec.decision == "SELL" else (abs(realized_return_pct) < 3.0)
        )

        if is_good_decision and is_good_outcome:
            quality = "GOOD_DECISION_GOOD_OUTCOME"
            error = "NONE"
            lesson = f"Multi-factor conviction in {rec.regime.value} regime confirmed with favorable risk-adjusted outcome."
            val_status = "VALIDATED_LEARNING"
        elif is_good_decision and not is_good_outcome:
            quality = "GOOD_DECISION_BAD_OUTCOME"
            error = "UNEXPECTED_EVENT"
            lesson = "Valid trade process executed within risk limits; loss driven by exogenous market variance. Do not overfit parameters."
            val_status = "VALIDATED_LEARNING"
        elif not is_good_decision and is_good_outcome:
            quality = "BAD_DECISION_GOOD_OUTCOME"
            error = "REASONING_ERROR"
            lesson = "Profitable outcome resulted from outcome luck despite high uncertainty/conflict. Do not reinforce trade pattern."
            val_status = "VALIDATED_LEARNING"
        else:
            quality = "BAD_DECISION_BAD_OUTCOME"
            error = "REGIME_ERROR" if rec.regime in [MarketRegime.CRISIS_STRESS, MarketRegime.HIGH_VOLATILITY] else "RISK_ERROR"
            lesson = f"Flawed trade initiation during elevated conflict/uncertainty. Enforce tighter abstention in {rec.regime.value} regimes."
            val_status = "VALIDATED_LEARNING"

        rec.decision_quality_label = quality
        rec.error_attribution = error
        rec.validated_lesson = lesson
        rec.validation_status = val_status
        return rec

    def get_memories_for_symbol(self, symbol: str) -> List[MemoryRecord]:
        return [r for r in self._memory_store if r.symbol == symbol.upper()]

    def get_all_memories(self) -> List[MemoryRecord]:
        return self._memory_store

    def _populate_seed_memories(self):
        """Pre-seeds realistic historical decisions to showcase Decision Replay and Self-Correction UX."""
        seeds = [
            MemoryRecord(
                id="mem-hist-001",
                symbol="NVDA",
                timestamp="2026-06-15T14:30:00Z",
                decision="BUY",
                confidence=0.82,
                uncertainty=0.18,
                regime=MarketRegime.BULL_TRENDING,
                dominant_evidence="Breakout above 50 EMA with positive earnings surprise catalyst.",
                risk_status="APPROVE",
                approved_size_pct=7.5,
                realized_return_pct=14.2,
                realized_drawdown_pct=-2.1,
                decision_quality_label="GOOD_DECISION_GOOD_OUTCOME",
                error_attribution="NONE",
                validated_lesson="Trend continuation with expanding volume in BULL_TRENDING regime provides high statistical reliability.",
                validation_status="VALIDATED_LEARNING",
            ),
            MemoryRecord(
                id="mem-hist-002",
                symbol="AAPL",
                timestamp="2026-07-22T10:15:00Z",
                decision="BUY",
                confidence=0.68,
                uncertainty=0.34,
                regime=MarketRegime.HIGH_VOLATILITY,
                dominant_evidence="Short-term oversold technical bounce signal.",
                risk_status="REDUCE",
                approved_size_pct=3.0,
                realized_return_pct=-4.8,
                realized_drawdown_pct=-6.2,
                decision_quality_label="GOOD_DECISION_BAD_OUTCOME",
                error_attribution="UNEXPECTED_EVENT",
                validated_lesson="Risk Guardian reduction from 6% to 3% successfully limited portfolio drawdown during macro interest rate announcement.",
                validation_status="VALIDATED_LEARNING",
            ),
            MemoryRecord(
                id="mem-hist-003",
                symbol="MSFT",
                timestamp="2026-08-10T11:00:00Z",
                decision="NO_TRADE",
                confidence=0.48,
                uncertainty=0.58,
                regime=MarketRegime.TRANSITION_UNCERTAIN,
                dominant_evidence="Abstention triggered: Technical BUY vs Regulatory investigation headline SELL.",
                risk_status="APPROVE",
                approved_size_pct=0.0,
                realized_return_pct=-8.5,
                realized_drawdown_pct=-9.1,
                decision_quality_label="GOOD_DECISION_GOOD_OUTCOME",
                error_attribution="NONE",
                validated_lesson="Abstention engine prevented severe portfolio loss during impending antitrust litigation disclosure.",
                validation_status="VALIDATED_LEARNING",
            ),
            MemoryRecord(
                id="mem-hist-004",
                symbol="SPY",
                timestamp="2026-09-02T09:45:00Z",
                decision="SELL",
                confidence=0.74,
                uncertainty=0.25,
                regime=MarketRegime.BEAR_TRENDING,
                dominant_evidence="Breakdown below 200 EMA with expanding downside volatility.",
                risk_status="APPROVE",
                approved_size_pct=5.0,
                realized_return_pct=-5.4,
                realized_drawdown_pct=-6.8,
                decision_quality_label="GOOD_DECISION_GOOD_OUTCOME",
                error_attribution="NONE",
                validated_lesson="De-risking and short hedge protected total portfolio capital during broad market correction.",
                validation_status="VALIDATED_LEARNING",
            ),
        ]
        self._memory_store.extend(seeds)


# Global memory engine singleton
decision_memory_engine = DecisionMemoryEngine()
