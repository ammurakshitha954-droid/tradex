"""
Real-world market data provider implementation using yfinance with graceful fallback.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
from .base import MarketDataProvider, NewsDataProvider, FundamentalDataProvider, AssetMetadata, NewsItem
from .mock_provider import MockDataProvider
from ...core.logging import get_logger

logger = get_logger("yfinance_provider")


class YFinanceProvider(MarketDataProvider, NewsDataProvider, FundamentalDataProvider):
    def __init__(self, fallback_provider: Optional[MarketDataProvider] = None):
        self.fallback = fallback_provider or MockDataProvider()

    def get_historical_ohlcv(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"
    ) -> pd.DataFrame:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=(end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                interval=timeframe,
                auto_adjust=True,
            )
            if df.empty or len(df) < 5:
                logger.warning(f"yfinance returned empty/minimal data for {symbol}. Using fallback.")
                return self.fallback.get_historical_ohlcv(symbol, start_date, end_date, timeframe)

            # Normalize column names
            df = df.reset_index()
            # Normalize date column
            date_col = "Date" if "Date" in df.columns else ("Datetime" if "Datetime" in df.columns else df.columns[0])
            df["datetime"] = pd.to_datetime(df[date_col]).dt.tz_localize(None)
            df = df.set_index("datetime")
            
            rename_map = {
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume"
            }
            clean_df = df[[c for c in rename_map.keys() if c in df.columns]].rename(columns=rename_map)
            clean_df.index.name = "datetime"
            return clean_df
        except Exception as e:
            logger.warning(f"Error fetching yfinance data for {symbol}: {e}. Delegating to fallback.")
            return self.fallback.get_historical_ohlcv(symbol, start_date, end_date, timeframe)

    def get_asset_metadata(self, symbol: str) -> AssetMetadata:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}
            return AssetMetadata(
                symbol=symbol.upper(),
                name=info.get("shortName") or info.get("longName") or f"{symbol.upper()} Asset",
                sector=info.get("sector") or "General",
                industry=info.get("industry") or "General Industry",
                exchange=info.get("exchange") or "Global",
                currency=info.get("currency") or "USD",
                market_cap=info.get("marketCap"),
            )
        except Exception as e:
            logger.warning(f"Error fetching metadata for {symbol}: {e}. Using fallback.")
            return self.fallback.get_asset_metadata(symbol)

    def get_latest_price(self, symbol: str) -> Dict[str, Any]:
        try:
            ticker = yf.Ticker(symbol)
            fast_info = getattr(ticker, "fast_info", None)
            if fast_info and hasattr(fast_info, "last_price") and fast_info.last_price is not None:
                last_price = float(fast_info.last_price)
                prev_close = float(getattr(fast_info, "previous_close", last_price))
                change = last_price - prev_close
                pct_change = (change / prev_close) * 100.0 if prev_close != 0 else 0.0
                return {
                    "symbol": symbol.upper(),
                    "price": round(last_price, 2),
                    "change": round(change, 2),
                    "pct_change": round(pct_change, 2),
                    "volume": int(getattr(fast_info, "last_volume", 0) or 0),
                    "timestamp": datetime.utcnow().isoformat(),
                }
        except Exception as e:
            logger.warning(f"Error fetching fast info for {symbol}: {e}. Using fallback.")
        return self.fallback.get_latest_price(symbol)

    def get_news(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[NewsItem]:
        try:
            ticker = yf.Ticker(symbol)
            raw_news = ticker.news or []
            items = []
            for i, n in enumerate(raw_news[:limit]):
                content = n.get("content", {}) if "content" in n else n
                title = content.get("title") or n.get("title") or "Market Update"
                summary = content.get("summary") or n.get("summary") or title
                pub_time = datetime.fromtimestamp(content.get("pubDate") or n.get("providerPublishTime", datetime.utcnow().timestamp()))
                items.append(
                    NewsItem(
                        id=f"yf-{symbol}-{i}",
                        symbol=symbol.upper(),
                        headline=title,
                        summary=summary,
                        source=content.get("provider", {}).get("displayName") or "Financial Wire",
                        published_at=pub_time,
                        url=content.get("canonicalUrl", {}).get("url") or n.get("link"),
                        event_type="market_news",
                        raw_sentiment=0.0,
                    )
                )
            if items:
                return items
        except Exception as e:
            logger.warning(f"Error fetching yfinance news for {symbol}: {e}.")
        return self.fallback.get_news(symbol, start_date, end_date, limit)

    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}
            if "trailingPE" in info:
                return {
                    "symbol": symbol.upper(),
                    "pe_ratio": info.get("trailingPE"),
                    "forward_pe": info.get("forwardPE"),
                    "peg_ratio": info.get("pegRatio"),
                    "pb_ratio": info.get("priceToBook"),
                    "debt_to_equity": info.get("debtToEquity"),
                    "operating_margin": info.get("operatingMargins"),
                    "free_cash_flow_yield": None,
                    "earnings_growth_yoy": info.get("earningsGrowth"),
                    "dividend_yield": info.get("dividendYield"),
                }
        except Exception:
            pass
        return self.fallback.get_fundamentals(symbol)
