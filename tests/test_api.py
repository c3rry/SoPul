"""Pulse2026 FastAPI Serving Layer & Route Integration Tests."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.main import app
from api.scheduler import PipelineState, VelocityScheduler
from db.database import Base, get_db

TEST_SQLITE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_SQLITE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_root_endpoint():
    """Verify healthcheck and circuit breaker status from root endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "online"
        assert "circuit_breaker_state" in data
        assert data["social_layer_active"] is True


@pytest.mark.asyncio
async def test_races_list_endpoint():
    """Verify race cards and chamber control summaries."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/races")
        assert resp.status_code == 200
        data = resp.json()
        assert "races" in data
        assert "chamber_control" in data
        assert isinstance(data["races"], list)


@pytest.mark.asyncio
async def test_markets_divergence_endpoint():
    """Verify prediction market divergence radar returns opportunities and volume status."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/markets/divergence")
        assert resp.status_code == 200
        data = resp.json()
        assert "opportunities_count" in data
        assert "items" in data
        assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_pipeline_on_demand_trigger():
    """Verify POST /api/v1/pipeline/run executes forecasting cycle and updates records."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/pipeline/run")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["races_updated"] >= 0


def test_circuit_breaker_degradation_state_machine():
    """Verify circuit breaker trips to State 1 after 3 failures and recovers on success."""
    scheduler = VelocityScheduler(failure_threshold=3)
    assert scheduler.state == PipelineState.STATE_0_NOMINAL
    assert scheduler.is_social_active() is True

    # 1 failure: remains nominal
    scheduler.record_scraper_failure("youtube")
    assert scheduler.state == PipelineState.STATE_0_NOMINAL

    # 2 failures: remains nominal
    scheduler.record_scraper_failure("youtube")
    assert scheduler.state == PipelineState.STATE_0_NOMINAL

    # 3 failures: trips to State 1 (Social Degraded)
    scheduler.record_scraper_failure("youtube")
    assert scheduler.state == PipelineState.STATE_1_SOCIAL_DEGRADED
    assert scheduler.is_social_active() is False

    # Scraper recovers on 3 consecutive successes
    scheduler.record_scraper_success("youtube")
    assert scheduler.state == PipelineState.STATE_0_NOMINAL
    assert scheduler.is_social_active() is True
