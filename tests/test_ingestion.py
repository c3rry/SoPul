"""Pulse2026 Ingestion Unit Tests."""

from datetime import date, datetime, timezone
import pytest

from ingestion.base import RawPost, hash_author_handle
from ingestion.bluesky_firehose import BlueskyFirehoseIngestor
from ingestion.kalshi_client import KalshiClient
from ingestion.polling_ingestor import PollingIngestor
from ingestion.tiktok_extractor import TikTokExtractor
from ingestion.youtube_rss import clean_vtt_subtitles


def test_vtt_subtitle_cleaning():
    """Verify timestamps, cue numbers, XML tags, and duplicates are stripped."""
    sample_vtt = """WEBVTT
Kind: captions
Language: en

1
00:00:01.000 --> 00:00:03.000
<c>Georgia Senate</c> race is heating up.

2
00:00:03.000 --> 00:00:05.000
Georgia Senate race is heating up.

3
00:00:05.000 --> 00:00:07.500
Jon Ossoff faces a tough challenge.
"""
    cleaned = clean_vtt_subtitles(sample_vtt)
    assert "WEBVTT" not in cleaned
    assert "-->" not in cleaned
    assert "<c>" not in cleaned
    # Ensure deduplication: "Georgia Senate race is heating up." appears once
    assert cleaned.count("Georgia Senate race is heating up.") == 1
    assert "Jon Ossoff faces a tough challenge." in cleaned


def test_author_handle_hashing():
    """Verify SHA-256 hashing for non-public authors and plain preservation for candidates."""
    official_candidates = {"@ossoff", "@briankempga", "jonossoff"}

    # Non-public creator handle must be SHA-256 hashed (64 hex characters)
    hashed = hash_author_handle("random_voter_123", official_candidates)
    assert len(hashed) == 64
    assert hashed != "random_voter_123"

    # Official candidate handles must be preserved
    plain = hash_author_handle("@ossoff", official_candidates)
    assert plain == "@ossoff"


def test_raw_post_model_initialization():
    """Verify RawPost automatically computes author hash if omitted."""
    post = RawPost(
        post_id="test_1",
        platform="youtube",
        author_handle="political_analyst",
        published_at=datetime.now(timezone.utc),
        caption="Midterm breakdown",
        transcript="Key battleground Senate analysis.",
    )
    assert post.author_handle_hash is not None
    assert len(post.author_handle_hash) == 64


def test_synthetic_polling_generation():
    """Verify synthetic polling generates valid dates, sample sizes, and margins."""
    races = [{"race_id": "2026_SEN_GA", "historical_lean": 1.2}]
    polls = PollingIngestor.generate_synthetic_polls(races, num_polls_per_race=4, reference_date=date(2026, 10, 1))

    assert len(polls) == 4
    for poll in polls:
        assert poll.race_id == "2026_SEN_GA"
        assert poll.sample_size >= 100
        assert poll.pollster_rating >= 0.5
        assert 0.0 <= poll.dem_pct <= 100.0
        assert 0.0 <= poll.rep_pct <= 100.0
        assert poll.end_date <= date(2026, 10, 1)


def test_kalshi_synthetic_snapshot():
    """Verify Kalshi synthetic snapshot matches implied probability and bounds."""
    client = KalshiClient()
    snapshot = client.generate_synthetic_snapshot("KXSENGA26", implied_probability=0.55, volume=5000, spread=2)

    assert snapshot.ticker == "KXSENGA26"
    assert snapshot.last_price == 55
    assert snapshot.yes_bid < snapshot.yes_ask
    assert snapshot.volume_24h == 5000


def test_bluesky_keyword_matching():
    """Verify keyword filtering matches target candidates and issues."""
    ingestor = BlueskyFirehoseIngestor(keywords=["ossoff", "kemp", "midterms 2026"])
    assert ingestor.matches_keywords("Huge debate today between Ossoff and Kemp!") is True
    assert ingestor.matches_keywords("What should I have for dinner tonight?") is False


def test_tiktok_challenge_screen_detection():
    """Verify regex filters out bot challenge screens."""
    extractor = TikTokExtractor(target_accounts=["test"])
    assert extractor.is_challenge_screen("Please verify you are human to continue.") is True
    assert extractor.is_challenge_screen("Attention required! Cloudflare security check") is True
    assert extractor.is_challenge_screen("Exclusive interview with Georgia voters on the economy.") is False
