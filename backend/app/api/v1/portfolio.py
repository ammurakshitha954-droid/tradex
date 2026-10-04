"""
Portfolio Intelligence & Risk Guardian API endpoints.
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Query, Body
from ...portfolio.analytics import PortfolioAnalytics, PortfolioState
from ...risk.guardian import RiskGuardian, RiskGuardianDecision
from ...data.providers.mock_provider import MockDataProvider

router = APIRouter(prefix="/portfolio", tags=["Portfolio Intelligence"])

# In-memory realistic initial portfolio
DEFAULT_PORTFOLIO_CASH = 42500.0
DEFAULT_HOLDINGS = {
    "AAPL": {"shares": 45, "price": 224.50, "sector": "Technology", "cost_basis": 210.0},
    "MSFT": {"shares": 30, "price": 448.20, "sector": "Technology", "cost_basis": 415.0},
    "NVDA": {"shares": 60, "price": 128.80, "sector": "Technology", "cost_basis": 115.0},
    "JPM": {"shares": 50, "price": 212.00, "sector": "Financial", "cost_basis": 195.0},
    "SPY": {"shares": 40, "price": 556.00, "sector": "Broad Market", "cost_basis": 530.0},
}


class RiskProposalRequest(BaseModel):
    symbol: str
    action: str  # "BUY", "SELL", "HOLD", "NO_TRADE"
    proposed_position_pct: float
    asset_sector: str = "Technology"
    asset_volatility_pct: float = 24.0
    uncertainty_score: float = 0.25


@router.get("")
def get_portfolio_overview() -> Dict[str, Any]:
    state = PortfolioAnalytics.analyze_portfolio(
        cash=DEFAULT_PORTFOLIO_CASH,
        holdings=DEFAULT_HOLDINGS,
    )
    return state.model_dump()


@router.post("/risk-check")
def evaluate_risk_guardian(request: RiskProposalRequest) -> Dict[str, Any]:
    state = PortfolioAnalytics.analyze_portfolio(
        cash=DEFAULT_PORTFOLIO_CASH,
        holdings=DEFAULT_HOLDINGS,
    )
    decision = RiskGuardian.evaluate_proposal(
        symbol=request.symbol,
        proposed_action=request.action,
        proposed_size_pct=request.proposed_position_pct,
        asset_sector=request.asset_sector,
        asset_volatility_pct=request.asset_volatility_pct,
        portfolio_state=state,
        uncertainty_score=request.uncertainty_score,
    )
    return decision.model_dump()
