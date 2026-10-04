"""
Contextual Memory & Decision Replay API endpoints.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query
from ...memory.decision_memory import decision_memory_engine, MemoryRecord

router = APIRouter(prefix="/memory", tags=["Contextual Memory & Replay"])


class OutcomeEvaluationRequest(BaseModel):
    memory_id: str
    realized_return_pct: float
    realized_drawdown_pct: float


@router.get("")
def list_memories(symbol: Optional[str] = Query(default=None)) -> List[Dict[str, Any]]:
    if symbol:
        records = decision_memory_engine.get_memories_for_symbol(symbol)
    else:
        records = decision_memory_engine.get_all_memories()
    return [r.model_dump() for r in records]


@router.get("/replay/{memory_id}")
def get_decision_replay(memory_id: str) -> Dict[str, Any]:
    """
    Returns structured Decision Replay breakdown:
    1. WHAT AI KNEW THEN
    2. WHAT AI DECIDED
    3. WHY
    4. WHAT HAPPENED
    5. WAS THE DECISION GOOD? (Process vs Luck)
    6. WHAT DID AI LEARN?
    """
    all_mem = decision_memory_engine.get_all_memories()
    rec = next((r for r in all_mem if r.id == memory_id), None)
    if not rec:
        raise HTTPException(status_code=404, detail="Memory record not found")

    is_good = "GOOD" in rec.decision_quality_label
    return {
        "memory_id": rec.id,
        "symbol": rec.symbol,
        "decision_timestamp": rec.timestamp,
        "what_ai_knew_then": {
            "market_regime": rec.regime.value,
            "calibrated_confidence": rec.confidence,
            "composite_uncertainty": rec.uncertainty,
            "dominant_evidence": rec.dominant_evidence,
            "risk_guardian_evaluation": rec.risk_status,
            "approved_allocation_pct": rec.approved_size_pct,
        },
        "what_ai_decided": rec.decision,
        "why": f"Action {rec.decision} authorized based on: {rec.dominant_evidence}. Risk Guardian status: {rec.risk_status}.",
        "what_happened": {
            "subsequent_return_pct": rec.realized_return_pct if rec.realized_return_pct is not None else "Pending observation",
            "subsequent_drawdown_pct": rec.realized_drawdown_pct if rec.realized_drawdown_pct is not None else "Pending observation",
        },
        "was_the_decision_good": {
            "classification": rec.decision_quality_label,
            "process_vs_luck_analysis": (
                "High-integrity process confirmed; sound multi-factor consensus aligned with disciplined risk control."
                if is_good else
                "Flawed execution or uncalibrated risk; outcome diverged due to elevated conflict or regime headwind."
            ),
        },
        "what_did_ai_learn": {
            "error_attribution": rec.error_attribution or "NONE",
            "validated_lesson": rec.validated_lesson or "Observation phase active.",
            "validation_status": rec.validation_status,
        },
    }


@router.post("/evaluate")
def evaluate_memory_outcome(request: OutcomeEvaluationRequest) -> Dict[str, Any]:
    updated = decision_memory_engine.evaluate_outcome(
        memory_id=request.memory_id,
        realized_return_pct=request.realized_return_pct,
        realized_drawdown_pct=request.realized_drawdown_pct,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Memory record not found")
    return updated.model_dump()
