"""Merge MIDI tracks to one Type-0 track before reference-style processing."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
from pathlib import Path

import mido


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/raw_midi"))
    parser.add_argument("--output", type=Path, default=Path("data/normalized_midi"))
    parser.add_argument(
        "--manifest", type=Path, default=Path("data/processed/normalization_manifest.csv")
    )
    args = parser.parse_args()
    midi_paths = sorted(args.input.glob("*.mid"))
    if not midi_paths:
        raise SystemExit(f"No .mid files found in {args.input}.")
    args.output.mkdir(parents=True, exist_ok=True)
    manifest_rows = []

    for source in midi_paths:
        midi = mido.MidiFile(source)
        merged = mido.MidiFile(type=0, ticks_per_beat=midi.ticks_per_beat)
        merged.tracks.append(mido.merge_tracks(midi.tracks))
        destination = args.output / source.name
        merged.save(destination)
        check = mido.MidiFile(destination)
        if check.type != 0 or len(check.tracks) != 1:
            raise RuntimeError(f"Type-0 normalization failed for {source.name}.")
        manifest_rows.append(
            {
                "source_file": source.name,
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "source_format": midi.type,
                "source_track_count": len(midi.tracks),
                "ticks_per_beat": midi.ticks_per_beat,
                "normalized_file": destination.name,
                "normalized_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                "normalized_format": check.type,
                "normalized_track_count": len(check.tracks),
                "mido_version": importlib.metadata.version("mido"),
            }
        )
        print(
            f"{source.name}: format {midi.type}, {len(midi.tracks)} track(s) -> "
            f"Type 0, 1 track ({destination})"
        )

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manifest_rows[0]))
        writer.writeheader()
        writer.writerows(manifest_rows)
    print(f"Normalization manifest: {args.manifest}")


if __name__ == "__main__":
    main()
