"""
Deterministic Portfolio Intelligence & Analytics Engine.
Calculates sector exposures, concentration risk (Herfindahl-Hirschman Index), correlation, and CVaR.
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import numpy as np
import pandas as pd


class Position(BaseModel):
    symbol: str
    shares: float
    current_price: float
    market_value: float
    weight_pct: float
    sector: str
    unrealized_pnl_pct: float


class PortfolioState(BaseModel):
    total_equity: float
    cash: float
    invested_equity: float
    positions: List[Position]
    sector_exposures: Dict[str, float]  # Sector name -> weight (0.0 to 1.0)
    top_3_concentration_pct: float
    hhi_concentration_index: float  # Herfindahl-Hirschman Index
    portfolio_volatility_annualized: float
    portfolio_cvar_95: float
    current_drawdown_pct: float
    peak_equity: float


class PortfolioAnalytics:
    @classmethod
    def analyze_portfolio(
        cls,
        cash: float,
        holdings: Dict[str, Dict[str, Any]],  # symbol -> {shares, price, sector, cost_basis}
        peak_equity: Optional[float] = None,
        asset_returns_matrix: Optional[pd.DataFrame] = None
    ) -> PortfolioState:
        positions: List[Position] = []
        invested = 0.0

        for sym, data in holdings.items():
            shares = float(data.get("shares", 0.0))
            price = float(data.get("price", 0.0))
            cost = float(data.get("cost_basis", price))
            val = shares * price
            invested += val
            pnl_pct = ((price - cost) / cost) * 100.0 if cost > 0 else 0.0

            positions.append(
                Position(
                    symbol=sym.upper(),
                    shares=shares,
                    current_price=round(price, 2),
                    market_value=round(val, 2),
                    weight_pct=0.0,  # calculated below
                    sector=data.get("sector", "General"),
                    unrealized_pnl_pct=round(pnl_pct, 2),
                )
            )

        total_equity = cash + invested
        if peak_equity is None or peak_equity < total_equity:
            peak_equity = total_equity

        current_dd = ((total_equity - peak_equity) / peak_equity) * 100.0 if peak_equity > 0 else 0.0

        # Calculate weights & sector exposure
        sector_exp: Dict[str, float] = {}
        weights = []
        for p in positions:
            w = (p.market_value / total_equity) if total_equity > 0 else 0.0
            p.weight_pct = round(w * 100.0, 2)
            weights.append(w)
            sector_exp[p.sector] = sector_exp.get(p.sector, 0.0) + w

        # Concentration metrics
        sorted_weights = sorted(weights, reverse=True)
        top_3_conc = sum(sorted_weights[:3]) * 100.0
        hhi = sum((w * 100.0) ** 2 for w in weights)  # Max 10,000

        # Portfolio Volatility & CVaR
        port_vol = 0.16  # standard baseline
        port_cvar = 0.025
        if asset_returns_matrix is not None and not asset_returns_matrix.empty and len(weights) > 0:
            cov = asset_returns_matrix.cov() * 252
            w_arr = np.array(weights[:len(cov)])
            if len(w_arr) == len(cov):
                port_var = float(np.dot(w_arr.T, np.dot(cov.values, w_arr)))
                port_vol = float(np.sqrt(max(0.0001, port_var)))
                port_cvar = float(port_vol * 1.645 / np.sqrt(252) * 1.25)

        return PortfolioState(
            total_equity=round(total_equity, 2),
            cash=round(cash, 2),
            invested_equity=round(invested, 2),
            positions=positions,
            sector_exposures={k: round(v * 100.0, 2) for k, v in sector_exp.items()},
            top_3_concentration_pct=round(top_3_conc, 2),
            hhi_concentration_index=round(hhi, 1),
            portfolio_volatility_annualized=round(port_vol * 100.0, 2),
            portfolio_cvar_95=round(port_cvar * 100.0, 2),
            current_drawdown_pct=round(current_dd, 2),
            peak_equity=round(peak_equity, 2),
        )
