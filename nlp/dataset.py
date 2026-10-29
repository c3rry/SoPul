"""Pulse2026 PyTorch Dataset and Synthetic Batch Generators."""

from typing import Any

import torch
from torch.utils.data import Dataset


def format_model_input_text(candidate_name: str, party: str, race_id: str, caption: str, transcript: str) -> str:
    """Format input string for DeBERTa dual-head sequence classification."""
    return f"Target Candidate: {candidate_name} ({party}, {race_id}) | Caption: {caption.strip()} | Transcript: {transcript.strip()}"


class SocialStanceDataset(Dataset):
    """PyTorch Dataset tokenizing formatted candidate mention sequences."""

    def __init__(
        self,
        samples: list[dict[str, Any]],
        tokenizer: Any | None = None,
        max_length: int = 512,
    ):
        self.samples = samples
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        item = self.samples[idx]
        text = format_model_input_text(
            candidate_name=item["candidate_name"],
            party=item["party"],
            race_id=item["race_id"],
            caption=item.get("caption", ""),
            transcript=item.get("transcript", ""),
        )

        if self.tokenizer:
            encoding = self.tokenizer(
                text,
                truncation=True,
                max_length=self.max_length,
                padding="max_length",
                return_tensors="pt",
            )
            input_ids = encoding["input_ids"].squeeze(0)
            attention_mask = encoding["attention_mask"].squeeze(0)
        else:
            # Deterministic character-level mapping for testing environments
            tokens = [min(ord(c), 999) for c in text[: self.max_length]]
            if len(tokens) < self.max_length:
                tokens += [0] * (self.max_length - len(tokens))
            input_ids = torch.tensor(tokens, dtype=torch.long)
            attention_mask = torch.tensor([1 if t > 0 else 0 for t in tokens], dtype=torch.long)

        result = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }

        if "y_ideo" in item:
            result["y_ideo"] = torch.tensor(item["y_ideo"], dtype=torch.float)
        if "y_stance" in item:
            result["y_stance"] = torch.tensor(item["y_stance"], dtype=torch.long)

        return result


def generate_synthetic_nlp_batch(batch_size: int = 4, seq_length: int = 64) -> dict[str, torch.Tensor]:
    """Generate deterministic synthetic batch tensors for unit and pipeline tests."""
    torch.manual_seed(42)
    input_ids = torch.randint(1, 999, (batch_size, seq_length), dtype=torch.long)
    attention_mask = torch.ones((batch_size, seq_length), dtype=torch.long)
    # y_ideo in [-1.0, +1.0]
    y_ideo = (torch.rand(batch_size) * 2.0) - 1.0
    # y_stance in {0, 1, 2}
    y_stance = torch.randint(0, 3, (batch_size,), dtype=torch.long)

    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "y_ideo": y_ideo,
        "y_stance": y_stance,
    }
