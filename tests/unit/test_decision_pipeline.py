"""
Unit tests for the integrated Decision Pipeline:
Data -> Features -> Regime -> Horizons -> News -> Council -> Conflict -> Uncertainty/Abstention -> Risk Guardian -> Counterfactual -> LLM Reasoner.
"""
from datetime import datetime, timedelta
import pytest
from backend.app.data.providers.mock_provider import MockDataProvider
from backend.app.features.technical import TechnicalIndicators
from backend.app.features.volatility import VolatilityIndicators
from backend.app.features.volume import VolumeIndicators
from backend.app.regime.detector import MarketRegimeDetector
from backend.app.reasoning.horizons import MultiHorizonEngine
from backend.app.news.pipeline import NewsIntelligencePipeline
from backend.app.models.council import ModelCouncil
from backend.app.uncertainty.conflict_engine import EvidenceConflictEngine
from backend.app.uncertainty.abstention import UncertaintyEngine
from backend.app.portfolio.analytics import PortfolioAnalytics
from backend.app.risk.guardian import RiskGuardian
from backend.app.reasoning.counterfactual import CounterfactualEngine
from backend.app.reasoning.llm_reasoner import LLMReasoner


def test_full_decision_flow():
    symbol = "NVDA"
    provider = MockDataProvider(seed=42)
    now = datetime.now()
    df = provider.get_historical_ohlcv(symbol, now - timedelta(days=200), now)
    
    # 1. Features
    tech_df = TechnicalIndicators.compute_all_indicators(df)
    vol_df = VolatilityIndicators.compute_volatility(tech_df)
    vol_metrics_df = VolumeIndicators.compute_volume_metrics(vol_df)
    
    tech_summary = TechnicalIndicators.get_latest_signal_summary(tech_df)
    vol_summary = VolatilityIndicators.get_latest_volatility_summary(vol_df)
    vol_metrics = VolumeIndicators.get_latest_volume_summary(vol_metrics_df)

    # 2. Regime
    regime_res = MarketRegimeDetector.detect_regime_from_series(df, symbol)
    assert regime_res.current_regime is not None
    assert 0.0 <= regime_res.regime_confidence <= 1.0

    # 3. News
    raw_news = provider.get_news(symbol)
    news_res = NewsIntelligencePipeline.process_news(raw_news, symbol)
    assert news_res.total_events > 0

    # 4. Horizons
    horizons = MultiHorizonEngine.analyze(
        symbol=symbol,
        tech_summary=tech_summary,
        vol_summary=vol_summary,
        vol_metrics=vol_metrics,
        regime=regime_res.current_regime,
        fundamentals=provider.get_fundamentals(symbol),
        sentiment_score=news_res.aggregate_sentiment,
    )
    assert horizons.short_term.action in ["BUY", "SELL", "HOLD"]

    # 5. Council & Conflict
    council = ModelCouncil()
    council_res = council.evaluate_council(
        symbol=symbol,
        features_df=tech_df,
        regime=regime_res.current_regime,
        news_sentiment=news_res.aggregate_sentiment,
        news_materiality=news_res.aggregate_materiality,
    )
    assert len(council_res.votes) == 5

    conflict = EvidenceConflictEngine.analyze_conflict(council_res, symbol)
    assert 0.0 <= conflict.disagreement_score <= 1.0

    # 6. Uncertainty & Abstention
    uncertainty = UncertaintyEngine.evaluate(
        symbol=symbol,
        council_result=council_res,
        conflict_analysis=conflict,
        regime=regime_res.current_regime,
        regime_confidence=regime_res.regime_confidence,
        vol_summary=vol_summary,
        news_sentiment=news_res.aggregate_sentiment,
        news_materiality=news_res.aggregate_materiality,
    )
    assert uncertainty.recommended_action in ["BUY", "SELL", "HOLD", "NO_TRADE"]

    # 7. Portfolio & Risk Guardian
    portfolio_state = PortfolioAnalytics.analyze_portfolio(
        cash=50000.0,
        holdings={"AAPL": {"shares": 50, "price": 180.0, "sector": "Technology", "cost_basis": 170.0}},
    )
    risk_decision = RiskGuardian.evaluate_proposal(
        symbol=symbol,
        proposed_action=uncertainty.recommended_action,
        proposed_size_pct=5.0,
        asset_sector="Technology",
        asset_volatility_pct=vol_summary["hist_vol_20d_pct"],
        portfolio_state=portfolio_state,
        uncertainty_score=uncertainty.composite_uncertainty,
    )
    assert risk_decision.decision in ["APPROVE", "REDUCE", "REJECT"]

    # 8. Counterfactuals
    counterfactuals = CounterfactualEngine.generate_scenarios(
        symbol=symbol,
        current_price=tech_summary["close"],
        decision=uncertainty.recommended_action,
        annualized_vol_pct=vol_summary["hist_vol_20d_pct"],
        atr_14=tech_summary["atr_14"],
        ema_200=float(tech_df["ema_200"].iloc[-1]),
    )
    assert len(counterfactuals.invalidation_conditions) > 0

    # 9. LLM Reasoner
    reasoner = LLMReasoner()
    explanation = reasoner.synthesize_reasoning(
        symbol=symbol,
        decision=uncertainty.recommended_action,
        horizons=horizons,
        regime=regime_res.current_regime,
        regime_conf=regime_res.regime_confidence,
        council=council_res,
        conflict=conflict,
        uncertainty=uncertainty,
        risk=risk_decision,
        tech_summary=tech_summary,
        news_summary={"sentiment": news_res.aggregate_sentiment},
    )
    assert len(explanation.why_this_decision) > 0
    assert len(explanation.why_not) > 0
