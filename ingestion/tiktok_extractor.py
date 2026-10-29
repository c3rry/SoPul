"""Pulse2026 TikTok Extractor ($0 Ingestion Cost with Anti-Ban Request Jitter)."""

import asyncio
import random
import re
from datetime import datetime, timezone
from typing import List, Optional
from yt_dlp import YoutubeDL

from ingestion.base import PostMetadata, RawPost, SocialIngestor

BOT_CHALLENGE_REGEX = re.compile(
    r"(verify you are human|cloudflare|sign in to continue|enable javascript|captcha|security check)",
    re.IGNORECASE,
)


class TikTokExtractor(SocialIngestor):
    """TikTok video metadata and subtitle scraper with request jitter."""

    def __init__(self, target_accounts: List[str], min_jitter: float = 3.5, max_jitter: float = 8.0):
        self.target_accounts = target_accounts
        self.min_jitter = min_jitter
        self.max_jitter = max_jitter

    async def _apply_jitter(self) -> None:
        """Enforce randomized sleep interval between sequential requests to evade rate limits."""
        delay = random.uniform(self.min_jitter, self.max_jitter)
        await asyncio.sleep(delay)

    def is_challenge_screen(self, text: str) -> bool:
        """Check if scraped content is a bot challenge or CAPTCHA screen."""
        return bool(BOT_CHALLENGE_REGEX.search(text))

    async def fetch_recent_posts(self, since: datetime) -> List[RawPost]:
        """Scrape recent public TikTok posts for target accounts."""
        posts: List[RawPost] = []
        for account in self.target_accounts:
            await self._apply_jitter()
            account_url = f"https://www.tiktok.com/@{account.lstrip('@')}"

            ydl_opts = {
                "skip_download": True,
                "extract_flat": "in_playlist",
                "playlistend": 10,
                "quiet": True,
                "no_warnings": True,
            }

            def _extract():
                try:
                    with YoutubeDL(ydl_opts) as ydl:
                        return ydl.extract_info(account_url, download=False)
                except Exception:
                    return None

            data = await asyncio.to_thread(_extract)
            if not data or "entries" not in data:
                continue

            for entry in data.get("entries", []):
                if not entry:
                    continue
                post_id = entry.get("id")
                if not post_id:
                    continue

                upload_date = entry.get("upload_date")  # YYYYMMDD
                if upload_date and len(upload_date) == 8:
                    try:
                        pub_dt = datetime.strptime(upload_date, "%Y%m%d").replace(tzinfo=timezone.utc)
                    except ValueError:
                        pub_dt = datetime.now(timezone.utc)
                else:
                    pub_dt = datetime.now(timezone.utc)

                if pub_dt < since:
                    continue

                caption = entry.get("title") or entry.get("description") or ""
                if self.is_challenge_screen(caption):
                    continue

                video_url = entry.get("url") or f"https://www.tiktok.com/@{account}/video/{post_id}"

                posts.append(
                    RawPost(
                        post_id=f"tt_{post_id}",
                        platform="tiktok",
                        author_handle=account,
                        published_at=pub_dt,
                        caption=caption,
                        transcript=caption,
                        raw_url=video_url,
                    )
                )

        return posts

    async def extract_metadata(self, url: str) -> PostMetadata:
        """Extract view and engagement metrics for a given TikTok post."""
        await self._apply_jitter()
        ydl_opts = {"skip_download": True, "quiet": True}

        def _get():
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return PostMetadata(
                        views=info.get("view_count") or 0,
                        likes=info.get("like_count") or 0,
                        comments=info.get("comment_count") or 0,
                        shares=info.get("repost_count") or 0,
                    )
            except Exception:
                return PostMetadata()

        return await asyncio.to_thread(_get)
