export type MarketRegime = 
  | "BULL_TRENDING"
  | "BEAR_TRENDING"
  | "SIDEWAYS_RANGING"
  | "HIGH_VOLATILITY"
  | "LOW_VOLATILITY_COMPRESSION"
  | "CRISIS_STRESS"
  | "TRANSITION_UNCERTAIN";

export type DecisionAction = "BUY" | "SELL" | "HOLD" | "NO_TRADE";

export type RiskGuardianStatus = "APPROVE" | "REDUCE" | "REJECT";

export interface AssetQuote {
  symbol: string;
  price: number;
  change: number;
  pct_change: number;
  volume: number;
  timestamp: string;
  name?: string;
  sector?: string;
  exchange?: string;
}

export interface MarketPulse {
  benchmark: string;
  market_regime: MarketRegime;
  regime_confidence: number;
  stability_score: number;
  key_macro_drivers: string[];
  market_breadth_advance_pct: number;
  watchlist: AssetQuote[];
  timestamp: string;
}

export interface HorizonSignal {
  timeframe: string;
  action: DecisionAction;
  conviction: number;
  drivers: string[];
  risks: string[];
}

export interface MultiHorizonAnalysis {
  symbol: string;
  short_term: HorizonSignal;
  medium_term: HorizonSignal;
  long_term: HorizonSignal;
  horizon_agreement: boolean;
  agreement_score: number;
  strongest_horizon: string;
  weakest_horizon: string;
  conflict_summary: string;
  decision_impact: string;
}

export interface ConfidenceBreakdown {
  technical_confidence: number;
  news_confidence: number;
  regime_confidence: number;
  model_agreement_confidence: number;
  volatility_quality_score: number;
  data_quality_score: number;
}

export interface UncertaintyAssessment {
  symbol: string;
  composite_uncertainty: number;
  calibrated_confidence: number;
  should_abstain: boolean;
  recommended_action: DecisionAction;
  abstention_reasons: string[];
  confidence_drivers: string[];
  confidence_reducers: string[];
  breakdown: ConfidenceBreakdown;
}

export interface ConflictPair {
  source_a: string;
  signal_a: string;
  source_b: string;
  signal_b: string;
  severity: "NONE" | "MILD" | "STRONG";
  description: string;
}

export interface EvidenceConflictAnalysis {
  symbol: string;
  agreement_score: number;
  disagreement_score: number;
  conflict_severity: "LOW" | "MILD" | "HIGH" | "EXTREME";
  dominant_evidence: string;
  conflicting_evidence: string[];
  conflict_pairs: ConflictPair[];
  entropy_score: number;
  uncertainty_penalty: number;
  conflict_explanation: string;
}

export interface RiskGuardianDecision {
  decision: RiskGuardianStatus;
  symbol: string;
  proposed_action: string;
  proposed_position_pct: number;
  approved_position_pct: number;
  binding_constraints: string[];
  risk_score: number;
  passed_all_checks: boolean;
  explanation: string;
}

export interface ScenarioOutcome {
  name: string;
  probability_pct: number;
  price_target: number;
  expected_return_pct: number;
  portfolio_impact_pct: number;
  trigger_conditions: string[];
  time_horizon_days: number;
}

export interface CounterfactualAnalysis {
  symbol: string;
  decision: DecisionAction;
  base_case: ScenarioOutcome;
  adverse_case: ScenarioOutcome;
  severe_case: ScenarioOutcome;
  invalidation_conditions: string[];
  key_vulnerabilities: string[];
  stop_loss_level: number;
  take_profit_level: number;
}

export interface ModelVote {
  model_name: string;
  signal: DecisionAction;
  conviction: number;
  primary_rationale: string;
  weight: number;
}

export interface ModelCouncilResult {
  symbol: string;
  votes: ModelVote[];
  consensus_signal: DecisionAction;
  consensus_conviction: number;
  vote_distribution: Record<string, number>;
}

export interface StructuredAIExplanation {
  summary: string;
  why_this_decision: string[];
  why_not: string[];
  horizon_tension_analysis: string;
  macro_regime_implication: string;
  risk_governance_takeaway: string;
}

