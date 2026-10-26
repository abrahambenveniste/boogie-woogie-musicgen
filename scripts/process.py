"""Create a rag-shenanigann-style character corpus from Type-0 MIDI files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
from pathlib import Path

from boogie_woogie_musicgen.symbolic import (
    encode_midi_file,
    encode_midi_file_duration,
    require_program,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/normalized_midi"))
    parser.add_argument(
        "--files",
        nargs="*",
        help="Optional MIDI basenames to process; by default, use every .mid file in the input folder.",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("data/processed/training_data_duration.txt")
    )
    parser.add_argument(
        "--manifest", type=Path, default=Path("data/processed/duration_processing_manifest.csv")
    )
    parser.add_argument(
        "--metadata", type=Path, default=Path("data/processed/training_data_duration.json")
    )
    parser.add_argument("--midicsv", default="midicsv", help="Executable name or path.")
    parser.add_argument(
        "--note-encoding",
        choices=("onset", "duration"),
        default="duration",
        help="onset reproduces the reference stream; duration records attack and hold tokens on a quantized grid.",
    )
    parser.add_argument(
        "--grid-ticks-per-slot",
        type=int,
        default=120,
        help="MIDI ticks represented by one generated slot in duration mode (120 is a sixteenth note at 480 PPQN).",
    )
    parser.add_argument(
        "--midicsv-version",
        default="not-recorded",
        help="Version/distribution label for the externally installed MIDICSV utility.",
    )
    args = parser.parse_args()

    midi_paths = sorted(args.input.glob("*.mid"))
    if args.files:
        requested = set(args.files)
        present = {path.name for path in midi_paths}
        missing = requested - present
        if missing:
            raise SystemExit(f"MIDI files not found in {args.input}: {', '.join(sorted(missing))}")
        midi_paths = [path for path in midi_paths if path.name in requested]
    if not midi_paths:
        raise SystemExit(
            f"No MIDI files found in {args.input}. Run scripts/normalize_type0.py first."
        )

    blocks: list[str] = []
    rows: list[dict[str, object]] = []
    for midi_path in midi_paths:
        encoded = (
            encode_midi_file(midi_path, args.midicsv)
            if args.note_encoding == "onset"
            else encode_midi_file_duration(midi_path, args.grid_ticks_per_slot)
        )
        blocks.append(
            f"{encoded.ppqn}\n{encoded.tempo_us_per_quarter}\n{encoded.sequence}"
        )
        rows.append(
            {
                "file": midi_path.name,
                "normalized_midi_sha256": hashlib.sha256(midi_path.read_bytes()).hexdigest(),
                "ppqn": encoded.ppqn,
                "tempo_us_per_quarter": encoded.tempo_us_per_quarter,
                "tick_slots": encoded.max_tick,
                "grid_ticks_per_slot": args.grid_ticks_per_slot if args.note_encoding == "duration" else 1,
                "positive_velocity_note_on_events": encoded.note_on_events,
                "encoded_sequence_characters": len(encoded.sequence),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output_encoding = "ascii" if args.note_encoding == "onset" else "utf-8"
    with args.output.open("w", encoding=output_encoding, newline="\n") as handle:
        handle.write("\n\n\n".join(blocks) + "\n\n\n")
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    event_total = sum(int(row["positive_velocity_note_on_events"]) for row in rows)
    tick_total = sum(int(row["tick_slots"]) for row in rows)
    corpus_bytes = args.output.read_bytes()
    midicsv_path = Path(require_program(args.midicsv)) if args.note_encoding == "onset" else None
    metadata = {
        "method": (
            "MIDICSV Type-0 PPQN/tempo/note-onset-per-tick text encoding"
            if args.note_encoding == "onset"
            else "Mido Type-0 duration-aware attack/hold tokens on a quantized grid"
        ),
        "note_encoding": args.note_encoding,
        "grid_ticks_per_slot": args.grid_ticks_per_slot if args.note_encoding == "duration" else 1,
        "pitch_token_encoding": (
            "ASCII attack tokens chr(33 + MIDI pitch)"
            if args.note_encoding == "onset"
            else "Unicode attack tokens chr(33 + pitch); hold tokens chr(256 + pitch)"
        ),
        "input_directory": args.input.as_posix(),
        "midicsv_command": args.midicsv if args.note_encoding == "onset" else None,
        "midicsv_version_label": args.midicsv_version if args.note_encoding == "onset" else None,
        "midicsv_executable_sha256": hashlib.sha256(midicsv_path.read_bytes()).hexdigest()
        if midicsv_path
        else None,
        "output_text": args.output.as_posix(),
        "output_sha256": hashlib.sha256(corpus_bytes).hexdigest(),
        "output_bytes": len(corpus_bytes),
        "input_files": rows,
        "file_count": len(rows),
        "total_tick_slots": tick_total,
        "positive_velocity_note_on_events": event_total,
        "python_version": platform.python_version(),
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Processed {len(rows)} Type-0 MIDI files.")
    print(f"Positive-velocity note-on events: {event_total:,}")
    print(f"Tick slots: {tick_total:,}")
    print(f"Training text: {args.output} ({args.output.stat().st_size:,} bytes)")
    print(f"Processing manifest: {args.manifest}")
    print(f"Corpus metadata: {args.metadata}")


if __name__ == "__main__":
    main()
