"""
News Intelligence API routes: Ingested, classified, and materiality-filtered financial events.
"""
from typing import Optional
from fastapi import APIRouter, Query
from ...data.providers.mock_provider import MockDataProvider
from ...data.providers.yfinance_provider import YFinanceProvider
from ...news.pipeline import NewsIntelligencePipeline

router = APIRouter(prefix="/news", tags=["News & Event Intelligence"])
mock_provider = MockDataProvider()
yf_provider = YFinanceProvider(fallback_provider=mock_provider)


@router.get("")
def get_news_intelligence(
    symbol: str = Query(default="NVDA"),
    limit: int = Query(default=10, ge=1, le=50)
):
    clean_sym = symbol.upper()
    raw_news = yf_provider.get_news(clean_sym, limit=limit)
    summary = NewsIntelligencePipeline.process_news(raw_news, clean_sym)
    return summary.model_dump()
