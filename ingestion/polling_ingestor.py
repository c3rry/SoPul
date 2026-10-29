"""Pulse2026 Public Polling Ingestor & Synthetic Dataset Generator."""

import csv
import io
import random
from datetime import date, datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field


class NormalizedPoll(BaseModel):
    """Standardized election poll record."""

    poll_id: str
    race_id: str
    pollster: str
    pollster_rating: float = Field(1.0, ge=0.5, le=1.5)
    start_date: date | None = None
    end_date: date
    sample_size: int = Field(..., ge=100)
    population_type: str = Field("LV", description="LV (Likely Voters), RV (Registered), A (Adults)")
    dem_pct: float
    rep_pct: float
    undecided_pct: float = 0.0


class PollingIngestor:
    """Parser and normalizer for CSV/JSON public polling feeds."""

    @staticmethod
    def parse_csv(csv_content: str) -> list[NormalizedPoll]:
        """Parse raw CSV polling data into normalized polling records."""
        reader = csv.DictReader(io.StringIO(csv_content))
        polls: list[NormalizedPoll] = []

        for idx, row in enumerate(reader):
            try:
                poll_id = row.get("poll_id") or f"csv_poll_{idx}_{int(datetime.now().timestamp())}"
                race_id = row["race_id"].strip()
                pollster = row.get("pollster", "Generic Pollster").strip()
                rating = float(row.get("pollster_rating", 1.0))
                end_date_str = row["end_date"].strip()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

                start_date = None
                if row.get("start_date"):
                    start_date = datetime.strptime(row["start_date"].strip(), "%Y-%m-%d").date()

                sample_size = int(row.get("sample_size", 800))
                population = row.get("population_type", "LV").strip().upper()
                dem_pct = float(row["dem_pct"])
                rep_pct = float(row["rep_pct"])
                undecided_pct = float(row.get("undecided_pct", 100.0 - dem_pct - rep_pct))

                polls.append(
                    NormalizedPoll(
                        poll_id=poll_id,
                        race_id=race_id,
                        pollster=pollster,
                        pollster_rating=rating,
                        start_date=start_date,
                        end_date=end_date,
                        sample_size=sample_size,
                        population_type=population,
                        dem_pct=dem_pct,
                        rep_pct=rep_pct,
                        undecided_pct=max(0.0, undecided_pct),
                    )
                )
            except Exception:
                continue

        return polls

    @staticmethod
    def generate_synthetic_polls(
        races: list[dict[str, Any]],
        num_polls_per_race: int = 5,
        reference_date: date | None = None,
    ) -> list[NormalizedPoll]:
        """Generate realistic synthetic 2026 battleground polls for testing and demonstrations."""
        ref = reference_date or date.today()
        polls: list[NormalizedPoll] = []
        pollsters = [
            ("Marist College", 1.3),
            ("Monmouth University", 1.2),
            ("Siena College/NYT", 1.4),
            ("Quinnipiac University", 1.1),
            ("Emerson College", 1.0),
            ("YouGov/CBS", 1.1),
            ("Morning Consult", 0.9),
            ("Trafalgar Group", 0.8),
        ]

        for race in races:
            race_id = race.get("race_id", "2026_SEN_GA")
            lean = race.get("historical_lean", 0.0)

            for i in range(num_polls_per_race):
                pollster_name, rating = random.choice(pollsters)
                days_ago = random.randint(1, 28)
                poll_end = ref - timedelta(days=days_ago)
                poll_start = poll_end - timedelta(days=random.randint(3, 5))
                sample_size = random.randint(600, 1800)
                pop_type = random.choice(["LV", "LV", "RV"])

                # Center synthetic margin on historical lean + random polling noise
                simulated_margin = lean + random.gauss(0, 2.5)
                base_dem = 48.0 + (simulated_margin / 2.0)
                base_rep = 48.0 - (simulated_margin / 2.0)
                undecided = max(2.0, 100.0 - base_dem - base_rep)

                polls.append(
                    NormalizedPoll(
                        poll_id=f"synth_{race_id}_{i}_{int(datetime.now().timestamp())}",
                        race_id=race_id,
                        pollster=pollster_name,
                        pollster_rating=rating,
                        start_date=poll_start,
                        end_date=poll_end,
                        sample_size=sample_size,
                        population_type=pop_type,
                        dem_pct=round(base_dem, 1),
                        rep_pct=round(base_rep, 1),
                        undecided_pct=round(undecided, 1),
                    )
                )

        return polls
