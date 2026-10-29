"""Pulse2026 Reddit Political Stream Ingestor ($0 Public JSON / AsyncPRAW Ingestion)."""

import asyncio
from datetime import datetime, timezone
from typing import List, Optional
import httpx

from ingestion.base import PostMetadata, RawPost, SocialIngestor


class RedditStreamIngestor(SocialIngestor):
    """Reddit political stream consumer using public unauthenticated endpoints."""

    def __init__(self, subreddits: List[str], keywords: List[str]):
        self.subreddits = subreddits
        self.keywords = [k.lower() for k in keywords]
        self.headers = {"User-Agent": "Pulse2026Bot/0.1 (election forecasting; zero commercial)"}

    def matches_keywords(self, text: str) -> bool:
        """Check if title or selftext contains tracked candidate or race keywords."""
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.keywords)

    async def fetch_subreddit_posts(self, subreddit: str, since: datetime) -> List[RawPost]:
        """Fetch newly published submissions from subreddit /new.json."""
        url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=25"
        posts: List[RawPost] = []

        async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return []
                data = resp.json()
            except Exception:
                return []

        children = data.get("data", {}).get("children", [])
        for child in children:
            post_data = child.get("data", {})
            created_utc = post_data.get("created_utc")
            if not created_utc:
                continue

            pub_dt = datetime.fromtimestamp(created_utc, tz=timezone.utc)
            if pub_dt < since:
                continue

            title = post_data.get("title", "")
            selftext = post_data.get("selftext", "")
            full_text = f"{title}\n{selftext}".strip()

            if not self.matches_keywords(full_text):
                continue

            post_id = post_data.get("id", "")
            author = post_data.get("author", "[deleted]")
            permalink = post_data.get("permalink", "")
            post_url = f"https://reddit.com{permalink}" if permalink else f"https://reddit.com/r/{subreddit}/comments/{post_id}"

            posts.append(
                RawPost(
                    post_id=f"rd_{post_id}",
                    platform="reddit",
                    author_handle=author,
                    published_at=pub_dt,
                    caption=title[:120],
                    transcript=full_text,
                    raw_url=post_url,
                )
            )

        return posts

    async def fetch_recent_posts(self, since: datetime) -> List[RawPost]:
        """Fetch posts across all registered subreddits."""
        tasks = [self.fetch_subreddit_posts(sub, since) for sub in self.subreddits]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        posts: List[RawPost] = []
        for r in results:
            if isinstance(r, list):
                posts.extend(r)
        return posts

    async def extract_metadata(self, url: str) -> PostMetadata:
        """Fetch score and comment counts via Reddit public JSON."""
        clean_url = url.rstrip("/") + ".json"
        async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
            try:
                resp = await client.get(clean_url)
                if resp.status_code == 200:
                    data = resp.json()
                    post_data = data[0]["data"]["children"][0]["data"]
                    score = post_data.get("score", 0)
                    num_comments = post_data.get("num_comments", 0)
                    # Text proxy heuristic: Views = 10 * (likes + comments)
                    proxy_views = max(score + num_comments, 1) * 10
                    return PostMetadata(views=proxy_views, likes=score, comments=num_comments, shares=0)
            except Exception:
                pass
        return PostMetadata(views=100, likes=10, comments=2, shares=0)
