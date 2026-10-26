"""Sample a MIDI tick/pitch stream from a trained character LSTM."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import torch

from train_char_rnn import CharacterLSTM


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=Path("models/boogie-char-lstm.pt"))
    parser.add_argument("--output", type=Path, default=Path("outputs/symbolic/boogie-rnn-demo.txt"))
    parser.add_argument("--ticks", type=int, default=4800, help="Tick slots to generate (4800 is 10s at 120 BPM and 480 PPQN).")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=73)
    parser.add_argument("--device", default="auto", choices=("auto", "cpu", "cuda"))
    args = parser.parse_args()
    if args.ticks < 2 or args.temperature <= 0:
        raise SystemExit("ticks must be at least 2 and temperature must be positive.")

    device = (
        "cuda"
        if args.device == "auto" and torch.cuda.is_available()
        else ("cpu" if args.device == "auto" else args.device)
    )
    if device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA was requested but is not available.")
    torch.manual_seed(args.seed)
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    vocabulary = checkpoint["vocabulary"]
    char_to_id = {character: index for index, character in enumerate(vocabulary)}
    model = CharacterLSTM(**checkpoint["model_config"])
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device).eval()

    pitch_tokens = checkpoint["pitch_tokens"]
    allowed_characters = [" ", *pitch_tokens]
    allowed_ids = torch.tensor(
        [char_to_id[character] for character in allowed_characters], dtype=torch.long, device=device
    )
    first_record = checkpoint.get("first_record")
    if first_record:
        ppqn, tempo = int(first_record[0]), int(first_record[1])
    else:
        # The processor preserves sorted file order; all bundled sources use 480 PPQN.
        ppqn, tempo = 480, 500000
    prefix = f"{ppqn}\n{tempo}\n"
    if any(character not in char_to_id for character in prefix):
        raise SystemExit("The model vocabulary does not contain the selected MIDI header.")

    prefix_ids = torch.tensor([[char_to_id[character] for character in prefix]], device=device)
    with torch.inference_mode():
        logits, hidden = model(prefix_ids)
        next_logits = logits[0, -1]
        generated: list[str] = []
        target_spaces = args.ticks - 1
        spaces = 0
        maximum_tokens = args.ticks * 5 + 1000
        for _ in range(maximum_tokens):
            filtered = torch.full_like(next_logits, float("-inf"))
            filtered[allowed_ids] = next_logits[allowed_ids] / args.temperature
            probabilities = torch.softmax(filtered, dim=-1)
            next_id = int(torch.multinomial(probabilities, 1).item())
            character = vocabulary[next_id]
            generated.append(character)
            if character == " ":
                spaces += 1
                if spaces >= target_spaces:
                    break
            next_input = torch.tensor([[next_id]], device=device)
            logits, hidden = model(next_input, hidden)
            next_logits = logits[0, -1]
        else:
            raise RuntimeError(
                "The sampler did not reach the requested number of tick slots. "
                "Try fewer ticks or train longer."
            )

    sequence = "".join(generated)
    text = prefix + sequence + "\n\n\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="ascii")
    metadata = {
        "method": "character-level LSTM over reference tick/pitch text",
        "checkpoint": str(args.checkpoint).replace("\\", "/"),
        "checkpoint_sha256": hashlib.sha256(args.checkpoint.read_bytes()).hexdigest(),
        "corpus_sha256": checkpoint["corpus_sha256"],
        "seed": args.seed,
        "temperature": args.temperature,
        "requested_tick_slots": args.ticks,
        "ppqn": ppqn,
        "tempo_us_per_quarter": tempo,
        "generated_characters": len(sequence),
        "generated_pitch_tokens": sum(character != " " for character in sequence),
        "device": device,
        "torch_version": torch.__version__,
        "python_version": platform.python_version(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "output_text": str(args.output).replace("\\", "/"),
    }
    args.output.with_suffix(".json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Generated text: {args.output}")
    print(f"Generation recipe: {args.output.with_suffix('.json')}")


if __name__ == "__main__":
    main()
