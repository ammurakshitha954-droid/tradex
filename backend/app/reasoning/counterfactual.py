"""
Counterfactual Scenario Engine: "What would make this decision wrong?"
Generates deterministic Base Case, Adverse Case, and Severe Shock scenarios with precise invalidation triggers.
"""
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ScenarioOutcome(BaseModel):
    name: str  # "Base Case", "Adverse Case", "Severe Stress Shock"
    probability_pct: float
    price_target: float
    expected_return_pct: float
    portfolio_impact_pct: float
    trigger_conditions: List[str]
    time_horizon_days: int


class CounterfactualAnalysis(BaseModel):
    symbol: str
    decision: str
    base_case: ScenarioOutcome
    adverse_case: ScenarioOutcome
    severe_case: ScenarioOutcome
    invalidation_conditions: List[str]  # "What would change my mind?"
    key_vulnerabilities: List[str]
    stop_loss_level: float
    take_profit_level: float


class CounterfactualEngine:
    @classmethod
    def generate_scenarios(
        cls,
        symbol: str,
        current_price: float,
        decision: str,
        annualized_vol_pct: float,
        atr_14: float,
        ema_200: float,
        position_size_pct: float = 5.0,
    ) -> CounterfactualAnalysis:
        vol = max(0.12, annualized_vol_pct / 100.0)
        daily_vol = vol / (252 ** 0.5)

        # 30-day projection (~21 trading days)
        horizon_days = 30
        t_factor = (horizon_days / 252) ** 0.5

        if decision == "BUY":
            # Base Case (Bullish Drift)
            base_ret = vol * t_factor * 0.85
            base_target = round(current_price * (1.0 + base_ret), 2)
            base_prob = 55.0

            # Adverse Case (1.5-sigma correction)
            adv_ret = -vol * t_factor * 1.20
            adv_target = round(current_price * (1.0 + adv_ret), 2)
            adv_prob = 33.0

            # Severe Case (3-sigma tail shock)
            sev_ret = -vol * t_factor * 2.50
            sev_target = round(current_price * (1.0 + sev_ret), 2)
            sev_prob = 12.0

            stop_loss = round(max(current_price - 2.5 * atr_14, ema_200 * 0.98), 2)
            take_profit = round(current_price + 3.5 * atr_14, 2)

            invalidation = [
                f"Close below structural support / 200 EMA at ${ema_200:.2f}",
                f"ATR trailing stop breach below ${stop_loss:.2f}",
                "Macro regime transition to CRISIS_STRESS or sudden volatility spike > 40%",
                "Negative high-materiality earnings revision or regulatory probe",
            ]
            vulnerabilities = [
                "Position vulnerable to sudden sector multiple compression",
                "High correlation with broad market beta during liquidity contractions",
            ]

        elif decision == "SELL":
            # Base Case (Bearish Drift)
            base_ret = -vol * t_factor * 0.85
            base_target = round(current_price * (1.0 + base_ret), 2)
            base_prob = 55.0

            # Adverse Case (Short squeeze / momentum reversal)
            adv_ret = vol * t_factor * 1.20
            adv_target = round(current_price * (1.0 + adv_ret), 2)
            adv_prob = 33.0

            # Severe Case (Breakout spike)
            sev_ret = vol * t_factor * 2.50
            sev_target = round(current_price * (1.0 + sev_ret), 2)
            sev_prob = 12.0

            stop_loss = round(current_price + 2.5 * atr_14, 2)
            take_profit = round(current_price - 3.5 * atr_14, 2)

            invalidation = [
                f"Decisive breakout above recent resistance at ${stop_loss:.2f}",
                "Positive surprise catalysts exceeding market consensus by > 20%",
                "Broad market transition to low-volatility risk-on expansion",
            ]
            vulnerabilities = [
                "Unbounded upside risk in sudden short squeeze scenarios",
                "Favorable sector rotation dampening downward pressure",
            ]

        else:  # HOLD or NO_TRADE
            base_ret = 0.01
            base_target = round(current_price * (1.0 + base_ret), 2)
            base_prob = 60.0

            adv_ret = -vol * t_factor * 0.80
            adv_target = round(current_price * (1.0 + adv_ret), 2)
            adv_prob = 25.0

            sev_ret = -vol * t_factor * 2.00
            sev_target = round(current_price * (1.0 + sev_ret), 2)
            sev_prob = 15.0

            stop_loss = round(current_price - 2.0 * atr_14, 2)
            take_profit = round(current_price + 2.0 * atr_14, 2)

            invalidation = [
                "Resolution of model disagreement above 75% consensus",
                "Clear breakout with abnormal volume (> 2.0x 20d average)",
                "Regime clarification from TRANSITION_UNCERTAIN to confirmed directional regime",
            ]
            vulnerabilities = [
                "Opportunity cost of missing early breakout acceleration",
            ]

        # Calculate portfolio impact: return * position weight
        w = position_size_pct / 100.0
        base_impact = round(base_ret * w * 100.0, 2)
        adv_impact = round(adv_ret * w * 100.0, 2)
        sev_impact = round(sev_ret * w * 100.0, 2)

        return CounterfactualAnalysis(
            symbol=symbol.upper(),
            decision=decision,
            base_case=ScenarioOutcome(
                name="Base Case (Expected Drift)",
                probability_pct=base_prob,
                price_target=base_target,
                expected_return_pct=round(base_ret * 100.0, 2),
                portfolio_impact_pct=base_impact,
                trigger_conditions=["Current regime and momentum persist within normal standard error."],
                time_horizon_days=horizon_days,
            ),
            adverse_case=ScenarioOutcome(
                name="Adverse Case (Moderate Correction)",
                probability_pct=adv_prob,
                price_target=adv_target,
                expected_return_pct=round(adv_ret * 100.0, 2),
                portfolio_impact_pct=adv_impact,
                trigger_conditions=["1.5-sigma technical mean-reversion shock or negative macro headline."],
                time_horizon_days=horizon_days,
            ),
            severe_case=ScenarioOutcome(
                name="Severe Case (Tail Stress Shock)",
                probability_pct=sev_prob,
                price_target=sev_target,
                expected_return_pct=round(sev_ret * 100.0, 2),
                portfolio_impact_pct=sev_impact,
                trigger_conditions=["Systemic market liquidity contraction or severe event failure."],
                time_horizon_days=horizon_days,
            ),
            invalidation_conditions=invalidation,
            key_vulnerabilities=vulnerabilities,
            stop_loss_level=stop_loss,
            take_profit_level=take_profit,
        )
