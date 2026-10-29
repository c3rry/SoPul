"""Pulse2026 Kalshi API v2 Public Market Client ($0 Ingestion Cost)."""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field

DEFAULT_KALSHI_API_BASE = "https://api.elections.kalshi.com/trade-api/v2"


class KalshiMarketSnapshot(BaseModel):
    """Normalized snapshot of a Kalshi prediction market contract."""

    ticker: str
    tick_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    yes_bid: int = Field(0, description="Highest Yes bid in cents [1, 99]")
    yes_ask: int = Field(100, description="Lowest Yes ask in cents [1, 99]")
    last_price: int = Field(50, description="Last trade price in cents")
    volume_24h: int = Field(0, description="Total contracts traded past 24 hours")
    open_interest: int = Field(0, description="Total active open contracts")
    vwap_24h: float = Field(50.0, description="24-hour volume-weighted average price in cents")


class KalshiClient:
    """Kalshi public market client with offline mock fallback."""

    def __init__(self, base_url: str = DEFAULT_KALSHI_API_BASE, timeout: float = 8.0):
        self.base_url = base_url
        self.timeout = timeout

    async def fetch_market_snapshot(self, ticker: str) -> Optional[KalshiMarketSnapshot]:
        """Fetch real-time orderbook and 24h volume for a public market ticker."""
        url = f"{self.base_url}/markets/{ticker}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return None
                data = resp.json().get("market", {})
                return self._parse_market_data(ticker, data)
            except Exception:
                return None

    def _parse_market_data(self, ticker: str, data: Dict[str, Any]) -> KalshiMarketSnapshot:
        """Parse raw Kalshi API response into a normalized snapshot."""
        yes_bid = data.get("yes_bid") or 0
        yes_ask = data.get("yes_ask") or 100
        last_price = data.get("last_price") or ((yes_bid + yes_ask) // 2)
        volume_24h = data.get("volume_24h") or data.get("volume") or 0
        open_interest = data.get("open_interest") or 0
        vwap = float(data.get("vwap_24h") or last_price)

        return KalshiMarketSnapshot(
            ticker=ticker,
            yes_bid=yes_bid,
            yes_ask=yes_ask,
            last_price=last_price,
            volume_24h=volume_24h,
            open_interest=open_interest,
            vwap_24h=vwap,
        )

    def generate_synthetic_snapshot(
        self,
        ticker: str,
        implied_probability: float = 0.52,
        volume: int = 6500,
        spread: int = 2,
    ) -> KalshiMarketSnapshot:
        """Generate deterministic synthetic orderbook snapshot for testing and demos."""
        mid_cents = int(round(implied_probability * 100))
        half_spread = max(1, spread // 2)
        yes_bid = max(1, min(98, mid_cents - half_spread))
        yes_ask = max(yes_bid + 1, min(99, mid_cents + half_spread))

        return KalshiMarketSnapshot(
            ticker=ticker,
            yes_bid=yes_bid,
            yes_ask=yes_ask,
            last_price=mid_cents,
            volume_24h=volume,
            open_interest=int(volume * 1.5),
            vwap_24h=float(mid_cents),
        )