export interface DecisionRecord {
  id: string;
  symbol: string;
  timestamp: string;
  final_decision: DecisionAction;
  calibrated_confidence: number;
  composite_uncertainty: number;
  approved_position_pct: number;
  current_price: number;
  expected_return_pct: number;
  expected_risk_pct: number;
  market_regime: MarketRegime;
  regime_confidence: number;
  horizons: MultiHorizonAnalysis;
  uncertainty: UncertaintyAssessment;
  conflict: EvidenceConflictAnalysis;
  risk_guardian: RiskGuardianDecision;
  counterfactuals: CounterfactualAnalysis;
  council: ModelCouncilResult;
  explanation: StructuredAIExplanation;
  model_version: string;
}

export interface MemoryRecord {
  id: string;
  symbol: string;
  timestamp: string;
  decision: DecisionAction;
  confidence: number;
  uncertainty: number;
  regime: MarketRegime;
  dominant_evidence: string;
  risk_status: RiskGuardianStatus;
  approved_size_pct: number;
  realized_return_pct?: number;
  realized_drawdown_pct?: number;
  decision_quality_label: string;
  error_attribution?: string;
  validated_lesson?: string;
  validation_status: string;
}

export interface DecisionReplayData {
  memory_id: string;
  symbol: string;
  decision_timestamp: string;
  what_ai_knew_then: {
    market_regime: MarketRegime;
    calibrated_confidence: number;
    composite_uncertainty: number;
    dominant_evidence: string;
    risk_guardian_evaluation: RiskGuardianStatus;
    approved_allocation_pct: number;
  };
  what_ai_decided: DecisionAction;
  why: string;
  what_happened: {
    subsequent_return_pct: number | string;
    subsequent_drawdown_pct: number | string;
  };
  was_the_decision_good: {
    classification: string;
    process_vs_luck_analysis: string;
  };
  what_did_ai_learn: {
    error_attribution: string;
    validated_lesson: string;
    validation_status: string;
  };
}

export interface PortfolioPosition {
  symbol: string;
  shares: number;
  current_price: number;
  market_value: number;
  weight_pct: number;
  sector: string;
  unrealized_pnl_pct: number;
}

export interface PortfolioState {
  total_equity: number;
  cash: number;
  invested_equity: number;
  positions: PortfolioPosition[];
  sector_exposures: Record<string, number>;
  top_3_concentration_pct: number;
  hhi_concentration_index: number;
  portfolio_volatility_annualized: number;
  portfolio_cvar_95: number;
  current_drawdown_pct: number;
  peak_equity: number;
}

export interface BaselineMetricRow {
  name: string;
  category: "Baseline" | "Ablation";
  annualized_return_pct: number;
  annualized_volatility_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown_pct: number;
  cvar_95_pct: number;
  win_rate_pct: number;
  profit_factor: number;
  total_trades: number;
  abstentions_count: number;
  marginal_contribution_note: string;
}

export interface ExperimentReport {
  experiment_id: string;
  symbol: string;
  timeframe: string;
  seed: number;
  transaction_cost_bps: number;
  slippage_bps: number;
  baselines: BaselineMetricRow[];
  ablations: BaselineMetricRow[];
  research_conclusion: string;
}

export interface BacktestResult {
  symbol: string;
  strategy_name: string;
  initial_capital: number;
  final_equity: number;
  total_return_pct: number;
  annualized_return_pct: number;
  annualized_volatility_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown_pct: number;
  calmar_ratio: number;
  cvar_95_pct: number;
  win_rate_pct: number;
  profit_factor: number;
  total_trades: number;
  abstentions_count: number;
  total_costs_paid: number;
  equity_curve: Array<{
    date: string;
    equity: number;
    drawdown_pct: number;
    benchmark_price: number;
    regime: string;
  }>;
  regime_breakdown: Record<string, {
    annualized_return_pct: number;
    sharpe_ratio: number;
    observations: number;
  }>;
  in_sample_sharpe: number;
  out_of_sample_sharpe: number;
}

export interface SystemHealth {
  status: string;
  timestamp: string;
  environment: string;
  services: Record<string, { status: string; [key: string]: any }>;
  model_versions: Record<string, string>;
  system_metrics: Record<string, number>;
}
