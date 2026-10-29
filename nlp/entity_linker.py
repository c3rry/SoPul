"""Pulse2026 Aho-Corasick / Trie Candidate Entity Linker."""

import re
from typing import Any

from pydantic import BaseModel


class EntityMention(BaseModel):
    """Candidate entity mention detected in post text."""

    candidate_id: str
    candidate_name: str
    party: str
    race_id: str
    matched_keyword: str


class EntityLinker:
    """High-speed keyword matching engine linking social text mentions to target candidates."""

    def __init__(self, races: list[dict[str, Any]]):
        self.races = races
        self.keyword_map: dict[str, dict[str, str]] = {}
        self._build_keyword_index()

    def _build_keyword_index(self) -> None:
        """Index candidate names, nicknames, and handles into a normalized keyword dictionary."""
        for race in self.races:
            race_id = race.get("race_id", "")
            for cand in race.get("candidates", []):
                cand_id = cand["candidate_id"]
                cand_name = cand["full_name"]
                party = cand["party"]

                # Collect all aliases
                aliases = set(cand.get("keywords", []))
                aliases.add(cand_name)
                for handle in cand.get("official_handles", []):
                    aliases.add(handle.lstrip("@"))

                for alias in aliases:
                    cleaned = alias.strip().lower()
                    if len(cleaned) >= 3:  # ignore 1-2 char noise
                        self.keyword_map[cleaned] = {
                            "candidate_id": cand_id,
                            "candidate_name": cand_name,
                            "party": party,
                            "race_id": race_id,
                        }

        # Build combined regex with word boundaries
        escaped_keys = sorted(self.keyword_map.keys(), key=lambda k: len(k), reverse=True)
        pattern = r"\b(" + "|".join(re.escape(k) for k in escaped_keys) + r")\b"
        self._regex = re.compile(pattern, re.IGNORECASE)

    def extract_mentions(self, text: str) -> list[EntityMention]:
        """Extract all candidate mentions from text, deduplicated per candidate."""
        if not text:
            return []

        matches = self._regex.findall(text)
        seen_candidates: set[str] = set()
        mentions: list[EntityMention] = []

        for match in matches:
            kw = match.lower()
            if kw in self.keyword_map:
                info = self.keyword_map[kw]
                cand_id = info["candidate_id"]
                if cand_id not in seen_candidates:
                    seen_candidates.add(cand_id)
                    mentions.append(
                        EntityMention(
                            candidate_id=cand_id,
                            candidate_name=info["candidate_name"],
                            party=info["party"],
                            race_id=info["race_id"],
                            matched_keyword=match,
                        )
                    )

        return mentions
