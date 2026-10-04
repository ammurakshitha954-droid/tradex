"""
Realistic Execution Simulator.
Models transaction friction, non-linear slippage, liquidity constraints, and execution delays.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import numpy as np


class ExecutionOrder(BaseModel):
    symbol: str
    side: str  # "BUY", "SELL"
    requested_shares: float
    market_price: float
    asset_volume_20d_sma: float
    urgency: str = "NORMAL"  # "LOW", "NORMAL", "HIGH"


class ExecutionReport(BaseModel):
    symbol: str
    side: str
    filled_shares: float
    arrival_price: float
    effective_execution_price: float
    slippage_bps: float
    slippage_cost: float
    commission_fees: float
    total_transaction_friction: float
    participation_rate_pct: float
    status: str  # "FILLED", "PARTIALLY_FILLED", "REJECTED"
    timestamp: str


class ExecutionSimulator:
    BASE_COMMISSION_BPS = 5.0  # 0.05% brokerage/exchange fee
    IMPACT_COEFFICIENT = 0.15  # Square-root market impact constant

    @classmethod
    def simulate_order_execution(
        cls,
        order: ExecutionOrder,
        fixed_cost_bps: Optional[float] = None,
        custom_slippage_bps: Optional[float] = None,
    ) -> ExecutionReport:
        arrival_price = order.market_price
        shares = order.requested_shares
        if shares <= 0:
            return ExecutionReport(
                symbol=order.symbol,
                side=order.side,
                filled_shares=0.0,
                arrival_price=arrival_price,
                effective_execution_price=arrival_price,
                slippage_bps=0.0,
                slippage_cost=0.0,
                commission_fees=0.0,
                total_transaction_friction=0.0,
                participation_rate_pct=0.0,
                status="REJECTED",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # Calculate participation rate relative to daily volume
        adv = max(10_000.0, order.asset_volume_20d_sma)
        participation_rate = float(shares / adv)

        # Slippage Model: Almgren-Chriss square root law
        # Slippage BPS = spread_half + impact_coef * sqrt(participation_rate) * 10000
        if custom_slippage_bps is not None:
            slippage_bps = custom_slippage_bps
        else:
            base_half_spread_bps = 2.5
            market_impact_bps = cls.IMPACT_COEFFICIENT * np.sqrt(min(participation_rate, 0.20)) * 1000.0
            urgency_multiplier = 1.5 if order.urgency == "HIGH" else (0.8 if order.urgency == "LOW" else 1.0)
            slippage_bps = (base_half_spread_bps + market_impact_bps) * urgency_multiplier

        # Execution price depends on side
        slippage_fraction = slippage_bps / 10000.0
        if order.side == "BUY":
            effective_price = arrival_price * (1.0 + slippage_fraction)
        else:
            effective_price = arrival_price * (1.0 - slippage_fraction)

        trade_notional = shares * arrival_price
        slippage_cost = abs(effective_price - arrival_price) * shares

        # Commissions / Fees
        comm_bps = fixed_cost_bps if fixed_cost_bps is not None else cls.BASE_COMMISSION_BPS
        commission_fees = trade_notional * (comm_bps / 10000.0)
        total_friction = slippage_cost + commission_fees

        return ExecutionReport(
            symbol=order.symbol.upper(),
            side=order.side,
            filled_shares=round(shares, 4),
            arrival_price=round(arrival_price, 2),
            effective_execution_price=round(effective_price, 2),
            slippage_bps=round(slippage_bps, 2),
            slippage_cost=round(slippage_cost, 2),
            commission_fees=round(commission_fees, 2),
            total_transaction_friction=round(total_friction, 2),
            participation_rate_pct=round(participation_rate * 100.0, 3),
            status="FILLED",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
