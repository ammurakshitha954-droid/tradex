"""
Core configuration settings for Adaptive AI Trading Decision-Support System.
Follows 12-factor application design with Pydantic settings.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Adaptive AI Trading Decision-Support System"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./trading_intelligence.db"

    # OpenAI / LLM
    OPENAI_API_KEY: str = Field(default="")
    LLM_MODEL: str = "gpt-4o"
    MOCK_LLM_IF_NO_KEY: bool = True

    # Market Data
    DEFAULT_SYMBOLS: List[str] = [
        "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", 
        "SPY", "QQQ", "RELIANCE.NS", "TCS.NS"
    ]
    PRIMARY_BENCHMARK: str = "SPY"
    DEFAULT_LOOKBACK_DAYS: int = 365

    # Risk Guardian hard constraints
    MAX_POSITION_SIZE_PCT: float = 0.10  # Max 10% in single asset
    MAX_SECTOR_EXPOSURE_PCT: float = 0.25  # Max 25% in one sector
    MAX_PORTFOLIO_DRAWDOWN_LIMIT: float = 0.15  # 15% hard circuit-breaker
    MAX_PORTFOLIO_VAR_95: float = 0.03  # 3% 1-day VaR limit
    MIN_CONFIDENCE_THRESHOLD: float = 0.55  # Below 55% -> NO_TRADE
    MAX_EVIDENCE_CONFLICT_SCORE: float = 0.65  # Above 65% conflict -> NO_TRADE or REDUCE
    MAX_MODEL_DISAGREEMENT_SCORE: float = 0.60

    # Execution Simulation Parameters
    DEFAULT_TRANSACTION_COST_BPS: float = 10.0  # 10 bps (0.10%)
    DEFAULT_SLIPPAGE_BPS: float = 5.0  # 5 bps
    EXECUTION_DELAY_MINUTES: int = 1


settings = Settings()
