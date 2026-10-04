"""
Base abstract classes for Provider-Independent Market Data and News Sources.
Allows seamlessly swapping between real market APIs (yfinance, NSE, etc.) and reproducible testing providers.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd
from pydantic import BaseModel


class NewsItem(BaseModel):
    id: str
    symbol: str
    headline: str
    summary: str
    source: str
    published_at: datetime
    url: Optional[str] = None
    event_type: Optional[str] = "general"
    raw_sentiment: Optional[float] = 0.0  # -1.0 to 1.0


class AssetMetadata(BaseModel):
    symbol: str
    name: str
    sector: str
    industry: str
    exchange: str
    currency: str = "USD"
    market_cap: Optional[float] = None


class MarketDataProvider(ABC):
    @abstractmethod
    def get_historical_ohlcv(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"
    ) -> pd.DataFrame:
        """
        Returns DataFrame with columns:
        ['datetime', 'open', 'high', 'low', 'close', 'volume']
        Index: pd.DatetimeIndex
        """
        pass

    @abstractmethod
    def get_asset_metadata(self, symbol: str) -> AssetMetadata:
        """Returns structured metadata for asset (sector, exchange, etc.)"""
        pass

    @abstractmethod
    def get_latest_price(self, symbol: str) -> Dict[str, Any]:
        """Returns real-time or latest available quote with timestamp"""
        pass


class NewsDataProvider(ABC):
    @abstractmethod
    def get_news(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 20
    ) -> List[NewsItem]:
        """Returns news items for a given symbol within time bounds"""
        pass


class FundamentalDataProvider(ABC):
    @abstractmethod
    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Returns fundamental ratios (P/E, P/B, Debt/Equity, Earnings Growth)"""
        pass
