"""
Comprehensive End-to-End System Lifecycle Verification Test.
Executes the entire 17-step institutional AI decision pipeline:
GATHER -> VALIDATE -> UNDERSTAND -> DETECT REGIME -> HORIZONS -> NEWS -> COUNCIL -> CONFLICT -> UNCERTAINTY -> ABSTAIN -> PORTFOLIO -> RISK GUARDIAN -> EXECUTE -> COUNTERFACTUAL -> REASON -> MEMORY -> LEARN
"""
from datetime import datetime, timedelta
import pytest
from backend.app.data.providers.mock_provider import MockDataProvider
from backend.app.data.validator import MarketDataValidator
from backend.app.features.technical import TechnicalIndicators
from backend.app.features.volatility import VolatilityIndicators
from backend.app.features.volume import VolumeIndicators
from backend.app.features.risk_metrics import RiskMetricsCalculator
from backend.app.regime.detector import MarketRegimeDetector
from backend.app.reasoning.horizons import MultiHorizonEngine
from backend.app.news.pipeline import NewsIntelligencePipeline
from backend.app.models.council import ModelCouncil
from backend.app.uncertainty.conflict_engine import EvidenceConflictEngine
from backend.app.uncertainty.abstention import UncertaintyEngine
from backend.app.portfolio.analytics import PortfolioAnalytics
from backend.app.risk.guardian import RiskGuardian
from backend.app.execution.simulator import ExecutionSimulator, ExecutionOrder
from backend.app.reasoning.counterfactual import CounterfactualEngine
from backend.app.reasoning.llm_reasoner import LLMReasoner
from backend.app.memory.decision_memory import DecisionMemoryEngine
from backend.app.backtest.engine import BacktestEngine, BacktestConfig
from backend.app.evaluation.ablation import AblationEngine


