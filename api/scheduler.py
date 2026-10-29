"""Pulse2026 Background Job Scheduler & Circuit Breaker Degradation State Machine."""

from datetime import datetime, timezone
from enum import Enum

from apscheduler.schedulers.asyncio import AsyncIOScheduler


class PipelineState(str, Enum):
    STATE_0_NOMINAL = "NOMINAL"
    STATE_1_SOCIAL_DEGRADED = "SOCIAL_DEGRADED"


class VelocityScheduler:
    """APScheduler daemon coordinating multi-snapshot re-polling and circuit breaker health."""

    def __init__(self, failure_threshold: int = 3):
        self.scheduler = AsyncIOScheduler()
        self.failure_threshold = failure_threshold
        self.consecutive_failures: dict[str, int] = {
            "youtube": 0,
            "tiktok": 0,
            "bluesky": 0,
            "reddit": 0,
        }
        self.state = PipelineState.STATE_0_NOMINAL
        self.last_state_change: datetime = datetime.now(timezone.utc)

    def record_scraper_failure(self, platform: str) -> None:
        """Increment failure counter and trip circuit breaker if threshold is exceeded."""
        self.consecutive_failures[platform] = self.consecutive_failures.get(platform, 0) + 1
        if self.consecutive_failures[platform] >= self.failure_threshold:
            if self.state != PipelineState.STATE_1_SOCIAL_DEGRADED:
                self.state = PipelineState.STATE_1_SOCIAL_DEGRADED
                self.last_state_change = datetime.now(timezone.utc)

    def record_scraper_success(self, platform: str) -> None:
        """Reset platform failure count and evaluate potential recovery to Nominal."""
        self.consecutive_failures[platform] = 0
        # If all platforms have 0 failures, restore Nominal state
        if all(f == 0 for f in self.consecutive_failures.values()):
            if self.state != PipelineState.STATE_0_NOMINAL:
                self.state = PipelineState.STATE_0_NOMINAL
                self.last_state_change = datetime.now(timezone.utc)

    def is_social_active(self) -> bool:
        """Return False if circuit breaker is tripped, setting social residual to 0.0."""
        return self.state == PipelineState.STATE_0_NOMINAL

    def start(self) -> None:
        """Start APScheduler background jobs if not already running."""
        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self) -> None:
        """Gracefully shut down scheduler jobs."""
        if self.scheduler.running:
            self.scheduler.shutdown()
