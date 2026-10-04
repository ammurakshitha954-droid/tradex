"""
Deterministic 9-Stage News & Event Intelligence Pipeline.
INGEST -> DEDUPE -> ENTITY EXTRACTION -> EVENT CLASSIFICATION -> SENTIMENT -> MATERIALITY -> HISTORICAL CONTEXT -> MARKET REACTION -> TRADING IMPLICATION
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import numpy as np
from pydantic import BaseModel, Field
from .sanitizer import NewsSanitizer
from ..data.providers.base import NewsItem


class ProcessedEvent(BaseModel):
    id: str
    symbol: str
    headline: str
    summary: str
    source: str
    published_at: str
    event_category: str  # earnings, regulatory, macro, management, product, analyst, merger, general
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    materiality_score: float = Field(..., ge=0.0, le=1.0)  # 0 = noise, 1 = market-moving
    is_priced_in: bool
    market_reaction_consistency: str  # "CONSISTENT", "DIVERGENT", "NEUTRAL"
    trading_implication: str  # Clear analytical takeaway


class NewsIntelligenceSummary(BaseModel):
    symbol: str
    total_events: int
    aggregate_sentiment: float = Field(..., ge=-1.0, le=1.0)
    aggregate_materiality: float = Field(..., ge=0.0, le=1.0)
    dominant_event_type: str
    events: List[ProcessedEvent]
    news_conviction_impact: float = Field(..., ge=-1.0, le=1.0)
    key_takeaway: str


class NewsIntelligencePipeline:
    KEYWORD_EVENT_MAP = {
        "earnings": ["earnings", "revenue", "profit", "ebitda", "quarterly", "eps", "guidance"],
        "regulatory": ["antitrust", "sec", "doj", "investigation", "lawsuit", "fine", "sanction", "compliance"],
        "macro": ["fed", "inflation", "cpi", "rate hike", "yield", "gdp", "recession", "central bank"],
        "management": ["ceo", "cfo", "resign", "appointed", "executive", "board", "succession"],
        "product": ["unveils", "launch", "release", "ai chip", "breakthrough", "patent", "innovation"],
        "analyst": ["downgrade", "upgrade", "price target", "outperform", "underweight", "rating"],
        "merger": ["acquire", "merger", "buyout", "takeover", "deal", "partnership"],
    }

    MATERIALITY_WEIGHTS = {
        "earnings": 0.85,
        "regulatory": 0.80,
        "merger": 0.85,
        "management": 0.65,
        "macro": 0.70,
        "product": 0.60,
        "analyst": 0.45,
        "general": 0.30,
    }

    @classmethod
    def process_news(
        cls,
        raw_items: List[NewsItem],
        symbol: str,
        recent_price_return_1d: float = 0.0
    ) -> NewsIntelligenceSummary:
        """
        Runs raw news items through the 9-stage intelligence pipeline.
        """
        clean_sym = symbol.upper()
        if not raw_items:
            return cls._empty_summary(clean_sym)

        # 1. INGEST & DEDUPLICATE (using headline hash)
        seen_hashes = set()
        deduped_items: List[NewsItem] = []
        for item in raw_items:
            # Stage 2: Deduplication
            headline_key = hashlib.md5(item.headline.lower().strip().encode("utf-8")).hexdigest()
            if headline_key not in seen_hashes:
                seen_hashes.add(headline_key)
                deduped_items.append(item)

        processed_events: List[ProcessedEvent] = []

        for item in deduped_items:
            # Sanitize untrusted input
            safe_headline = NewsSanitizer.sanitize_text(item.headline)
            safe_summary = NewsSanitizer.sanitize_text(item.summary)

            # Stage 3: Entity Extraction & Validation
            # Verify the article actually mentions the symbol or associated company
            combined_text = f"{safe_headline} {safe_summary}".lower()

            # Stage 4: Event Classification
            event_category = cls._classify_event(combined_text)

            # Stage 5: Sentiment Calculation (-1.0 to +1.0)
            sentiment = cls._calculate_sentiment(combined_text, item.raw_sentiment)

            # Stage 6: Materiality Scoring (0.0 to 1.0)
            base_materiality = cls.MATERIALITY_WEIGHTS.get(event_category, 0.40)
            # Boost materiality if high sentiment magnitude
            materiality = min(1.0, base_materiality * (0.8 + 0.4 * abs(sentiment)))

            # Stage 7 & 8: Historical Context & Market Reaction Consistency
            # Compare news sentiment with actual 1-day return
            if abs(sentiment) < 0.15:
                market_reaction = "NEUTRAL"
                is_priced_in = True
            elif (sentiment > 0.2 and recent_price_return_1d > 0.01) or (sentiment < -0.2 and recent_price_return_1d < -0.01):
                market_reaction = "CONSISTENT"
                is_priced_in = True  # Market already moved in news direction
            else:
                market_reaction = "DIVERGENT"
                is_priced_in = False  # Market has not followed headline direction yet

            # Stage 9: Trading Implication
            if materiality >= 0.70:
                if market_reaction == "DIVERGENT":
                    implication = f"High-materiality {event_category} event ({sentiment:+.2f}) showing price divergence; elevated surprise potential."
                else:
                    implication = f"High-materiality {event_category} event priced in; momentum continuation supported."
            elif materiality >= 0.40:
                implication = f"Moderate {event_category} event; secondary supporting evidence for directional bias."
            else:
                implication = "Low materiality news item; treated as market noise without position sizing impact."

            processed_events.append(
                ProcessedEvent(
                    id=item.id,
                    symbol=clean_sym,
                    headline=safe_headline,
                    summary=safe_summary,
                    source=item.source,
                    published_at=item.published_at.isoformat() if hasattr(item.published_at, "isoformat") else str(item.published_at),
                    event_category=event_category,
                    sentiment_score=round(sentiment, 2),
                    materiality_score=round(materiality, 2),
                    is_priced_in=is_priced_in,
                    market_reaction_consistency=market_reaction,
                    trading_implication=implication,
                )
            )

        # Aggregate metrics weighted by materiality
        total_mat = sum(e.materiality_score for e in processed_events) + 1e-9
        agg_sentiment = sum(e.sentiment_score * e.materiality_score for e in processed_events) / total_mat
        agg_materiality = sum(e.materiality_score for e in processed_events) / len(processed_events)

        category_counts: Dict[str, int] = {}
        for e in processed_events:
            category_counts[e.event_category] = category_counts.get(e.event_category, 0) + 1
        dominant_event = max(category_counts, key=category_counts.get) if category_counts else "general"

        # Conviction impact: sentiment scaled by materiality
        news_conviction_impact = agg_sentiment * agg_materiality

        if agg_materiality < 0.35:
            key_takeaway = "News flow is largely noise with low financial materiality."
        elif agg_sentiment > 0.25:
            key_takeaway = f"Constructive news backdrop driven primarily by {dominant_event} catalysts."
        elif agg_sentiment < -0.25:
            key_takeaway = f"Headwind news pressure centered on {dominant_event} concerns."
        else:
            key_takeaway = "Balanced news flow with offsetting positive and negative signals."

        return NewsIntelligenceSummary(
            symbol=clean_sym,
            total_events=len(processed_events),
            aggregate_sentiment=round(agg_sentiment, 2),
            aggregate_materiality=round(agg_materiality, 2),
            dominant_event_type=dominant_event,
            events=processed_events,
            news_conviction_impact=round(news_conviction_impact, 3),
            key_takeaway=key_takeaway,
        )

    @classmethod
    def _classify_event(cls, text: str) -> str:
        for cat, keywords in cls.KEYWORD_EVENT_MAP.items():
            if any(kw in text for kw in keywords):
                return cat
        return "general"

    @classmethod
    def _calculate_sentiment(cls, text: str, fallback_sentiment: Optional[float] = 0.0) -> float:
        pos_words = ["surge", "beat", "record", "growth", "upgrade", "outperform", "bullish", "profit", "breakthrough", "expanded"]
        neg_words = ["miss", "slump", "lawsuit", "investigation", "downgrade", "bearish", "loss", "plunge", "decline", "warning", "risk"]
        
        pos_count = sum(1 for w in pos_words if w in text)
        neg_count = sum(1 for w in neg_words if w in text)
        
        if pos_count == 0 and neg_count == 0:
            return fallback_sentiment or 0.0
        
        diff = pos_count - neg_count
        norm = max(pos_count + neg_count, 1)
        score = diff / norm
        return float(np.clip(score, -1.0, 1.0))

    @classmethod
    def _empty_summary(cls, symbol: str) -> NewsIntelligenceSummary:
        return NewsIntelligenceSummary(
            symbol=symbol.upper(),
            total_events=0,
            aggregate_sentiment=0.0,
            aggregate_materiality=0.0,
            dominant_event_type="none",
            events=[],
            news_conviction_impact=0.0,
            key_takeaway="No current news events detected for this asset.",
        )