def test_complete_e2e_system_lifecycle():
    symbol = "NVDA"
    provider = MockDataProvider(seed=555)
    now = datetime.now()
    start = now - timedelta(days=365)

    # 1. GATHER & VALIDATE
    df = provider.get_historical_ohlcv(symbol, start, now)
    is_valid, errs = MarketDataValidator.validate_ohlcv(df)
    assert is_valid, f"Validation errors: {errs}"

    # 2. QUANTITATIVE ENGINE (Deterministic)
    tech_df = TechnicalIndicators.compute_all_indicators(df)
    vol_df = VolatilityIndicators.compute_volatility(tech_df)
    full_df = VolumeIndicators.compute_volume_metrics(vol_df).bfill().ffill()

    tech_summary = TechnicalIndicators.get_latest_signal_summary(full_df)
    vol_summary = VolatilityIndicators.get_latest_volatility_summary(full_df)
    vol_metrics = VolumeIndicators.get_latest_volume_summary(full_df)
    assert tech_summary["technical_signal"] in ["BUY", "SELL", "HOLD"]

    # 3. REGIME DETECTION (7 states)
    regime_res = MarketRegimeDetector.detect_regime_from_series(df, symbol)
    assert regime_res.current_regime is not None
    assert len(regime_res.regime_probabilities) == 7

    # 4. NEWS INTELLIGENCE & MATERIALITY
    raw_news = provider.get_news(symbol)
    news_summary = NewsIntelligencePipeline.process_news(raw_news, symbol)
    assert news_summary.total_events > 0

    # 5. MULTI-HORIZON REASONING (Short, Med, Long)
    horizons = MultiHorizonEngine.analyze(
        symbol=symbol,
        tech_summary=tech_summary,
        vol_summary=vol_summary,
        vol_metrics=vol_metrics,
        regime=regime_res.current_regime,
        fundamentals=provider.get_fundamentals(symbol),
        sentiment_score=news_summary.aggregate_sentiment,
    )
    assert horizons.strongest_horizon in ["Short-Term", "Medium-Term", "Long-Term"]

    # 6. MODEL COUNCIL (5 heterogeneous models)
    council = ModelCouncil()
    council_res = council.evaluate_council(
        symbol=symbol,
        features_df=full_df,
        regime=regime_res.current_regime,
        news_sentiment=news_summary.aggregate_sentiment,
        news_materiality=news_summary.aggregate_materiality,
    )
    assert len(council_res.votes) == 5

    # 7. EVIDENCE CONFLICT & DISAGREEMENT
    conflict_res = EvidenceConflictEngine.analyze_conflict(council_res, symbol)
    assert 0.0 <= conflict_res.disagreement_score <= 1.0

    # 8. UNCERTAINTY & EXPLICIT ABSTENTION (NO_TRADE)
    uncertainty_res = UncertaintyEngine.evaluate(
        symbol=symbol,
        council_result=council_res,
        conflict_analysis=conflict_res,
        regime=regime_res.current_regime,
        regime_confidence=regime_res.regime_confidence,
        vol_summary=vol_summary,
        news_sentiment=news_summary.aggregate_sentiment,
        news_materiality=news_summary.aggregate_materiality,
    )
    assert uncertainty_res.recommended_action in ["BUY", "SELL", "HOLD", "NO_TRADE"]

    # 9. PORTFOLIO RISK & CONCENTRATION
    portfolio = PortfolioAnalytics.analyze_portfolio(
        cash=40_000.0,
        holdings={"AAPL": {"shares": 40, "price": 220.0, "sector": "Technology", "cost_basis": 200.0}},
    )
    assert portfolio.total_equity > 40_000.0

    # 10. INDEPENDENT RISK GUARDIAN (APPROVE / REDUCE / REJECT)
    risk_ruling = RiskGuardian.evaluate_proposal(
        symbol=symbol,
        proposed_action=uncertainty_res.recommended_action,
        proposed_size_pct=8.0,
        asset_sector="Technology",
        asset_volatility_pct=vol_summary["hist_vol_20d_pct"],
        portfolio_state=portfolio,
        uncertainty_score=uncertainty_res.composite_uncertainty,
    )
    assert risk_ruling.decision in ["APPROVE", "REDUCE", "REJECT"]

    # 11. REALISTIC EXECUTION SIMULATION (Slippage & Fees)
    if risk_ruling.approved_position_pct > 0 and risk_ruling.proposed_action == "BUY":
        target_notional = portfolio.total_equity * (risk_ruling.approved_position_pct / 100.0)
        req_shares = target_notional / tech_summary["close"]
        order = ExecutionOrder(
            symbol=symbol,
            side="BUY",
            requested_shares=req_shares,
            market_price=tech_summary["close"],
            asset_volume_20d_sma=float(vol_metrics["volume_sma_20"]),
        )
        exec_report = ExecutionSimulator.simulate_order_execution(order)
        assert exec_report.status == "FILLED"
        assert exec_report.total_transaction_friction > 0.0

    # 12. COUNTERFACTUAL ENGINE ("What would change my mind?")
    counterfactuals = CounterfactualEngine.generate_scenarios(
        symbol=symbol,
        current_price=tech_summary["close"],
        decision=uncertainty_res.recommended_action,
        annualized_vol_pct=vol_summary["hist_vol_20d_pct"],
        atr_14=tech_summary["atr_14"],
        ema_200=float(full_df["ema_200"].iloc[-1]),
        position_size_pct=risk_ruling.approved_position_pct,
    )
    assert len(counterfactuals.invalidation_conditions) > 0

    # 13. ADAPTIVE AI REASONER (WHY THIS DECISION vs WHY NOT)
    reasoner = LLMReasoner()
    explanation = reasoner.synthesize_reasoning(
        symbol=symbol,
        decision=uncertainty_res.recommended_action,
        horizons=horizons,
        regime=regime_res.current_regime,
        regime_conf=regime_res.regime_confidence,
        council=council_res,
        conflict=conflict_res,
        uncertainty=uncertainty_res,
        risk=risk_ruling,
        tech_summary=tech_summary,
        news_summary={"sentiment": news_summary.aggregate_sentiment},
    )
    assert len(explanation.why_this_decision) > 0
    assert len(explanation.why_not) > 0

    # 14. CONTEXTUAL DECISION MEMORY & SELF-CORRECTION
    memory_engine = DecisionMemoryEngine()
    record = memory_engine.store_decision(
        decision_id="test-e2e-001",
        symbol=symbol,
        decision=uncertainty_res.recommended_action,
        confidence=uncertainty_res.calibrated_confidence,
        uncertainty=uncertainty_res.composite_uncertainty,
        regime=regime_res.current_regime,
        dominant_evidence=conflict_res.dominant_evidence,
        risk_status=risk_ruling.decision,
        approved_size_pct=risk_ruling.approved_position_pct,
    )
    # Simulate post-trade evaluation after 1 month
    evaluated = memory_engine.evaluate_outcome(
        memory_id=record.id,
        realized_return_pct=8.4,
        realized_drawdown_pct=-1.8,
    )
    assert evaluated is not None
    assert evaluated.decision_quality_label != "PENDING"
    assert evaluated.validation_status == "VALIDATED_LEARNING"

    # 15. BACKTESTING & ABLATION STUDY
    bt_cfg = BacktestConfig(symbol=symbol, initial_capital=50000.0, strategy="full_adaptive")
    bt_res = BacktestEngine.run_backtest(df, bt_cfg)
    assert bt_res.final_equity > 0.0

    exp_report = AblationEngine.run_full_experiment_suite(df, symbol=symbol, seed=42)
    assert len(exp_report.ablations) == 8
    assert len(exp_report.baselines) == 8
