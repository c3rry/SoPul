"""Pulse2026 Race Forecast REST Endpoints."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import Race, RaceForecast

router = APIRouter(prefix="/races", tags=["races"])


class RaceCardResponse(BaseModel):
    race_id: str
    state: str
    chamber: str
    district: str | None = None
    historical_lean: float
    dem_win_prob: float
    rep_win_prob: float
    predicted_dem_margin: float
    ci_lower_90: float
    ci_upper_90: float
    poll_component_margin: float
    kalshi_component_margin: float
    social_component_shift: float


class ChamberSummary(BaseModel):
    p_house_dem_majority: float
    p_senate_dem_majority: float
    house_dem_seats_mean: float
    senate_dem_seats_mean: float


class RaceListResponse(BaseModel):
    races: list[RaceCardResponse]
    chamber_control: ChamberSummary


@router.get("", response_model=RaceListResponse)
async def get_all_races(db: AsyncSession = Depends(get_db)):
    """Return all tracked 2026 battleground races with latest forecast cards."""
    stmt = select(Race)
    result = await db.execute(stmt)
    races = result.scalars().all()

    race_cards: list[RaceCardResponse] = []
    for r in races:
        # Fetch latest forecast
        fc_stmt = (
            select(RaceForecast)
            .where(RaceForecast.race_id == r.race_id)
            .order_by(desc(RaceForecast.forecast_time))
            .limit(1)
        )
        fc_res = await db.execute(fc_stmt)
        fc = fc_res.scalar_one_or_none()

        if fc:
            card = RaceCardResponse(
                race_id=r.race_id,
                state=r.state,
                chamber=r.chamber,
                district=r.district,
                historical_lean=r.historical_lean,
                dem_win_prob=fc.dem_win_prob,
                rep_win_prob=fc.rep_win_prob,
                predicted_dem_margin=fc.predicted_dem_margin,
                ci_lower_90=fc.ci_lower_90,
                ci_upper_90=fc.ci_upper_90,
                poll_component_margin=fc.poll_component_margin,
                kalshi_component_margin=fc.kalshi_component_margin,
                social_component_shift=fc.social_component_shift,
            )
        else:
            # Fallback baseline when no forecast runs exist
            dem_prob = 0.50 + (r.historical_lean * 0.05)
            card = RaceCardResponse(
                race_id=r.race_id,
                state=r.state,
                chamber=r.chamber,
                district=r.district,
                historical_lean=r.historical_lean,
                dem_win_prob=round(max(0.01, min(0.99, dem_prob)), 4),
                rep_win_prob=round(1.0 - max(0.01, min(0.99, dem_prob)), 4),
                predicted_dem_margin=r.historical_lean,
                ci_lower_90=r.historical_lean - 7.5,
                ci_upper_90=r.historical_lean + 7.5,
                poll_component_margin=r.historical_lean,
                kalshi_component_margin=r.historical_lean,
                social_component_shift=0.0,
            )
        race_cards.append(card)

    chamber = ChamberSummary(
        p_house_dem_majority=0.48,
        p_senate_dem_majority=0.52,
        house_dem_seats_mean=216.5,
        senate_dem_seats_mean=50.2,
    )

    return RaceListResponse(races=race_cards, chamber_control=chamber)


@router.get("/{race_id}/timeseries")
async def get_race_timeseries(race_id: str, days: int = Query(30, ge=1, le=90), db: AsyncSession = Depends(get_db)):
    """Return historical probability curves and margins for a specific race."""
    stmt = (
        select(RaceForecast)
        .where(RaceForecast.race_id == race_id)
        .order_by(desc(RaceForecast.forecast_time))
        .limit(days)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    if not records:
        # Return fallback series
        return {
            "race_id": race_id,
            "days_tracked": 0,
            "timeseries": [],
        }

    timeseries = [
        {
            "forecast_time": r.forecast_time.isoformat(),
            "dem_win_prob": r.dem_win_prob,
            "rep_win_prob": r.rep_win_prob,
            "predicted_dem_margin": r.predicted_dem_margin,
            "ci_lower_90": r.ci_lower_90,
            "ci_upper_90": r.ci_upper_90,
            "poll_component_margin": r.poll_component_margin,
            "kalshi_component_margin": r.kalshi_component_margin,
            "social_component_shift": r.social_component_shift,
        }
        for r in reversed(records)
    ]

    return {
        "race_id": race_id,
        "days_tracked": len(timeseries),
        "timeseries": timeseries,
    }


@router.get("/{race_id}/drivers")
async def get_race_drivers(race_id: str, db: AsyncSession = Depends(get_db)):
    """Return closed-form feature attributions and driver narratives."""
    stmt = (
        select(RaceForecast)
        .where(RaceForecast.race_id == race_id)
        .order_by(desc(RaceForecast.forecast_time))
        .limit(1)
    )
    result = await db.execute(stmt)
    fc = result.scalar_one_or_none()

    if not fc:
        return {
            "race_id": race_id,
            "drivers": {},
            "narrative": "No historical forecast attributions recorded yet.",
        }

    attributions = fc.shap_attributions or {}
    narrative = attributions.get("narrative", f"Forecast driven by anchor margin of {fc.predicted_dem_margin:+.2f}%.")

    return {
        "race_id": race_id,
        "dem_win_prob": fc.dem_win_prob,
        "predicted_dem_margin": fc.predicted_dem_margin,
        "drivers": attributions,
        "narrative": narrative,
    }
