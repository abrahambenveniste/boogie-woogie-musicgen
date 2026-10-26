#!/usr/bin/env python3
"""Audit the MIDI corpus with MidiTok's REMI event representation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
from collections import Counter
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

try:
    from miditok import REMI, TokenizerConfig
except ImportError as exc:  # pragma: no cover - exercised by the user-facing error
    raise SystemExit(
        "Install the symbolic-modern extra first: "
        "python -m pip install -e '.[symbolic-modern]'"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCES = ROOT / "data" / "normalized_midi"
DEFAULT_GENERATED = ROOT / "outputs" / "symbolic"
DEFAULT_REFERENCE_MANIFEST = ROOT / "data" / "processed" / "processing_manifest.csv"
DEFAULT_OUTPUT = ROOT / "outputs" / "symbolic" / "remi-token-audit.json"


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


def flatten_tokens(value: Any) -> list[str]:
    """Flatten MidiTok's per-track or nested token representation."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        flattened: list[str] = []
        for item in value:
            flattened.extend(flatten_tokens(item))
        return flattened
    raise TypeError(f"Unexpected MidiTok token value: {type(value).__name__}")


def load_reference_rows(path: Path) -> dict[str, dict[str, int]]:
    if not path.is_file():
        return {}
    with path.open(newline="", encoding="utf-8") as stream:
        return {
            row["file"]: {
                "encoded_sequence_characters": int(row["encoded_sequence_characters"]),
                "positive_velocity_note_on_events": int(row["positive_velocity_note_on_events"]),
            }
            for row in csv.DictReader(stream)
        }


def make_tokenizer() -> tuple[REMI, dict[str, Any]]:
    # A 12-position-per-quarter grid can express common triplet and 16th-note
    # subdivisions. Velocities and tempos are deliberately quantized; the exact
    # settings are recorded in the output report.
    config = TokenizerConfig(
        pitch_range=(0, 127),
        drums_pitch_range=(0, 127),
        beat_res={(0, 12): 12},
        num_velocities=16,
        use_velocities=True,
        use_tempos=True,
        num_tempos=32,
        tempo_range=(40, 250),
        use_time_signatures=True,
        use_programs=True,
        one_token_stream_for_programs=True,
    )
    return REMI(config), config.to_dict(serialize=True)


def tokenize_file(path: Path, tokenizer: REMI, reference_rows: dict[str, dict[str, int]]) -> dict[str, Any]:
    encoded = tokenizer.encode(path)
    sequences = encoded if isinstance(encoded, list) else [encoded]
    tokens: list[str] = []
    for sequence in sequences:
        tokens.extend(flatten_tokens(sequence.tokens))
    if not tokens:
        raise ValueError(f"MidiTok produced no tokens for {path}")

    type_counts = Counter(token.partition("_")[0] for token in tokens)
    reference_row = reference_rows.get(path.name, {})
    reference_length = reference_row.get("encoded_sequence_characters")
    reference_note_events = reference_row.get("positive_velocity_note_on_events")
    pitch_tokens = type_counts.get("Pitch", 0)
    drum_tokens = type_counts.get("PitchDrum", 0)
    result: dict[str, Any] = {
        "file": repo_path(path),
        "sha256": sha256_file(path),
        "token_count": len(tokens),
        "unique_tokens_observed": len(set(tokens)),
        "token_type_counts": dict(sorted(type_counts.items())),
        "pitched_note_token_count": pitch_tokens,
        "percussion_note_token_count": drum_tokens,
        "note_event_token_count": pitch_tokens + drum_tokens,
        "velocity_token_count": type_counts.get("Velocity", 0),
        "duration_token_count": type_counts.get("Duration", 0),
        "reference_positive_velocity_note_on_events": reference_note_events,
        "source_note_event_count_minus_remi_note_tokens": (
            reference_note_events - pitch_tokens - drum_tokens
            if reference_note_events is not None
            else None
        ),
        "reference_character_stream_characters": reference_length,
        "remi_tokens_per_reference_character": (
            round(len(tokens) / reference_length, 6) if reference_length else None
        ),
        "token_preview": tokens[:48],
    }
    return result


def midi_paths(directory: Path) -> list[Path]:
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in {".mid", ".midi"}
    )


