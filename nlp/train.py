"""Pulse2026 DeBERTa-v3 Multi-Task Training Loop."""

import torch

from nlp.model import DebertaDualHeadClassifier


def train_step(
    model: DebertaDualHeadClassifier,
    batch: dict[str, torch.Tensor],
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    scaler: torch.amp.GradScaler | None = None,
    alpha_ideo: float = 0.4,
    beta_stance: float = 0.6,
) -> float:
    """Execute single multi-task training step with gradient update."""
    model.train()
    optimizer.zero_grad()

    input_ids = batch["input_ids"].to(device)
    attention_mask = batch.get("attention_mask")
    if attention_mask is not None:
        attention_mask = attention_mask.to(device)

    y_ideo = batch["y_ideo"].to(device)
    y_stance = batch["y_stance"].to(device)

    if scaler and device.type == "cuda":
        with torch.amp.autocast(device_type="cuda"):
            y_hat_ideo, z_stance = model(input_ids, attention_mask)
            loss = model.compute_multitask_loss(
                y_hat_ideo, y_ideo, z_stance, y_stance, alpha_ideo, beta_stance
            )
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
    else:
        y_hat_ideo, z_stance = model(input_ids, attention_mask)
        loss = model.compute_multitask_loss(
            y_hat_ideo, y_ideo, z_stance, y_stance, alpha_ideo, beta_stance
        )
        loss.backward()
        optimizer.step()

    return float(loss.item())


def evaluate_batch(
    model: DebertaDualHeadClassifier,
    batch: dict[str, torch.Tensor],
    device: torch.device,
) -> dict[str, float]:
    """Evaluate batch performance returning ideology MAE and stance accuracy."""
    model.eval()
    with torch.no_grad():
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch.get("attention_mask")
        if attention_mask is not None:
            attention_mask = attention_mask.to(device)

        y_ideo = batch["y_ideo"].to(device)
        y_stance = batch["y_stance"].to(device)

        y_hat_ideo, z_stance = model(input_ids, attention_mask)
        ideo_mae = torch.mean(torch.abs(y_hat_ideo - y_ideo)).item()

        preds = torch.argmax(z_stance, dim=-1)
        stance_acc = (preds == y_stance).float().mean().item()

    return {
        "ideo_mae": float(ideo_mae),
        "stance_accuracy": float(stance_acc),
    }
