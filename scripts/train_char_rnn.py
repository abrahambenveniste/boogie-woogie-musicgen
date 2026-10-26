"""Train a small PyTorch character LSTM on the MIDI tick/pitch corpus."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import random
from datetime import datetime, timezone
from pathlib import Path

import torch
from torch import nn

from boogie_woogie_musicgen.symbolic import corpus_records


class CharacterLSTM(nn.Module):
    def __init__(self, vocabulary_size: int, embedding_size: int, hidden_size: int, layers: int):
        super().__init__()
        self.embedding = nn.Embedding(vocabulary_size, embedding_size)
        self.recurrent = nn.LSTM(
            embedding_size,
            hidden_size,
            num_layers=layers,
            batch_first=True,
            dropout=0.1 if layers > 1 else 0.0,
        )
        self.output = nn.Linear(hidden_size, vocabulary_size)

    def forward(self, tokens: torch.Tensor, hidden=None):
        embedded = self.embedding(tokens)
        states, hidden = self.recurrent(embedded, hidden)
        return self.output(states), hidden


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/processed/training_data_duration.txt"))
    parser.add_argument("--checkpoint", type=Path, default=Path("models/boogie-char-lstm-duration.pt"))
    parser.add_argument("--log", type=Path, default=Path("outputs/symbolic/training-loss-duration.csv"))
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--sequence-length", type=int, default=128)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--embedding-size", type=int, default=32)
    parser.add_argument("--hidden-size", type=int, default=96)
    parser.add_argument("--layers", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=0.002)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="auto", choices=("auto", "cpu", "cuda"))
    args = parser.parse_args()
    if args.steps < 1 or args.sequence_length < 4 or args.batch_size < 1:
        raise SystemExit("Steps, batch size, and sequence length must be positive.")

    corpus_bytes = args.input.read_bytes()
    corpus = corpus_bytes.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    records = corpus_records(corpus)
    if not records:
        raise SystemExit("Training corpus contains no valid MIDI records.")
    characters = sorted(set(corpus))
    char_to_id = {character: index for index, character in enumerate(characters)}
    ids = torch.tensor([char_to_id[character] for character in corpus], dtype=torch.long)
    if len(ids) <= args.sequence_length + 1:
        raise SystemExit("Corpus is shorter than the configured sequence length.")

    pitch_tokens = sorted({token for _, _, sequence in records for token in sequence if token != " "})
    corpus_metadata_path = args.input.with_suffix(".json")
    corpus_metadata = (
        json.loads(corpus_metadata_path.read_text(encoding="utf-8"))
        if corpus_metadata_path.is_file()
        else {}
    )
    device = (
        "cuda"
        if args.device == "auto" and torch.cuda.is_available()
        else ("cpu" if args.device == "auto" else args.device)
    )
    if device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA was requested but is not available.")
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
    torch.set_num_threads(max(1, min(4, torch.get_num_threads())))
    randomizer = random.Random(args.seed)

    model = CharacterLSTM(
        vocabulary_size=len(characters),
        embedding_size=args.embedding_size,
        hidden_size=args.hidden_size,
        layers=args.layers,
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    criterion = nn.CrossEntropyLoss()
    data = ids.to(device)
    offsets = torch.arange(args.sequence_length, device=device)
    losses: list[tuple[int, float]] = []
    model.train()

    for step in range(1, args.steps + 1):
        starts = [
            randomizer.randrange(0, len(ids) - args.sequence_length - 1)
            for _ in range(args.batch_size)
        ]
        positions = torch.tensor(starts, device=device).unsqueeze(1) + offsets
        inputs = data[positions]
        targets = data[positions + 1]
        optimizer.zero_grad(set_to_none=True)
        logits, _ = model(inputs)
        loss = criterion(logits.reshape(-1, len(characters)), targets.reshape(-1))
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        value = float(loss.detach().cpu())
        losses.append((step, value))
        if step == 1 or step % 50 == 0 or step == args.steps:
            print(f"step {step:5d}/{args.steps}  cross_entropy={value:.4f}")

    args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
    args.log.parent.mkdir(parents=True, exist_ok=True)
    config = {
        "vocabulary_size": len(characters),
        "embedding_size": args.embedding_size,
        "hidden_size": args.hidden_size,
        "layers": args.layers,
    }
    checkpoint = {
        "architecture": "character_lstm_v1",
        "model_config": config,
        "model_state_dict": model.cpu().state_dict(),
        "vocabulary": characters,
        "pitch_tokens": pitch_tokens,
        "note_encoding": corpus_metadata.get("note_encoding", "onset"),
        "grid_ticks_per_slot": corpus_metadata.get("grid_ticks_per_slot", 1),
        "pitch_token_encoding": corpus_metadata.get(
            "pitch_token_encoding", "Latin-1 one-byte characters using chr(33 + MIDI pitch)"
        ),
        "corpus_sha256": hashlib.sha256(corpus_bytes).hexdigest(),
        "corpus_characters": len(corpus),
        "first_record": list(records[0][:2]),
        "training": {
            "steps": args.steps,
            "sequence_length": args.sequence_length,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
            "seed": args.seed,
            "device": device,
            "final_cross_entropy": losses[-1][1],
        },
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    torch.save(checkpoint, args.checkpoint)
    with args.log.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["step", "cross_entropy"])
        writer.writerows((step, f"{loss:.6f}") for step, loss in losses)
    metadata_path = args.checkpoint.with_suffix(".json")
    metadata_path.write_text(json.dumps({k: v for k, v in checkpoint.items() if k != "model_state_dict"}, indent=2) + "\n", encoding="utf-8")
    print(f"Checkpoint: {args.checkpoint}")
    print(f"Checkpoint metadata: {metadata_path}")
    print(f"Training log: {args.log}")


if __name__ == "__main__":
    main()
