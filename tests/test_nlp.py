"""Pulse2026 NLP Pipeline Unit Tests."""

import torch

from nlp.dataset import generate_synthetic_nlp_batch
from nlp.entity_linker import EntityLinker
from nlp.inference import NLPInferencePipeline
from nlp.model import DebertaDualHeadClassifier
from nlp.train import evaluate_batch, train_step


def test_model_forward_pass_dimensions():
    """Verify dual head output dimensions and value ranges."""
    model = DebertaDualHeadClassifier(pretrained=False)
    batch = generate_synthetic_nlp_batch(batch_size=3, seq_length=32)

    y_hat_ideo, z_stance = model(batch["input_ids"], batch["attention_mask"])

    # Head 1: Ideological framing regression in [-1.0, +1.0]
    assert y_hat_ideo.shape == (3,)
    assert torch.all(y_hat_ideo >= -1.0) and torch.all(y_hat_ideo <= 1.0)

    # Head 2: Raw linear logits for 3-class stance
    assert z_stance.shape == (3, 3)

    # Derived continuous stance in [-1.0, +1.0]
    stance_score = model.compute_continuous_stance(z_stance)
    assert stance_score.shape == (3,)
    assert torch.all(stance_score >= -1.0) and torch.all(stance_score <= 1.0)


def test_multitask_loss_and_training_step():
    """Verify multi-task loss calculation and gradient backprop."""
    model = DebertaDualHeadClassifier(pretrained=False)
    batch = generate_synthetic_nlp_batch(batch_size=2, seq_length=16)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)

    loss_val = train_step(model, batch, optimizer, device=torch.device("cpu"))
    assert isinstance(loss_val, float)
    assert loss_val > 0.0

    eval_metrics = evaluate_batch(model, batch, device=torch.device("cpu"))
    assert "ideo_mae" in eval_metrics
    assert "stance_accuracy" in eval_metrics


def test_multi_candidate_entity_linking():
    """Verify Aho-Corasick linker detects multiple candidates in a comparative political debate."""
    races = [
        {
            "race_id": "2026_SEN_GA",
            "candidates": [
                {
                    "candidate_id": "jon_ossoff",
                    "full_name": "Jon Ossoff",
                    "party": "DEM",
                    "keywords": ["ossoff", "jon ossoff"],
                    "official_handles": ["@ossoff"],
                },
                {
                    "candidate_id": "brian_kemp",
                    "full_name": "Brian Kemp",
                    "party": "REP",
                    "keywords": ["kemp", "brian kemp"],
                    "official_handles": ["@briankempga"],
                },
            ],
        }
    ]
    linker = EntityLinker(races)
    text = "In tonight's debate, Jon Ossoff clashed sharply with Governor Brian Kemp over the state budget."

    mentions = linker.extract_mentions(text)
    assert len(mentions) == 2
    cand_ids = {m.candidate_id for m in mentions}
    assert cand_ids == {"jon_ossoff", "brian_kemp"}


def test_inference_pipeline_dto_output():
    """Verify inference pipeline produces pure DTOs without database coupling."""
    pipeline = NLPInferencePipeline()
    items = [
        {
            "post_id": "test_post_1",
            "candidate_id": "jon_ossoff",
            "race_id": "2026_SEN_GA",
            "candidate_name": "Jon Ossoff",
            "party": "DEM",
            "caption": "Ossoff rallies supporters in Atlanta",
            "transcript": "We are fighting for working families across Georgia.",
        }
    ]

    results = pipeline.predict(items)
    assert len(results) == 1
    res = results[0]
    assert res.post_id == "test_post_1"
    assert res.candidate_id == "jon_ossoff"
    assert -1.0 <= res.ideology_score <= 1.0
    assert -1.0 <= res.stance_score <= 1.0
    assert len(res.stance_probs) == 3
