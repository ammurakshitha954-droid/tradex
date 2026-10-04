"""
Integration tests for FastAPI endpoints: Market, Assets, Regime, News, Portfolio, Decisions, Memory, Backtest, System.
"""
from fastapi.testclient import TestClient
import pytest
from backend.app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "OPERATIONAL"


def test_market_pulse():
    response = client.get("/api/v1/market/pulse")
    assert response.status_code == 200
    data = response.json()
    assert "market_regime" in data
    assert "watchlist" in data
    assert len(data["watchlist"]) > 0


def test_asset_endpoints():
    sym = "AAPL"
    overview = client.get(f"/api/v1/assets/{sym}")
    assert overview.status_code == 200
    assert overview.json()["metadata"]["symbol"] == sym

    chart = client.get(f"/api/v1/assets/{sym}/chart?days=120")
    assert chart.status_code == 200
    assert len(chart.json()["candles"]) > 20
    assert "overlays" in chart.json()


def test_regime_endpoints():
    response = client.get("/api/v1/regime/current?symbol=SPY")
    assert response.status_code == 200
    data = response.json()
    assert "current_regime" in data
    assert "regime_probabilities" in data

    timeline = client.get("/api/v1/regime/timeline?symbol=SPY")
    assert timeline.status_code == 200
    assert len(timeline.json()["timeline"]) > 5


def test_news_endpoint():
    response = client.get("/api/v1/news?symbol=NVDA&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "NVDA"
    assert "aggregate_sentiment" in data


def test_portfolio_and_risk():
    port = client.get("/api/v1/portfolio")
    assert port.status_code == 200
    data = port.json()
    assert data["total_equity"] > 0

    risk_check = client.post(
        "/api/v1/portfolio/risk-check",
        json={
            "symbol": "NVDA",
            "action": "BUY",
            "proposed_position_pct": 5.0,
            "asset_sector": "Technology",
            "asset_volatility_pct": 28.0,
            "uncertainty_score": 0.25,
        }
    )
    assert risk_check.status_code == 200
    assert risk_check.json()["decision"] in ["APPROVE", "REDUCE", "REJECT"]


def test_decisions_analyze_and_latest():
    res = client.post(
        "/api/v1/decisions/analyze",
        json={"symbol": "MSFT", "lookback_days": 180, "proposed_position_pct": 5.0}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["final_decision"] in ["BUY", "SELL", "HOLD", "NO_TRADE"]
    assert "horizons" in data
    assert "uncertainty" in data
    assert "counterfactuals" in data
    assert "explanation" in data
    assert len(data["explanation"]["why_this_decision"]) > 0

    latest = client.get("/api/v1/decisions/latest?symbol=MSFT")
    assert latest.status_code == 200

    debate = client.get("/api/v1/decisions/debate?symbol=MSFT")
    assert debate.status_code == 200
    assert len(debate.json()["council_votes"]) == 5


def test_memory_and_replay():
    memories = client.get("/api/v1/memory")
    assert memories.status_code == 200
    all_m = memories.json()
    assert len(all_m) > 0

    first_id = all_m[0]["id"]
    replay = client.get(f"/api/v1/memory/replay/{first_id}")
    assert replay.status_code == 200
    data = replay.json()
    assert "what_ai_knew_then" in data
    assert "what_ai_decided" in data
    assert "what_happened" in data
    assert "was_the_decision_good" in data
    assert "what_did_ai_learn" in data


def test_backtest_and_experiments():
    bt = client.post(
        "/api/v1/backtest",
        json={
            "symbol": "SPY",
            "initial_capital": 50000.0,
            "strategy": "full_adaptive",
            "transaction_cost_bps": 10.0,
            "slippage_bps": 5.0,
            "use_abstention": True,
        }
    )
    assert bt.status_code == 200
    assert bt.json()["final_equity"] > 0

    exp = client.get("/api/v1/experiments/suite?symbol=SPY")
    assert exp.status_code == 200
    assert len(exp.json()["baselines"]) == 8
    assert len(exp.json()["ablations"]) == 8


def test_system_health():
    res = client.get("/api/v1/system/health")
    assert res.status_code == 200
    assert res.json()["status"] == "HEALTHY"
