"""Pulse2026 Batched NLP Inference Service (Decoupled from DB Sessions)."""

from typing import Any

import torch
from pydantic import BaseModel, Field

from nlp.dataset import SocialStanceDataset
from nlp.model import DebertaDualHeadClassifier


class InferenceResult(BaseModel):
    """Scored NLP output for a candidate mention in a social media post."""

    post_id: str
    candidate_id: str
    race_id: str
    ideology_score: float = Field(..., ge=-1.0, le=1.0, description="Ideology: -1.0=Left, 0.0=Neutral, +1.0=Right")
    stance_score: float = Field(..., ge=-1.0, le=1.0, description="Net stance: p(Favor) - p(Against)")
    stance_probs: dict[str, float] = Field(..., description="Class probabilities: against, neutral, favor")


class NLPInferencePipeline:
    """Batched forward evaluation engine returning pure inference DTOs."""

    def __init__(
        self,
        model: DebertaDualHeadClassifier | None = None,
        tokenizer: Any | None = None,
        device: torch.device | None = None,
    ):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = model or DebertaDualHeadClassifier(pretrained=False)
        self.model.to(self.device)
        self.model.eval()
        self.tokenizer = tokenizer

    def predict(self, items: list[dict[str, Any]]) -> list[InferenceResult]:
        """Perform batched inference across formatted candidate mention items."""
        if not items:
            return []

        dataset = SocialStanceDataset(items, tokenizer=self.tokenizer)
        results: list[InferenceResult] = []

        with torch.no_grad():
            for idx in range(len(dataset)):
                sample = dataset[idx]
                input_ids = sample["input_ids"].unsqueeze(0).to(self.device)
                attention_mask = sample["attention_mask"].unsqueeze(0).to(self.device)

                y_hat_ideo, z_stance = self.model(input_ids, attention_mask)
                probs = torch.softmax(z_stance, dim=-1).squeeze(0)

                p_against = float(probs[0].item())
                p_neutral = float(probs[1].item())
                p_favor = float(probs[2].item())
                net_stance = p_favor - p_against

                item = items[idx]
                results.append(
                    InferenceResult(
                        post_id=item["post_id"],
                        candidate_id=item["candidate_id"],
                        race_id=item["race_id"],
                        ideology_score=round(float(y_hat_ideo.squeeze().item()), 4),
                        stance_score=round(float(net_stance), 4),
                        stance_probs={
                            "against": round(p_against, 4),
                            "neutral": round(p_neutral, 4),
                            "favor": round(p_favor, 4),
                        },
                    )
                )

        return results
