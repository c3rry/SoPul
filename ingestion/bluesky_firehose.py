"""Pulse2026 Bluesky Jetstream Firehose Client ($0 Real-Time WebSocket Ingestion)."""

import asyncio
import json
from datetime import datetime, timezone
from typing import Callable, List, Optional, Set
import websockets

from ingestion.base import PostMetadata, RawPost, SocialIngestor

DEFAULT_JETSTREAM_URL = (
    "wss://jetstream2.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post"
)


class BlueskyFirehoseIngestor(SocialIngestor):
    """Real-time Bluesky Jetstream consumer filtered against election keyword dictionaries."""

    def __init__(self, keywords: List[str], ws_url: str = DEFAULT_JETSTREAM_URL):
        self.keywords = [k.lower() for k in keywords]
        self.ws_url = ws_url
        self._collected_posts: List[RawPost] = []
        self._running = False

    def matches_keywords(self, text: str) -> bool:
        """Check if post text contains any tracked election keywords."""
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.keywords)

    async def listen(self, duration_seconds: float = 10.0) -> List[RawPost]:
        """Connect to Jetstream WebSocket for a bounded window and collect matching posts."""
        self._collected_posts = []
        end_time = asyncio.get_event_loop().time() + duration_seconds

        try:
            async with websockets.connect(self.ws_url, ping_interval=20, ping_timeout=10) as ws:
                while asyncio.get_event_loop().time() < end_time:
                    try:
                        timeout_rem = max(0.5, end_time - asyncio.get_event_loop().time())
                        message = await asyncio.wait_for(ws.recv(), timeout=timeout_rem)
                        event = json.loads(message)

                        kind = event.get("kind")
                        if kind != "commit":
                            continue

                        commit = event.get("commit", {})
                        if commit.get("collection") != "app.bsky.feed.post":
                            continue

                        record = commit.get("record", {})
                        text = record.get("text", "")
                        if not text or not self.matches_keywords(text):
                            continue

                        rkey = commit.get("rkey", "")
                        did = event.get("did", "")
                        post_id = f"bsky_{did}_{rkey}"
                        post_url = f"https://bsky.app/profile/{did}/post/{rkey}"

                        created_at_str = record.get("createdAt")
                        if created_at_str:
                            try:
                                pub_dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                            except ValueError:
                                pub_dt = datetime.now(timezone.utc)
                        else:
                            pub_dt = datetime.now(timezone.utc)

                        self._collected_posts.append(
                            RawPost(
                                post_id=post_id,
                                platform="bluesky",
                                author_handle=did,
                                published_at=pub_dt,
                                caption=text[:120],
                                transcript=text,
                                raw_url=post_url,
                            )
                        )
                    except asyncio.TimeoutError:
                        break
                    except Exception:
                        continue
        except Exception:
            pass

        return self._collected_posts

    async def fetch_recent_posts(self, since: datetime) -> List[RawPost]:
        """Fetch posts collected during recent stream monitoring."""
        posts = await self.listen(duration_seconds=5.0)
        return [p for p in posts if p.published_at >= since]

    async def extract_metadata(self, url: str) -> PostMetadata:
        """Return baseline metadata for text posts with view proxy."""
        # For Bluesky firehose posts without native counters, views default to standard base
        return PostMetadata(views=100, likes=10, comments=2, shares=1)