def build_report(
    source_dir: Path,
    generated_paths: list[Path],
    reference_manifest: Path,
) -> dict[str, Any]:
    source_paths = midi_paths(source_dir)
    if not source_paths:
        raise ValueError(f"No source MIDI files found in {source_dir}")
    for path in generated_paths:
        if not path.is_file():
            raise FileNotFoundError(f"Generated MIDI not found: {path}")

    tokenizer, config = make_tokenizer()
    package_versions = {}
    for package in ("miditok", "symusic", "tokenizers"):
        try:
            package_versions[package] = version(package)
        except PackageNotFoundError:  # pragma: no cover - miditok is required
            package_versions[package] = None

    reference_rows = load_reference_rows(reference_manifest)
    source_records = [tokenize_file(path, tokenizer, reference_rows) for path in source_paths]
    generated_records = [tokenize_file(path, tokenizer, {}) for path in generated_paths]
    all_source_tokens = sum(record["token_count"] for record in source_records)
    all_source_note_tokens = sum(record["note_event_token_count"] for record in source_records)
    all_reference_note_events = sum(
        record["reference_positive_velocity_note_on_events"] or 0 for record in source_records
    )
    all_reference_chars = sum(
        record["reference_character_stream_characters"] or 0 for record in source_records
    )
    source_type_counts: Counter[str] = Counter()
    for record in source_records:
        source_type_counts.update(record["token_type_counts"])

    corpus_fingerprint = hashlib.sha256(
        "\n".join(f"{row['file']}:{row['sha256']}" for row in source_records).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": 1,
        "method": "MidiTok REMI event tokenization of normalized Type-0 MIDI files.",
        "tooling": {
            "packages": package_versions,
            "tokenizer": "REMI",
            "base_vocabulary_size": tokenizer.vocab_size,
            "python_version": platform.python_version(),
        },
        "configuration": config,
        "dataset": {
            "source_directory": repo_path(source_dir),
            "source_file_count": len(source_records),
            "source_corpus_sha256": corpus_fingerprint,
            "reference_manifest": repo_path(reference_manifest)
            if reference_manifest.is_file()
            else None,
            "reference_character_stream_characters": all_reference_chars or None,
            "remi_token_count": all_source_tokens,
            "reference_positive_velocity_note_on_events": all_reference_note_events or None,
            "remi_note_event_token_count": all_source_note_tokens,
            "reference_note_event_count_minus_remi_note_tokens": (
                all_reference_note_events - all_source_note_tokens
                if all_reference_note_events
                else None
            ),
            "remi_tokens_per_reference_character": (
                round(all_source_tokens / all_reference_chars, 6) if all_reference_chars else None
            ),
            "token_type_counts": dict(sorted(source_type_counts.items())),
        },
        "source_files": source_records,
        "generated_files": generated_records,
        "interpretation": [
            "REMI is an event-based representation: it uses bar/position, pitch, velocity, duration, and configured tempo, time-signature, and program tokens.",
            "The reference character stream records pitch onsets on a dense tick grid; its character count is not directly comparable to REMI token count as a measure of model quality or information content.",
            "This report tokenizes files for inspection. It does not train a Transformer or establish musical quality.",
            "The fixed 12-position-per-quarter grid, 16 velocity bins, and 32 tempo bins quantize source events; inspect the recorded configuration before interpreting results.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES, help="Directory of normalized source MIDI files")
    parser.add_argument(
        "--generated",
        type=Path,
        action="append",
        help="Generated MIDI file to tokenize; repeat this option for multiple takes",
    )
    parser.add_argument(
        "--reference-manifest",
        type=Path,
        default=DEFAULT_REFERENCE_MANIFEST,
        help="Manifest with character-stream lengths for the reference-compatible encoding",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="JSON audit report destination")
    args = parser.parse_args()

    generated = args.generated
    if generated is None:
        generated = sorted(DEFAULT_GENERATED.glob("boogie-rnn-seed-*-000.mid"))
    report = build_report(args.sources, generated, args.reference_manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Tokenized {len(report['source_files'])} source MIDI files and {len(report['generated_files'])} generated MIDI files.")
    print(f"Wrote {repo_path(args.output)}")


if __name__ == "__main__":
    main()
