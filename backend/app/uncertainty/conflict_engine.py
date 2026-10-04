"""
Evidence Conflict & Model Disagreement Engine.
Measures pairwise divergence across heterogeneous models, computes entropy of council votes,
and generates explainable conflict matrices.
"""
from typing import Dict, Any, List, Tuple
from pydantic import BaseModel, Field
import numpy as np
from ..models.council import ModelCouncilResult, ModelVote


class ConflictPair(BaseModel):
    source_a: str
    signal_a: str
    source_b: str
    signal_b: str
    severity: str  # "NONE", "MILD", "STRONG"
    description: str


class EvidenceConflictAnalysis(BaseModel):
    symbol: str
    agreement_score: float = Field(..., ge=0.0, le=1.0)
    disagreement_score: float = Field(..., ge=0.0, le=1.0)
    conflict_severity: str  # "LOW", "MILD", "HIGH", "EXTREME"
    dominant_evidence: str
    conflicting_evidence: List[str]
    conflict_pairs: List[ConflictPair]
    entropy_score: float  # Information entropy of votes
    uncertainty_penalty: float = Field(..., ge=0.0, le=1.0)
    conflict_explanation: str


class EvidenceConflictEngine:
    OPPOSING_MAP = {
        ("BUY", "SELL"): "STRONG",
        ("SELL", "BUY"): "STRONG",
        ("BUY", "HOLD"): "MILD",
        ("HOLD", "BUY"): "MILD",
        ("SELL", "HOLD"): "MILD",
        ("HOLD", "SELL"): "MILD",
        ("BUY", "BUY"): "NONE",
        ("SELL", "SELL"): "NONE",
        ("HOLD", "HOLD"): "NONE",
        ("NO_TRADE", "BUY"): "STRONG",
        ("NO_TRADE", "SELL"): "STRONG",
        ("NO_TRADE", "HOLD"): "MILD",
    }

    @classmethod
    def analyze_conflict(
        cls,
        council_result: ModelCouncilResult,
        symbol: str
    ) -> EvidenceConflictAnalysis:
        votes = council_result.votes
        n_votes = len(votes)
        if n_votes <= 1:
            return cls._trivial_result(symbol)

        # 1. Pairwise Conflict Evaluation
        conflict_pairs: List[ConflictPair] = []
        strong_conflict_count = 0
        mild_conflict_count = 0

        for i in range(n_votes):
            for j in range(i + 1, n_votes):
                v_a = votes[i]
                v_b = votes[j]
                sev = cls.OPPOSING_MAP.get((v_a.signal, v_b.signal), "MILD")
                
                if sev == "STRONG":
                    strong_conflict_count += 1
                    desc = f"{v_a.model_name} ({v_a.signal}) directly opposes {v_b.model_name} ({v_b.signal})."
                elif sev == "MILD":
                    mild_conflict_count += 1
                    desc = f"{v_a.model_name} ({v_a.signal}) exhibits mild tension with {v_b.model_name} ({v_b.signal})."
                else:
                    desc = f"{v_a.model_name} and {v_b.model_name} agree on {v_a.signal}."

                conflict_pairs.append(
                    ConflictPair(
                        source_a=v_a.model_name,
                        signal_a=v_a.signal,
                        source_b=v_b.model_name,
                        signal_b=v_b.signal,
                        severity=sev,
                        description=desc,
                    )
                )

        total_pairs = len(conflict_pairs)
        # Disagreement score: weighted ratio of conflicts
        disagreement_score = (strong_conflict_count * 1.0 + mild_conflict_count * 0.4) / max(1, total_pairs)
        disagreement_score = float(np.clip(disagreement_score, 0.0, 1.0))
        agreement_score = 1.0 - disagreement_score

        # 2. Vote Entropy Calculation
        distribution = council_result.vote_distribution
        probs = np.array([count / n_votes for count in distribution.values() if count > 0])
        # Normalized entropy (0 = perfect unanimous agreement, 1 = maximum dispersion)
        entropy = -np.sum(probs * np.log2(probs)) if len(probs) > 1 else 0.0
        max_possible_entropy = np.log2(len(distribution)) if len(distribution) > 1 else 1.0
        normalized_entropy = float(entropy / max_possible_entropy) if max_possible_entropy > 0 else 0.0

        # Conflict Severity Categorization
        if disagreement_score < 0.20:
            severity = "LOW"
            uncertainty_penalty = 0.05
        elif disagreement_score < 0.45:
            severity = "MILD"
            uncertainty_penalty = 0.20
        elif disagreement_score < 0.70:
            severity = "HIGH"
            uncertainty_penalty = 0.45
        else:
            severity = "EXTREME"
            uncertainty_penalty = 0.70

        # Identify dominant and conflicting evidence
        consensus = council_result.consensus_signal
        dominant_models = [v.model_name for v in votes if v.signal == consensus]
        conflicting_models = [f"{v.model_name} ({v.signal})" for v in votes if v.signal != consensus]

        dominant_evidence = f"Consensus {consensus} supported by {', '.join(dominant_models)}."
        
        if strong_conflict_count > 0:
            conflict_explanation = (
                f"Significant model divergence detected ({strong_conflict_count} direct oppositions). "
                f"Consensus is {consensus}, but opposing models ({', '.join(conflicting_models)}) "
                f"substantially degrade conviction and demand risk reduction or abstention."
            )
        elif mild_conflict_count > 0:
            conflict_explanation = (
                f"Moderate model consensus on {consensus}. Dissenting models exhibit caution "
                f"without outright contradiction."
            )
        else:
            conflict_explanation = f"Unanimous council alignment across all models on {consensus}."

        return EvidenceConflictAnalysis(
            symbol=symbol.upper(),
            agreement_score=round(agreement_score, 3),
            disagreement_score=round(disagreement_score, 3),
            conflict_severity=severity,
            dominant_evidence=dominant_evidence,
            conflicting_evidence=conflicting_models,
            conflict_pairs=conflict_pairs,
            entropy_score=round(normalized_entropy, 3),
            uncertainty_penalty=round(uncertainty_penalty, 3),
            conflict_explanation=conflict_explanation,
        )

    @classmethod
    def _trivial_result(cls, symbol: str) -> EvidenceConflictAnalysis:
        return EvidenceConflictAnalysis(
            symbol=symbol.upper(),
            agreement_score=1.0,
            disagreement_score=0.0,
            conflict_severity="LOW",
            dominant_evidence="Single model active",
            conflicting_evidence=[],
            conflict_pairs=[],
            entropy_score=0.0,
            uncertainty_penalty=0.0,
            conflict_explanation="Single model evaluation; no disagreement.",
        )
