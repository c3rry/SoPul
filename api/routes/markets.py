"""Pulse2026 Prediction Market Divergence & Arbitrage Radar REST Endpoints."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import KalshiTick, Race, RaceForecast
from features.kalshi_pricing import evaluate_arbitrage_divergence

router = APIRouter(prefix="/markets", tags=["markets"])


class DivergenceItem(BaseModel):
    race_id: str
    ticker: str
    model_win_prob: float
    kalshi_win_prob: float
    delta_arb: float
    liquidity_weight: float
    volume_24h: int
    status: str
    alert: bool


class MarketDivergenceResponse(BaseModel):
    opportunities_count: int
    alerts_count: int
    items: list[DivergenceItem]


@router.get("/divergence", response_model=MarketDivergenceResponse)
async def get_market_divergence(
    threshold: float = Query(0.08, ge=0.01, le=0.50),
    min_liquidity: float = Query(0.40, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
):
    """Return positional arbitrage signals where model deviates from Kalshi contracts."""
    stmt = select(Race)
    result = await db.execute(stmt)
    races = result.scalars().all()

    items: list[DivergenceItem] = []
    alerts_count = 0

    for r in races:
        if not r.kalshi_market_ticker:
            continue

        # Fetch latest model forecast
        fc_stmt = (
            select(RaceForecast)
            .where(RaceForecast.race_id == r.race_id)
            .order_by(desc(RaceForecast.forecast_time))
            .limit(1)
        )
        fc_res = await db.execute(fc_stmt)
        fc = fc_res.scalar_one_or_none()

        # Fetch latest Kalshi tick
        tick_stmt = (
            select(KalshiTick)
            .where(KalshiTick.ticker == r.kalshi_market_ticker)
            .order_by(desc(KalshiTick.tick_time))
            .limit(1)
        )
        tick_res = await db.execute(tick_stmt)
        tick = tick_res.scalar_one_or_none()

        model_prob = fc.dem_win_prob if fc else 0.50
        kalshi_prob = (tick.last_price / 100.0) if tick else 0.50
        l_r = tick.liquidity_weight if tick else 0.50
        vol_24h = tick.volume_24h if tick else 5000

        div = evaluate_arbitrage_divergence(
            model_win_prob=model_prob,
            kalshi_win_prob=kalshi_prob,
            liquidity_weight=l_r,
            hourly_volume=vol_24h // 24,
            volume_24h_ma=vol_24h / 24.0,
            threshold=threshold,
            min_liquidity=min_liquidity,
        )

        if div["alert"]:
            alerts_count += 1

        items.append(
            DivergenceItem(
                race_id=r.race_id,
                ticker=r.kalshi_market_ticker,
                model_win_prob=round(model_prob, 4),
                kalshi_win_prob=round(kalshi_prob, 4),
                delta_arb=div["delta_arb"],
                liquidity_weight=round(l_r, 4),
                volume_24h=vol_24h,
                status=div["status"],
                alert=div["alert"],
            )
        )

    return MarketDivergenceResponse(
        opportunities_count=len(items),
        alerts_count=alerts_count,
        items=items,
    )
