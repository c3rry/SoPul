"""Pulse2026 Zero-Cost Ingestion Package."""

from ingestion.base import PostMetadata, RawPost, SocialIngestor, hash_author_handle
from ingestion.bluesky_firehose import BlueskyFirehoseIngestor
from ingestion.kalshi_client import KalshiClient, KalshiMarketSnapshot
from ingestion.polling_ingestor import NormalizedPoll, PollingIngestor
from ingestion.reddit_stream import RedditStreamIngestor
from ingestion.tiktok_extractor import TikTokExtractor
from ingestion.whisper_fallback import EphemeralWhisperTranscriber
from ingestion.youtube_rss import YouTubeRSSIngestor, clean_vtt_subtitles

__all__ = [
    "RawPost",
    "PostMetadata",
    "SocialIngestor",
    "hash_author_handle",
    "YouTubeRSSIngestor",
    "clean_vtt_subtitles",
    "TikTokExtractor",
    "EphemeralWhisperTranscriber",
    "BlueskyFirehoseIngestor",
    "RedditStreamIngestor",
    "PollingIngestor",
    "NormalizedPoll",
    "KalshiClient",
    "KalshiMarketSnapshot",
]
