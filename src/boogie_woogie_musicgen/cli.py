"""Command-line entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

from .generator import DEFAULT_MODEL, MAX_SECONDS, generate_audio
from .prompting import PRESETS, build_prompt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a short Boogie-Woogie WAV with pretrained MusicGen."
    )
    parser.add_argument("--prompt", help="Use a custom prompt instead of a preset.")
    parser.add_argument("--preset", choices=sorted(PRESETS), default="classic-honky-tonk")
    parser.add_argument("--notes", default="", help="Extra direction appended to the preset.")
    parser.add_argument("--seconds", type=int, default=11, help=f"1–{MAX_SECONDS} seconds (11 gives at least 10s of MusicGen audio).")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--device", default="auto", help="auto, cpu, cuda, or mps.")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-k", type=int, default=250)
    parser.add_argument("--guidance-scale", type=float, default=3.0)
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/boogie-woogie-demo.wav")
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prompt = args.prompt.strip() if args.prompt else build_prompt(args.preset, args.notes)
    wav_path, metadata_path = generate_audio(
        prompt=prompt,
        output_path=args.output,
        seconds=args.seconds,
        seed=args.seed,
        model_id=args.model,
        device=args.device,
        temperature=args.temperature,
        top_k=args.top_k,
        guidance_scale=args.guidance_scale,
    )
    print(f"Saved audio: {wav_path}")
    print(f"Saved recipe: {metadata_path}")


if __name__ == "__main__":
    main()
