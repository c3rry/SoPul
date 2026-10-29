"""Pulse2026 Ingestion Abstract Base Class and Data Transfer Objects."""

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime

from pydantic import BaseModel, Field


def hash_author_handle(handle: str, official_handles: set[str] | None = None) -> str:
    """Hash non-public creator handles with SHA-256 for privacy.

    Official candidate accounts listed in configuration retain plain handles.
    """
    cleaned = handle.strip().lower()
    if official_handles and (cleaned in official_handles or handle in official_handles):
        return handle
    return hashlib.sha256(handle.encode("utf-8")).hexdigest()


class RawPost(BaseModel):
    """Normalized ingested social media post record."""

    post_id: str = Field(..., description="Unique platform-scoped post identifier")
    platform: str = Field(..., description="Source platform name: youtube, tiktok, bluesky, reddit")
    author_handle: str = Field(..., description="Raw creator handle or username")
    author_handle_hash: str | None = Field(None, description="SHA-256 hashed handle for non-public creators")
    published_at: datetime = Field(..., description="Publication timestamp with timezone")
    caption: str | None = Field("", description="Post text caption or submission title")
    transcript: str | None = Field("", description="Cleaned spoken transcript or body text")
    raw_url: str | None = Field("", description="Canonical web URL to source post")

    def model_post_init(self, __context) -> None:
        if not self.author_handle_hash:
            self.author_handle_hash = hash_author_handle(self.author_handle)


class PostMetadata(BaseModel):
    """Dynamic engagement snapshot metrics."""

    views: int = Field(0, description="Video view count or approximated interaction views")
    likes: int = Field(0, description="Number of upvotes or likes")
    comments: int = Field(0, description="Number of comments/replies")
    shares: int = Field(0, description="Number of shares/retweets/reposts")


class SocialIngestor(ABC):
    """Abstract interface for all zero-cost platform ingestors."""

    @abstractmethod
    async def fetch_recent_posts(self, since: datetime) -> list[RawPost]:
        """Fetch newly published posts since the given timestamp without commercial API fees."""

    @abstractmethod
    async def extract_metadata(self, url: str) -> PostMetadata:
        """Fetch latest engagement counters for a specific post URL."""
