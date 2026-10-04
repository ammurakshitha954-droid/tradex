"""
Deterministic and reproducible mock market data and news provider.
Enables offline development, reproducible unit/integration tests, and scenario stress testing.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd
from .base import MarketDataProvider, NewsDataProvider, FundamentalDataProvider, AssetMetadata, NewsItem


class MockDataProvider(MarketDataProvider, NewsDataProvider, FundamentalDataProvider):
    METADATA_STORE: Dict[str, AssetMetadata] = {
        "AAPL": AssetMetadata(symbol="AAPL", name="Apple Inc.", sector="Technology", industry="Consumer Electronics", exchange="NASDAQ", market_cap=3.4e12),
        "MSFT": AssetMetadata(symbol="MSFT", name="Microsoft Corp.", sector="Technology", industry="Software - Infrastructure", exchange="NASDAQ", market_cap=3.1e12),
        "NVDA": AssetMetadata(symbol="NVDA", name="NVIDIA Corp.", sector="Technology", industry="Semiconductors", exchange="NASDAQ", market_cap=2.9e12),
        "GOOGL": AssetMetadata(symbol="GOOGL", name="Alphabet Inc.", sector="Communication Services", industry="Internet Content", exchange="NASDAQ", market_cap=2.1e12),
        "AMZN": AssetMetadata(symbol="AMZN", name="Amazon.com Inc.", sector="Consumer Cyclical", industry="Internet Retail", exchange="NASDAQ", market_cap=1.9e12),
        "JPM": AssetMetadata(symbol="JPM", name="JPMorgan Chase & Co.", sector="Financial", industry="Banks - Diversified", exchange="NYSE", market_cap=5.6e11),
        "SPY": AssetMetadata(symbol="SPY", name="SPDR S&P 500 ETF Trust", sector="Broad Market", industry="ETF", exchange="NYSE Arca", market_cap=5.2e11),
        "QQQ": AssetMetadata(symbol="QQQ", name="Invesco QQQ Trust", sector="Broad Tech", industry="ETF", exchange="NASDAQ", market_cap=2.7e11),
        "RELIANCE.NS": AssetMetadata(symbol="RELIANCE.NS", name="Reliance Industries Ltd", sector="Energy", industry="Oil & Gas / Conglomerate", exchange="NSE", currency="INR", market_cap=1.9e12),
        "TCS.NS": AssetMetadata(symbol="TCS.NS", name="Tata Consultancy Services Ltd", sector="Technology", industry="IT Services", exchange="NSE", currency="INR", market_cap=1.4e12),
    }

    def __init__(self, seed: int = 42):
        self.seed = seed

    def get_asset_metadata(self, symbol: str) -> AssetMetadata:
        clean_sym = symbol.upper()
        if clean_sym in self.METADATA_STORE:
            return self.METADATA_STORE[clean_sym]
        return AssetMetadata(
            symbol=clean_sym,
            name=f"{clean_sym} Asset",
            sector="General",
            industry="General Industry",
            exchange="Global"
        )

    def get_historical_ohlcv(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"
    ) -> pd.DataFrame:
        """
        Generates realistic geometric Brownian motion with mean-reversion, jumps, and regime shifts.
        Deterministic based on symbol hash + seed.
        """
        sym_hash = abs(hash(symbol)) % 100000
        rng = np.random.default_rng(self.seed + sym_hash)

        # Generate business day range
        date_range = pd.date_range(start=start_date, end=end_date, freq="B")
        n = len(date_range)
        if n < 10:
            # Fallback if too short
            date_range = pd.date_range(end=end_date, periods=30, freq="B")
            n = len(date_range)

        # Base starting price
        base_price = 150.0 + (sym_hash % 200)
        daily_drift = 0.0004  # ~10% annual
        daily_vol = 0.015  # ~24% annual

        # Add regime variation:
        # Phase 1: Bull, Phase 2: Sideways, Phase 3: Volatile dip, Phase 4: Recovery
        regime_multipliers = np.ones(n)
        p1, p2, p3 = int(n * 0.3), int(n * 0.6), int(n * 0.8)
        regime_multipliers[:p1] = 1.2
        regime_multipliers[p1:p2] = 0.2
        regime_multipliers[p2:p3] = -1.5
        regime_multipliers[p3:] = 1.0

        shocks = rng.normal(daily_drift * regime_multipliers, daily_vol, n)
        # Add occasional jump
        jumps = rng.choice([0, 1], size=n, p=[0.97, 0.03]) * rng.normal(0, 0.03, n)
        returns = shocks + jumps

        price_series = base_price * np.exp(np.cumsum(returns))

        highs = price_series * (1.0 + np.abs(rng.normal(0.004, 0.003, n)))
        lows = price_series * (1.0 - np.abs(rng.normal(0.004, 0.003, n)))
        opens = lows + (highs - lows) * rng.uniform(0.1, 0.9, n)
        closes = price_series

        # Volume with occasional volume spikes
        base_vol = 25_000_000 + (sym_hash * 1000)
        vol_noise = rng.lognormal(0, 0.35, n)
        volume = (base_vol * vol_noise).astype(np.int64)

        df = pd.DataFrame(
            {
                "open": np.round(opens, 2),
                "high": np.round(highs, 2),
                "low": np.round(lows, 2),
                "close": np.round(closes, 2),
                "volume": volume,
            },
            index=date_range
        )
        df.index.name = "datetime"
        return df

    def get_latest_price(self, symbol: str) -> Dict[str, Any]:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=5)
        df = self.get_historical_ohlcv(symbol, start_date, end_date)
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2] if len(df) > 1 else last_row
        change = float(last_row["close"] - prev_row["close"])
        pct_change = float((change / prev_row["close"]) * 100.0) if prev_row["close"] != 0 else 0.0

        return {
            "symbol": symbol.upper(),
            "price": float(last_row["close"]),
            "change": round(change, 2),
            "pct_change": round(pct_change, 2),
            "volume": int(last_row["volume"]),
            "timestamp": df.index[-1].isoformat(),
        }

    def get_news(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[NewsItem]:
        clean_sym = symbol.upper()
        now = end_date or datetime.now(timezone.utc)
        
        sample_headlines = [
            (f"{clean_sym} reports quarterly revenue surge driven by enterprise cloud demand", "earnings", 0.72),
            (f"Federal Reserve interest rate stance creates mixed sentiment across {clean_sym} sector", "macro", -0.15),
            (f"{clean_sym} unveils new AI hardware architecture with 40% efficiency improvement", "product", 0.85),
            (f"Analyst consensus upgraded to Outperform for {clean_sym} with target revision", "analyst", 0.60),
            (f"Supply chain lead-times normalize following regional logistics adjustments for {clean_sym}", "operations", 0.20),
            (f"Regulatory scrutiny intensifies regarding antitrust compliance in tech ecosystem", "regulatory", -0.55),
        ]
        
        items = []
        for i, (headline, ev_type, sent) in enumerate(sample_headlines[:limit]):
            pub_time = now - timedelta(hours=(i * 14 + 2))
            items.append(
                NewsItem(
                    id=f"news-{clean_sym}-{i}",
                    symbol=clean_sym,
                    headline=headline,
                    summary=f"Automated intelligence report on {clean_sym}: {headline}. Market analysts are monitoring the follow-through implications.",
                    source="Reuters / Financial Times Intelligence",
                    published_at=pub_time,
                    event_type=ev_type,
                    raw_sentiment=sent,
                )
            )
        return items

    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        return {
            "symbol": symbol.upper(),
            "pe_ratio": 28.4,
            "forward_pe": 24.1,
            "peg_ratio": 1.45,
            "pb_ratio": 8.2,
            "debt_to_equity": 0.45,
            "operating_margin": 0.31,
            "free_cash_flow_yield": 0.038,
            "earnings_growth_yoy": 0.18,
            "dividend_yield": 0.007,
        }
