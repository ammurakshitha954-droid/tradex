"""
Independent Risk Guardian Engine.
The AI proposes trades; Risk Guardian strictly controls execution.
Outputs: APPROVE, REDUCE, or REJECT with deterministic constraint attribution.
The AI/LLM cannot bypass or alter these rules.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from ..portfolio.analytics import PortfolioState


class RiskGuardianDecision(BaseModel):
    decision: str  # "APPROVE", "REDUCE", "REJECT"
    symbol: str
    proposed_action: str
    proposed_position_pct: float
    approved_position_pct: float
    binding_constraints: List[str]
    risk_score: float = Field(..., ge=0.0, le=100.0)  # 0 to 100, >70 is dangerous
    passed_all_checks: bool
    explanation: str


class RiskGuardian:
    # Hard risk constraints (can be configured via settings)
    MAX_SINGLE_POSITION_PCT = 10.0  # Max 10% in any single security
    MAX_SECTOR_EXPOSURE_PCT = 25.0  # Max 25% in any single industry sector
    MAX_PORTFOLIO_DRAWDOWN_CIRCUIT_BREAKER = -15.0  # Halt new buys if portfolio is in >15% drawdown
    MAX_PORTFOLIO_CVAR_PCT = 4.0  # Max daily 95% CVaR of 4.0%
    MAX_VOLATILITY_THRESHOLD = 50.0  # Annualized volatility ceiling

    @classmethod
    def evaluate_proposal(
        cls,
        symbol: str,
        proposed_action: str,
        proposed_size_pct: float,
        asset_sector: str,
        asset_volatility_pct: float,
        portfolio_state: PortfolioState,
        uncertainty_score: float = 0.20,
    ) -> RiskGuardianDecision:
        """
        Independent deterministic risk assessment of proposed trading action.
        """
        clean_sym = symbol.upper()

        # If proposal is NO_TRADE or HOLD, Risk Guardian trivially approves
        if proposed_action in ["NO_TRADE", "HOLD"]:
            return RiskGuardianDecision(
                decision="APPROVE",
                symbol=clean_sym,
                proposed_action=proposed_action,
                proposed_position_pct=0.0,
                approved_position_pct=0.0,
                binding_constraints=[],
                risk_score=15.0,
                passed_all_checks=True,
                explanation=f"Passive action '{proposed_action}' maintains existing risk profile.",
            )

        # For SELL proposals: approving risk de-risking
        if proposed_action == "SELL":
            return RiskGuardianDecision(
                decision="APPROVE",
                symbol=clean_sym,
                proposed_action="SELL",
                proposed_position_pct=proposed_size_pct,
                approved_position_pct=proposed_size_pct,
                binding_constraints=[],
                risk_score=20.0,
                passed_all_checks=True,
                explanation=f"SELL proposal on {clean_sym} reduces overall portfolio risk exposure.",
            )

        # BUY proposals require rigorous multi-constraint inspection
        binding_constraints: List[str] = []
        approved_size_pct = proposed_size_pct
        risk_penalties = 0.0

        # Check 1: Portfolio Drawdown Circuit Breaker
        if portfolio_state.current_drawdown_pct <= cls.MAX_PORTFOLIO_DRAWDOWN_CIRCUIT_BREAKER:
            binding_constraints.append(
                f"Portfolio drawdown ({portfolio_state.current_drawdown_pct:.1f}%) exceeds hard circuit breaker ({cls.MAX_PORTFOLIO_DRAWDOWN_CIRCUIT_BREAKER:.1f}%)."
            )
            return RiskGuardianDecision(
                decision="REJECT",
                symbol=clean_sym,
                proposed_action="BUY",
                proposed_position_pct=proposed_size_pct,
                approved_position_pct=0.0,
                binding_constraints=binding_constraints,
                risk_score=95.0,
                passed_all_checks=False,
                explanation="HARD REJECT: Portfolio-level drawdown limit breached. Capital allocation frozen.",
            )

        # Check 2: Single Position Sizing Limit
        existing_pos = next((p for p in portfolio_state.positions if p.symbol == clean_sym), None)
        existing_weight = existing_pos.weight_pct if existing_pos else 0.0
        post_trade_weight = existing_weight + proposed_size_pct

        if post_trade_weight > cls.MAX_SINGLE_POSITION_PCT:
            excess = post_trade_weight - cls.MAX_SINGLE_POSITION_PCT
            approved_size_pct = max(0.0, cls.MAX_SINGLE_POSITION_PCT - existing_weight)
            binding_constraints.append(
                f"Single position ceiling violated: Proposed total {post_trade_weight:.1f}% exceeds max {cls.MAX_SINGLE_POSITION_PCT:.1f}%."
            )
            risk_penalties += 25.0

        # Check 3: Sector Concentration Limit
        current_sector_exp = portfolio_state.sector_exposures.get(asset_sector, 0.0)
        post_trade_sector = current_sector_exp + approved_size_pct
        if post_trade_sector > cls.MAX_SECTOR_EXPOSURE_PCT:
            allowed_sector_room = max(0.0, cls.MAX_SECTOR_EXPOSURE_PCT - current_sector_exp)
            if allowed_sector_room < approved_size_pct:
                approved_size_pct = allowed_sector_room
                binding_constraints.append(
                    f"Sector concentration limit reached: {asset_sector} would reach {post_trade_sector:.1f}% (cap: {cls.MAX_SECTOR_EXPOSURE_PCT:.1f}%)."
                )
                risk_penalties += 30.0

        # Check 4: Asset Volatility Ceiling
        if asset_volatility_pct > cls.MAX_VOLATILITY_THRESHOLD:
            binding_constraints.append(
                f"Asset annualized volatility ({asset_volatility_pct:.1f}%) exceeds safety ceiling ({cls.MAX_VOLATILITY_THRESHOLD:.1f}%)."
            )
            risk_penalties += 40.0
            # Scale down position inversely to excess volatility
            vol_scale = cls.MAX_VOLATILITY_THRESHOLD / asset_volatility_pct
            approved_size_pct *= vol_scale

        # Check 5: Uncertainty Scaling
        if uncertainty_score > 0.40:
            scale = 1.0 - (uncertainty_score - 0.40) * 1.5
            scale = max(0.20, scale)
            approved_size_pct *= scale
            binding_constraints.append(
                f"Elevated model/evidence uncertainty ({uncertainty_score * 100:.1f}%) triggered sizing haircut ({scale * 100:.0f}% factor)."
            )
            risk_penalties += 15.0

        # Final Decision Synthesis
        risk_score = min(100.0, 20.0 + risk_penalties)
        approved_size_pct = round(max(0.0, approved_size_pct), 2)

        if approved_size_pct <= 0.5:
            decision = "REJECT"
            explanation = f"REJECTED: Proposed BUY violated risk boundaries: {'; '.join(binding_constraints)}."
        elif approved_size_pct < proposed_size_pct:
            decision = "REDUCE"
            explanation = f"REDUCED: Position size scaled down from {proposed_size_pct:.1f}% to {approved_size_pct:.1f}% due to: {'; '.join(binding_constraints)}."
        else:
            decision = "APPROVE"
            explanation = f"APPROVED: Proposal of {proposed_size_pct:.1f}% satisfies all portfolio risk and concentration constraints."

        return RiskGuardianDecision(
            decision=decision,
            symbol=clean_sym,
            proposed_action="BUY",
            proposed_position_pct=proposed_size_pct,
            approved_position_pct=approved_size_pct,
            binding_constraints=binding_constraints,
            risk_score=round(risk_score, 1),
            passed_all_checks=(len(binding_constraints) == 0),
            explanation=explanation,
        )
