"""SQLAlchemy Declarative Models for Pulse2026."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from db.database import Base


def utc_now() -> datetime:
    """Return current timestamp in UTC timezone."""
    return datetime.now(timezone.utc)


class Race(Base):
    __tablename__ = "races"

    race_id = Column(String(32), primary_key=True)
    state = Column(String(2), nullable=False)
    chamber = Column(String(16), nullable=False)  # Senate, House, Governor
    district = Column(String(8), nullable=True)
    historical_lean = Column(Float, nullable=False, default=0.0)
    kalshi_market_ticker = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    candidates = relationship("Candidate", back_populates="race", cascade="all, delete-orphan")
    polls = relationship("Poll", back_populates="race", cascade="all, delete-orphan")
    mentions = relationship("SocialPostMention", back_populates="race", cascade="all, delete-orphan")
    forecasts = relationship("RaceForecast", back_populates="race", cascade="all, delete-orphan")


class Candidate(Base):
    __tablename__ = "candidates"

    candidate_id = Column(String(64), primary_key=True)
    race_id = Column(String(32), ForeignKey("races.race_id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String(128), nullable=False)
    party = Column(String(16), nullable=False)  # DEM, REP, IND
    incumbent = Column(Boolean, nullable=False, default=False)
    keywords = Column(JSON, nullable=False, default=list)  # nick/search terms for Aho-Corasick
    official_handles = Column(JSON, nullable=False, default=list)  # whitelist exempt from SHA-256
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    race = relationship("Race", back_populates="candidates")
    mentions = relationship("SocialPostMention", back_populates="candidate", cascade="all, delete-orphan")


class SocialPost(Base):
    __tablename__ = "social_posts"

    post_id = Column(String(128), primary_key=True)
    platform = Column(String(32), nullable=False)  # youtube, tiktok, bluesky, reddit
    author_handle_hash = Column(String(64), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=False)
    caption = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    raw_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    mentions = relationship("SocialPostMention", back_populates="post", cascade="all, delete-orphan")
    snapshots = relationship("EngagementSnapshot", back_populates="post", cascade="all, delete-orphan")


class SocialPostMention(Base):
    __tablename__ = "social_post_mentions"

    post_id = Column(String(128), ForeignKey("social_posts.post_id", ondelete="CASCADE"), primary_key=True)
    candidate_id = Column(String(64), ForeignKey("candidates.candidate_id", ondelete="CASCADE"), primary_key=True)
    race_id = Column(String(32), ForeignKey("races.race_id", ondelete="CASCADE"), nullable=False)
    ideology_score = Column(Float, nullable=True)  # [-1.0, +1.0]
    stance_score = Column(Float, nullable=True)  # [-1.0, +1.0]
    comment_ratio_penalty = Column(Float, nullable=False, default=1.0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    post = relationship("SocialPost", back_populates="mentions")
    candidate = relationship("Candidate", back_populates="mentions")
    race = relationship("Race", back_populates="mentions")

    __table_args__ = (
        Index("idx_mentions_race", "race_id"),
        Index("idx_mentions_candidate", "candidate_id"),
    )


class Poll(Base):
    __tablename__ = "polls"

    poll_id = Column(String(128), primary_key=True)
    race_id = Column(String(32), ForeignKey("races.race_id", ondelete="CASCADE"), nullable=False)
    pollster = Column(String(128), nullable=False)
    pollster_rating = Column(Float, nullable=False, default=1.0)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=False)
    sample_size = Column(Integer, nullable=False)
    population_type = Column(String(8), nullable=False, default="LV")  # LV, RV, A
    dem_pct = Column(Float, nullable=False)
    rep_pct = Column(Float, nullable=False)
    undecided_pct = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    race = relationship("Race", back_populates="polls")

    __table_args__ = (
        Index("idx_polls_race_end_date", "race_id", "end_date"),
    )


class EngagementSnapshot(Base):
    __tablename__ = "engagement_snapshots"

    post_id = Column(String(128), ForeignKey("social_posts.post_id", ondelete="CASCADE"), primary_key=True)
    observed_at = Column(DateTime(timezone=True), primary_key=True, default=utc_now)
    views = Column(Integer, nullable=False, default=0)
    likes = Column(Integer, nullable=False, default=0)
    comments = Column(Integer, nullable=False, default=0)
    shares = Column(Integer, nullable=False, default=0)
    ewss_score = Column(Float, nullable=False, default=0.0)

    post = relationship("SocialPost", back_populates="snapshots")

    __table_args__ = (
        Index("idx_snapshots_post_observed", "post_id", "observed_at"),
    )


class KalshiTick(Base):
    __tablename__ = "kalshi_ticks"

    ticker = Column(String(64), primary_key=True)
    tick_time = Column(DateTime(timezone=True), primary_key=True, default=utc_now)
    yes_bid = Column(Integer, nullable=False, default=0)
    yes_ask = Column(Integer, nullable=False, default=0)
    last_price = Column(Integer, nullable=False, default=0)
    volume_24h = Column(Integer, nullable=False, default=0)
    open_interest = Column(Integer, nullable=False, default=0)
    vwap_24h = Column(Float, nullable=False, default=0.0)
    liquidity_weight = Column(Float, nullable=False, default=0.0)

    __table_args__ = (
        Index("idx_kalshi_ticks_ticker_time", "ticker", "tick_time"),
    )


class RaceForecast(Base):
    __tablename__ = "race_forecasts"

    race_id = Column(String(32), ForeignKey("races.race_id", ondelete="CASCADE"), primary_key=True)
    forecast_time = Column(DateTime(timezone=True), primary_key=True, default=utc_now)
    dem_win_prob = Column(Float, nullable=False)
    rep_win_prob = Column(Float, nullable=False)
    predicted_dem_margin = Column(Float, nullable=False)
    ci_lower_90 = Column(Float, nullable=False)
    ci_upper_90 = Column(Float, nullable=False)
    poll_component_margin = Column(Float, nullable=False)
    kalshi_component_margin = Column(Float, nullable=False)
    social_component_shift = Column(Float, nullable=False, default=0.0)
    shap_attributions = Column(JSON, nullable=False, default=dict)

    race = relationship("Race", back_populates="forecasts")

    __table_args__ = (
        Index("idx_forecasts_race_time", "race_id", "forecast_time"),
    )
