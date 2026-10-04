"""
Decisions API routes: End-to-end AI Decision Engine, latest decision card, debate view, and history.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from fastapi import APIRouter, Query, Body, HTTPException
from ...data.providers.mock_provider import MockDataProvider
from ...data.providers.yfinance_provider import YFinanceProvider
from ...features.technical import TechnicalIndicators
from ...features.volatility import VolatilityIndicators
from ...features.volume import VolumeIndicators
from ...regime.detector import MarketRegimeDetector
from ...reasoning.horizons import MultiHorizonEngine
from ...news.pipeline import NewsIntelligencePipeline
from ...models.council import ModelCouncil
from ...uncertainty.conflict_engine import EvidenceConflictEngine
from ...uncertainty.abstention import UncertaintyEngine
from ...portfolio.analytics import PortfolioAnalytics
from ...risk.guardian import RiskGuardian
from ...reasoning.counterfactual import CounterfactualEngine
from ...reasoning.llm_reasoner import LLMReasoner
from ...reasoning.schemas import DecisionRecord
from ...memory.decision_memory import decision_memory_engine
from .portfolio import DEFAULT_PORTFOLIO_CASH, DEFAULT_HOLDINGS

router = APIRouter(prefix="/decisions", tags=["AI Decisions & Debate"])
mock_provider = MockDataProvider()
yf_provider = YFinanceProvider(fallback_provider=mock_provider)
model_council = ModelCouncil()
llm_reasoner = LLMReasoner()

# In-memory cache of generated decisions for fast retrieval and replay
DECISION_CACHE: Dict[str, DecisionRecord] = {}


class AnalyzeRequest(BaseModel):
    symbol: str = "NVDA"
    lookback_days: int = 250
    proposed_position_pct: float = 5.0


def _run_full_decision_flow(symbol: str, lookback_days: int = 250, proposed_size_pct: float = 5.0) -> DecisionRecord:
    clean_sym = symbol.upper()
    now = datetime.now()
    start = now - timedelta(days=lookback_days)

    # 1. Market Data
    df = yf_provider.get_historical_ohlcv(clean_sym, start, now)
    if df.empty or len(df) < 30:
        raise HTTPException(status_code=400, detail=f"Insufficient market data for {clean_sym}")

    metadata = yf_provider.get_asset_metadata(clean_sym)
    fundamentals = yf_provider.get_fundamentals(clean_sym)

    # 2. Features
    tech_df = TechnicalIndicators.compute_all_indicators(df)
    vol_df = VolatilityIndicators.compute_volatility(tech_df)
    full_df = VolumeIndicators.compute_volume_metrics(vol_df).bfill().ffill()

    tech_summary = TechnicalIndicators.get_latest_signal_summary(full_df)
    vol_summary = VolatilityIndicators.get_latest_volatility_summary(full_df)
    vol_metrics = VolumeIndicators.get_latest_volume_summary(full_df)

    # 3. Market Regime
    regime_res = MarketRegimeDetector.detect_regime_from_series(df, clean_sym)

    # 4. News Intelligence
    raw_news = yf_provider.get_news(clean_sym, limit=10)
    news_summary = NewsIntelligencePipeline.process_news(raw_news, clean_sym)

    # 5. Multi-Horizon Reasoning
    horizons = MultiHorizonEngine.analyze(
        symbol=clean_sym,
        tech_summary=tech_summary,
        vol_summary=vol_summary,
        vol_metrics=vol_metrics,
        regime=regime_res.current_regime,
        fundamentals=fundamentals,
        sentiment_score=news_summary.aggregate_sentiment,
    )

    # 6. Model Council & Conflict
    council_res = model_council.evaluate_council(
        symbol=clean_sym,
        features_df=full_df,
        regime=regime_res.current_regime,
        news_sentiment=news_summary.aggregate_sentiment,
        news_materiality=news_summary.aggregate_materiality,
    )
    conflict_res = EvidenceConflictEngine.analyze_conflict(council_res, clean_sym)

    # 7. Uncertainty & Abstention
    uncertainty_res = UncertaintyEngine.evaluate(
        symbol=clean_sym,
        council_result=council_res,
        conflict_analysis=conflict_res,
        regime=regime_res.current_regime,
        regime_confidence=regime_res.regime_confidence,
        vol_summary=vol_summary,
        news_sentiment=news_summary.aggregate_sentiment,
        news_materiality=news_summary.aggregate_materiality,
    )

    # 8. Portfolio & Risk Guardian
    portfolio_state = PortfolioAnalytics.analyze_portfolio(
        cash=DEFAULT_PORTFOLIO_CASH,
        holdings=DEFAULT_HOLDINGS,
    )
    risk_res = RiskGuardian.evaluate_proposal(
        symbol=clean_sym,
        proposed_action=uncertainty_res.recommended_action,
        proposed_size_pct=proposed_size_pct,
        asset_sector=metadata.sector,
        asset_volatility_pct=vol_summary.get("hist_vol_20d_pct", 22.0),
        portfolio_state=portfolio_state,
        uncertainty_score=uncertainty_res.composite_uncertainty,
    )

    # 9. Counterfactual Engine
    current_price = tech_summary.get("close", float(df["close"].iloc[-1]))
    ema_200 = float(full_df["ema_200"].iloc[-1]) if "ema_200" in full_df else current_price
    atr_14 = float(tech_summary.get("atr_14", current_price * 0.02))

    counterfactuals = CounterfactualEngine.generate_scenarios(
        symbol=clean_sym,
        current_price=current_price,
        decision=uncertainty_res.recommended_action,
        annualized_vol_pct=vol_summary.get("hist_vol_20d_pct", 22.0),
        atr_14=atr_14,
        ema_200=ema_200,
        position_size_pct=risk_res.approved_position_pct,
    )

    # 10. AI Reasoner (WHY THIS vs WHY NOT)
    explanation = llm_reasoner.synthesize_reasoning(
        symbol=clean_sym,
        decision=uncertainty_res.recommended_action,
        horizons=horizons,
        regime=regime_res.current_regime,
        regime_conf=regime_res.regime_confidence,
        council=council_res,
        conflict=conflict_res,
        uncertainty=uncertainty_res,
        risk=risk_res,
        tech_summary=tech_summary,
        news_summary={"sentiment": news_summary.aggregate_sentiment},
    )

    # Final decision assembly
    now_utc = datetime.now(timezone.utc)
    dec_id = f"dec-{clean_sym}-{int(now_utc.timestamp())}"
    rec = DecisionRecord(
        id=dec_id,
        symbol=clean_sym,
        timestamp=now_utc.isoformat(),
        final_decision=uncertainty_res.recommended_action,
        calibrated_confidence=uncertainty_res.calibrated_confidence,
        composite_uncertainty=uncertainty_res.composite_uncertainty,
        approved_position_pct=risk_res.approved_position_pct,
        current_price=current_price,
        expected_return_pct=counterfactuals.base_case.expected_return_pct,
        expected_risk_pct=round(vol_summary.get("hist_vol_20d_pct", 22.0) / (252**0.5) * 1.645, 2),
        market_regime=regime_res.current_regime,
        regime_confidence=regime_res.regime_confidence,
        horizons=horizons,
        uncertainty=uncertainty_res,
        conflict=conflict_res,
        risk_guardian=risk_res,
        counterfactuals=counterfactuals,
        council=council_res,
        explanation=explanation,
    )

    DECISION_CACHE[clean_sym] = rec

    # Log to memory engine
    decision_memory_engine.store_decision(
        decision_id=dec_id,
        symbol=clean_sym,
        decision=rec.final_decision,
        confidence=rec.calibrated_confidence,
        uncertainty=rec.composite_uncertainty,
        regime=rec.market_regime,
        dominant_evidence=conflict_res.dominant_evidence,
        risk_status=risk_res.decision,
        approved_size_pct=risk_res.approved_position_pct,
    )

    return rec


@router.get("/latest")
def get_latest_decision(symbol: str = Query(default="NVDA")) -> Dict[str, Any]:
    clean_sym = symbol.upper()
    if clean_sym in DECISION_CACHE:
        return DECISION_CACHE[clean_sym].model_dump()
    # Generate on demand
    rec = _run_full_decision_flow(clean_sym)
    return rec.model_dump()


@router.post("/analyze")
def generate_decision_analysis(request: AnalyzeRequest) -> Dict[str, Any]:
    rec = _run_full_decision_flow(
        symbol=request.symbol,
        lookback_days=request.lookback_days,
        proposed_size_pct=request.proposed_position_pct
    )
    return rec.model_dump()


@router.get("/debate")
def get_ai_debate_view(symbol: str = Query(default="NVDA")) -> Dict[str, Any]:
    """Exposes explainable multi-model debate view comparing technical, ML, regime, news, and risk models."""
    clean_sym = symbol.upper()
    dec = DECISION_CACHE.get(clean_sym) or _run_full_decision_flow(clean_sym)
    return {
        "symbol": clean_sym,
        "final_consensus": dec.final_decision,
        "council_votes": [v.model_dump() for v in dec.council.votes],
        "conflict_severity": dec.conflict.conflict_severity,
        "disagreement_score": dec.conflict.disagreement_score,
        "conflict_pairs": [p.model_dump() for p in dec.conflict.conflict_pairs],
        "dominant_evidence": dec.conflict.dominant_evidence,
        "conflicting_evidence": dec.conflict.conflicting_evidence,
    }
