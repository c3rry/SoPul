"""Pulse2026 YouTube RSS Monitor & VTT Subtitle Extractor ($0 API Cost)."""

import asyncio
import re
from datetime import datetime, timezone

import feedparser
import httpx
from yt_dlp import YoutubeDL

from ingestion.base import PostMetadata, RawPost, SocialIngestor


def clean_vtt_subtitles(vtt_text: str) -> str:
    """Clean WebVTT transcript by stripping timestamps and deduplicating rolling lines."""
    lines = vtt_text.splitlines()
    cleaned_lines: list[str] = []
    prev_line = ""

    timestamp_regex = re.compile(
        r"^\d{2}:\d{2}(?::\d{2})?\.\d{3}\s+-->\s+\d{2}:\d{2}(?::\d{2})?\.\d{3}"
    )

    for line in lines:
        line = line.strip()
        # Skip header, empty lines, cue identifiers, and timestamp intervals
        if not line or line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if timestamp_regex.match(line) or line.isdigit():
            continue
        # Remove XML/HTML formatting tags (e.g., <c>, </c>, <00:00:01.000>)
        clean = re.sub(r"<[^>]+>", "", line).strip()
        if clean and clean != prev_line:
            cleaned_lines.append(clean)
            prev_line = clean

    return " ".join(cleaned_lines)


class YouTubeRSSIngestor(SocialIngestor):
    """Zero-quota YouTube monitor extracting Shorts from unauthenticated RSS feeds."""

    def __init__(self, channel_ids: list[str]):
        self.channel_ids = channel_ids
        self.ydl_opts = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en", "en-US", "en-GB"],
            "quiet": True,
            "no_warnings": True,
        }

    async def fetch_channel_feed(self, channel_id: str, since: datetime) -> list[RawPost]:
        """Fetch unauthenticated channel RSS feed and extract video metadata."""
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        posts: list[RawPost] = []

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return []
                feed = feedparser.parse(resp.text)
            except Exception:
                return []

        for entry in feed.entries:
            published_parsed = getattr(entry, "published_parsed", None)
            if published_parsed:
                pub_dt = datetime(*published_parsed[:6], tzinfo=timezone.utc)
            else:
                pub_dt = datetime.now(timezone.utc)

            if pub_dt < since:
                continue

            video_id = getattr(entry, "yt_videoid", None)
            if not video_id:
                # Fallback parse from link
                link = getattr(entry, "link", "")
                m = re.search(r"v=([a-zA-Z0-9_-]+)", link)
                video_id = m.group(1) if m else link

            title = getattr(entry, "title", "")
            author = getattr(entry, "author", channel_id)
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # Extract subtitles asynchronously
            transcript = await asyncio.to_thread(self._extract_transcript_ydl, video_url)

            posts.append(
                RawPost(
                    post_id=f"yt_{video_id}",
                    platform="youtube",
                    author_handle=author,
                    published_at=pub_dt,
                    caption=title,
                    transcript=transcript or title,
                    raw_url=video_url,
                )
            )

        return posts

    def _extract_transcript_ydl(self, video_url: str) -> str:
        """Download subtitle track without audio/video data."""
        try:
            with YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                subtitles = info.get("subtitles", {}) or info.get("automatic_captions", {})
                for lang in ["en", "en-US", "en-GB"]:
                    if lang in subtitles:
                        for fmt in subtitles[lang]:
                            if fmt.get("ext") == "vtt":
                                sub_url = fmt.get("url")
                                if sub_url:
                                    import urllib.request
                                    with urllib.request.urlopen(sub_url, timeout=5) as r:
                                        return clean_vtt_subtitles(r.read().decode("utf-8", errors="ignore"))
        except Exception:
            pass
        return ""

    async def fetch_recent_posts(self, since: datetime) -> list[RawPost]:
        """Fetch posts across all registered channel IDs."""
        tasks = [self.fetch_channel_feed(cid, since) for cid in self.channel_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        posts: list[RawPost] = []
        for r in results:
            if isinstance(r, list):
                posts.extend(r)
        return posts

    async def extract_metadata(self, url: str) -> PostMetadata:
        """Extract latest view and interaction metrics via yt-dlp."""
        def _get():
            opts = {"skip_download": True, "quiet": True}
            try:
                with YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return PostMetadata(
                        views=info.get("view_count") or 0,
                        likes=info.get("like_count") or 0,
                        comments=info.get("comment_count") or 0,
                        shares=0,
                    )
            except Exception:
                return PostMetadata()

        return await asyncio.to_thread(_get)
