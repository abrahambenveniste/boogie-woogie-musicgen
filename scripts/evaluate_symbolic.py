#!/usr/bin/env python3
"""Write comparable, descriptive MIDI diagnostics for the source and generated scores."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

try:
    import mido
except ImportError as exc:  # pragma: no cover - exercised by the user-facing error
    raise SystemExit("Install the symbolic extra first: python -m pip install -e '.[symbolic]'") from exc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCES = ROOT / "data" / "normalized_midi"
DEFAULT_GENERATED = ROOT / "outputs" / "symbolic" / "boogie-rnn-demo-000.mid"
DEFAULT_OUTPUT = ROOT / "outputs" / "symbolic" / "evaluation.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def midi_metrics(path: Path) -> dict[str, Any]:
    midi = mido.MidiFile(path)
    if midi.ticks_per_beat <= 0:
        raise ValueError(f"MIDI file has invalid PPQN: {path}")

    events: list[tuple[int, int, Any]] = []
    order = 0
    final_tick = 0
    for track in midi.tracks:
        tick = 0
        for message in track:
            tick += message.time
            events.append((tick, order, message))
            final_tick = max(final_tick, tick)
            order += 1
    events.sort(key=lambda event: (event[0], event[1]))

    tempo = 500_000
    tempo_changes = [{"tick": 0, "microseconds_per_beat": tempo}]
    previous_tick = 0
    elapsed_seconds = 0.0
    note_events: list[tuple[int, float, int]] = []

    for tick, _, message in events:
        elapsed_seconds += (tick - previous_tick) * tempo / 1_000_000 / midi.ticks_per_beat
        previous_tick = tick
        if message.type == "set_tempo":
            tempo = message.tempo
            tempo_changes.append({"tick": tick, "microseconds_per_beat": tempo})
        elif message.type == "note_on" and message.velocity > 0:
            note_events.append((tick, elapsed_seconds, message.note))

    pitches = [note for _, _, note in note_events]
    onset_ticks = [tick for tick, _, _ in note_events]
    intervals = [right - left for left, right in zip(pitches, pitches[1:])]
    note_tick_span = max(onset_ticks) + 1 if onset_ticks else 0
    duration = elapsed_seconds

    return {
        "file": repo_path(path),
        "sha256": sha256_file(path),
        "midi_type": midi.type,
        "track_count": len(midi.tracks),
        "ticks_per_beat": midi.ticks_per_beat,
        "tempo_changes": tempo_changes,
        "duration_seconds": round(duration, 6),
        "positive_velocity_note_on_events": len(note_events),
        "note_on_events_per_second": round(len(note_events) / duration, 6) if duration else None,
        "pitch_min": min(pitches) if pitches else None,
        "pitch_max": max(pitches) if pitches else None,
        "pitch_histogram": dict(sorted(Counter(pitches).items())),
        "adjacent_note_event_interval_histogram_semitones": dict(sorted(Counter(intervals).items())),
        "distinct_onset_ticks": len(set(onset_ticks)),
        "onset_tick_occupancy_through_last_note": (
            round(len(set(onset_ticks)) / note_tick_span, 8) if note_tick_span else None
        ),
        "pitch_event_sequence": pitches,
    }


def pitch_ngram_overlap(generated: list[int], sources: list[list[int]], size: int = 8) -> dict[str, Any]:
    source_ngrams = {
        tuple(sequence[index : index + size])
        for sequence in sources
        for index in range(max(0, len(sequence) - size + 1))
    }
    generated_ngrams = [
        tuple(generated[index : index + size])
        for index in range(max(0, len(generated) - size + 1))
    ]
    matched = sum(ngram in source_ngrams for ngram in generated_ngrams)
    return {
        "n": size,
        "generated_windows": len(generated_ngrams),
        "windows_found_in_any_source": matched,
        "fraction_found_in_any_source": round(matched / len(generated_ngrams), 6)
        if generated_ngrams
        else None,
        "definition": "Contiguous pitch-event n-grams in chronological MIDI note-on order; simultaneous note ordering follows the MIDI parser order.",
    }


def build_report(source_dir: Path, generated_path: Path) -> dict[str, Any]:
    source_paths = sorted(
        path for path in source_dir.iterdir() if path.is_file() and path.suffix.lower() in {".mid", ".midi"}
    )
    if not source_paths:
        raise ValueError(f"No MIDI files found in {source_dir}")
    if not generated_path.is_file():
        raise FileNotFoundError(f"Generated MIDI not found: {generated_path}")

    sources = [midi_metrics(path) for path in source_paths]
    generated = midi_metrics(generated_path)
    all_source_pitches = [
        pitch for source in sources for pitch in source["pitch_event_sequence"]
    ]
    source_rates = [source["note_on_events_per_second"] for source in sources if source["note_on_events_per_second"] is not None]
    report = {
        "schema_version": 1,
        "method": "Descriptive MIDI note-on diagnostics computed with Mido using the same parser for source and generated files.",
        "source_files": sources,
        "source_collection_summary": {
            "file_count": len(sources),
            "total_positive_velocity_note_on_events": sum(
                source["positive_velocity_note_on_events"] for source in sources
            ),
            "combined_pitch_min": min(all_source_pitches) if all_source_pitches else None,
            "combined_pitch_max": max(all_source_pitches) if all_source_pitches else None,
            "median_source_note_on_events_per_second": round(statistics.median(source_rates), 6)
            if source_rates
            else None,
        },
        "generated_file": generated,
        "generated_pitch_ngram_overlap_with_sources": pitch_ngram_overlap(
            generated["pitch_event_sequence"],
            [source["pitch_event_sequence"] for source in sources],
        ),
        "interpretation": [
            "These measurements describe MIDI files; they do not measure musical quality, genre authenticity, originality, or listener preference.",
            "Pitch-event n-gram overlap is a narrow exact-sequence diagnostic, not a plagiarism or originality test.",
            "The generated score is one stochastic sample from a model trained on only six source files.",
        ],
    }
    for source in sources:
        source.pop("pitch_event_sequence")
    generated.pop("pitch_event_sequence")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES, help="Directory of source MIDI files")
    parser.add_argument("--generated", type=Path, default=DEFAULT_GENERATED, help="Generated MIDI file to compare")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="JSON report destination")
    args = parser.parse_args()

    report = build_report(args.sources, args.generated)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {repo_path(args.output)}")


if __name__ == "__main__":
    main()

