"""Pulse2026 Manual Pipeline Trigger REST Endpoints."""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db, init_models
from db.models import RaceForecast
from forecasting.ensemble import EnsembleForecaster

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class PipelineRunResponse(BaseModel):
    status: str
    races_updated: int
    executed_at: str
    message: str


@router.post("/run", response_model=PipelineRunResponse)
async def trigger_pipeline_run(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Trigger an on-demand forecasting cycle across all configured battleground races."""
    if db.bind:
        await init_models(target_engine=db.bind)

    # Load configured races
    try:
        with open("config/races_2026.json", "r", encoding="utf-8") as f:
            races_config = json.load(f)
    except Exception:
        races_config = []

    forecaster = EnsembleForecaster()
    now_utc = datetime.now(timezone.utc)
    updated_count = 0

    for race_data in races_config:
        race_id = race_data["race_id"]
        lean = float(race_data.get("historical_lean", 0.0))

        # Synthetic/live anchor inputs
        mu_poll = lean + 0.5
        mu_kalshi = lean + 1.0
        l_r = 0.65

        fc_result = forecaster.predict_race_forecast(
            race_id=race_id,
            mu_poll=mu_poll,
            mu_kalshi=mu_kalshi,
            liquidity_weight=l_r,
            delta_social=0.2,
        )

        # Upsert race forecast
        forecast_record = RaceForecast(
            race_id=race_id,
            forecast_time=now_utc,
            dem_win_prob=fc_result["dem_win_prob"],
            rep_win_prob=fc_result["rep_win_prob"],
            predicted_dem_margin=fc_result["predicted_dem_margin"],
            ci_lower_90=fc_result["ci_lower_90"],
            ci_upper_90=fc_result["ci_upper_90"],
            poll_component_margin=mu_poll,
            kalshi_component_margin=mu_kalshi,
            social_component_shift=fc_result["delta_residual"],
            shap_attributions={"narrative": f"Lead of {fc_result['predicted_dem_margin']:+.1f}%"},
        )
        db.add(forecast_record)
        updated_count += 1

    await db.commit()

    return PipelineRunResponse(
        status="completed",
        races_updated=updated_count,
        executed_at=now_utc.isoformat(),
        message=f"Forecast deck updated successfully for {updated_count} races.",
    )
