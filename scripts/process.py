"""Create a rag-shenanigann-style character corpus from Type-0 MIDI files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
from pathlib import Path

from boogie_woogie_musicgen.symbolic import encode_midi_file, require_program


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/normalized_midi"))
    parser.add_argument(
        "--output", type=Path, default=Path("data/processed/training_data.txt")
    )
    parser.add_argument(
        "--manifest", type=Path, default=Path("data/processed/processing_manifest.csv")
    )
    parser.add_argument(
        "--metadata", type=Path, default=Path("data/processed/training_data.json")
    )
    parser.add_argument("--midicsv", default="midicsv", help="Executable name or path.")
    parser.add_argument(
        "--midicsv-version",
        default="not-recorded",
        help="Version/distribution label for the externally installed MIDICSV utility.",
    )
    args = parser.parse_args()

    midi_paths = sorted(args.input.glob("*.mid"))
    if not midi_paths:
        raise SystemExit(
            f"No MIDI files found in {args.input}. Run scripts/normalize_type0.py first."
        )

    blocks: list[str] = []
    rows: list[dict[str, object]] = []
    for midi_path in midi_paths:
        encoded = encode_midi_file(midi_path, args.midicsv)
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
                "positive_velocity_note_on_events": encoded.note_on_events,
                "encoded_sequence_characters": len(encoded.sequence),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="ascii", newline="\n") as handle:
        handle.write("\n\n\n".join(blocks) + "\n\n\n")
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    event_total = sum(int(row["positive_velocity_note_on_events"]) for row in rows)
    tick_total = sum(int(row["tick_slots"]) for row in rows)
    corpus_bytes = args.output.read_bytes()
    midicsv_path = Path(require_program(args.midicsv))
    metadata = {
        "method": "MIDICSV Type-0 PPQN/tempo/pitch-per-tick text encoding",
        "input_directory": args.input.as_posix(),
        "midicsv_command": args.midicsv,
        "midicsv_version_label": args.midicsv_version,
        "midicsv_executable_sha256": hashlib.sha256(midicsv_path.read_bytes()).hexdigest(),
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
