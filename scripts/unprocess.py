"""Decode generated reference-format text to MIDI CSV and MIDI files."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
from pathlib import Path

import mido

from boogie_woogie_musicgen.symbolic import corpus_records, csv_from_record, require_program


def write_with_mido(
    path: Path,
    ppqn: int,
    tempo: int,
    sequence: str,
    note_encoding: str = "onset",
    grid_ticks_per_slot: int = 1,
) -> None:
    groups: list[tuple[set[int], set[int]]] = []
    for slot in sequence.split(" "):
        pitches: set[int] = set()
        attacks: set[int] = set()
        for token in slot:
            codepoint = ord(token)
            if note_encoding == "duration" and 256 <= codepoint <= 383:
                pitch = codepoint - 256
            elif 33 <= codepoint <= 160:
                pitch = codepoint - 33
                if note_encoding == "duration":
                    attacks.add(pitch)
            else:
                raise ValueError(f"Invalid pitch token {token!r} (code point {codepoint}).")
            if not 0 <= pitch <= 127:
                raise ValueError(f"Invalid pitch value {pitch}.")
            pitches.add(pitch)
        groups.append((pitches, attacks))
    events: list[tuple[int, int, int, int]] = []
    active: set[int] = set()
    for slot, (current, attacks) in enumerate(groups):
        tick = slot * grid_ticks_per_slot
        for pitch in (active - current) | (active & attacks):
            events.append((tick, 0, pitch, 0))
        for pitch in (current - active) | attacks:
            events.append((tick, 1, pitch, 96))
        active = current
    end_tick = len(groups) * grid_ticks_per_slot
    for pitch in active:
        events.append((end_tick, 0, pitch, 0))

    track = mido.MidiTrack()
    track.append(mido.MetaMessage("set_tempo", tempo=tempo, time=0))
    previous_tick = 0
    for tick, kind, pitch, velocity in sorted(events):
        message = (
            mido.Message("note_on", channel=0, note=pitch, velocity=velocity, time=tick - previous_tick)
            if kind
            else mido.Message("note_off", channel=0, note=pitch, velocity=0, time=tick - previous_tick)
        )
        track.append(message)
        previous_tick = tick
    track.append(mido.MetaMessage("end_of_track", time=max(0, end_tick - previous_tick)))
    midi = mido.MidiFile(type=0, ticks_per_beat=ppqn)
    midi.tracks.append(track)
    midi.save(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Three-line corpus/generated text file.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/symbolic"))
    parser.add_argument("--prefix", default="boogie-rnn")
    parser.add_argument("--record-index", type=int, default=None, help="Decode one record only.")
    parser.add_argument(
        "--midi-backend",
        choices=("auto", "csvmidi", "mido"),
        default="auto",
        help="Use csvmidi when available; mido is a self-contained fallback.",
    )
    parser.add_argument("--csvmidi", default="csvmidi", help="Executable name or path.")
    parser.add_argument(
        "--csvmidi-version",
        default="not-recorded",
        help="Version/distribution label for the externally installed CSVmidi utility.",
    )
    args = parser.parse_args()

    text = args.input.read_text(encoding="utf-8")
    generation_metadata_path = args.input.with_suffix(".json")
    generation_metadata = (
        json.loads(generation_metadata_path.read_text(encoding="utf-8"))
        if generation_metadata_path.is_file()
        else {}
    )
    note_encoding = generation_metadata.get("note_encoding", "onset")
    grid_ticks_per_slot = int(generation_metadata.get("grid_ticks_per_slot", 1))
    records = corpus_records(text)
    if args.record_index is not None:
        try:
            records = [records[args.record_index]]
        except IndexError as exc:
            raise SystemExit(f"No record at index {args.record_index}.") from exc
    if not records:
        raise SystemExit("No valid three-line records found in input.")

    use_csvmidi = args.midi_backend == "csvmidi" or (
        args.midi_backend == "auto" and shutil.which(args.csvmidi) is not None
    )
    if args.midi_backend == "csvmidi" and shutil.which(args.csvmidi) is None:
        raise SystemExit(f"Could not find csvmidi executable: {args.csvmidi}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for index, (ppqn, tempo, sequence) in enumerate(records):
        stem = f"{args.prefix}-{index:03d}"
        csv_path = args.output_dir / f"{stem}.csv"
        midi_path = args.output_dir / f"{stem}.mid"
        csv_path.write_text(
            csv_from_record(ppqn, tempo, sequence, note_encoding, grid_ticks_per_slot),
            encoding="ascii",
        )
        if use_csvmidi:
            csvmidi_path = Path(require_program(args.csvmidi))
            subprocess.run(
                [str(csvmidi_path), "-z", str(csv_path), str(midi_path)],
                check=True,
                capture_output=True,
                text=True,
            )
            backend = "csvmidi"
        else:
            write_with_mido(midi_path, ppqn, tempo, sequence, note_encoding, grid_ticks_per_slot)
            backend = "mido"
        decoded = mido.MidiFile(midi_path)
        pitches = [
            message.note
            for track in decoded.tracks
            for message in track
            if message.type == "note_on" and message.velocity > 0
        ]
        sidecar = {
            "source_text": args.input.as_posix(),
            "source_text_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
            "record_index": index,
            "csv_file": csv_path.as_posix(),
            "csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
            "midi_file": midi_path.as_posix(),
            "midi_sha256": hashlib.sha256(midi_path.read_bytes()).hexdigest(),
            "decoder": backend,
            "csvmidi_version_label": args.csvmidi_version if backend == "csvmidi" else None,
            "csvmidi_executable_sha256": (
                hashlib.sha256(csvmidi_path.read_bytes()).hexdigest() if backend == "csvmidi" else None
            ),
            "format": decoded.type,
            "tracks": len(decoded.tracks),
            "ppqn": decoded.ticks_per_beat,
            "tempo_us_per_quarter": tempo,
            "note_encoding": note_encoding,
            "grid_ticks_per_slot": grid_ticks_per_slot,
            "note_encoding": json.loads(args.input.with_suffix(".json").read_text(encoding="utf-8")).get("note_encoding")
            if args.input.with_suffix(".json").is_file()
            else None,
            "tick_slots": len(sequence.split(" ")),
            "positive_velocity_note_on_events": len(pitches),
            "pitch_range": [min(pitches), max(pitches)] if pitches else None,
            "duration_seconds": round(decoded.length, 3),
            "python_version": platform.python_version(),
        }
        midi_path.with_suffix(".json").write_text(
            json.dumps(sidecar, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Record {index}: {csv_path} -> {midi_path} ({backend})")


if __name__ == "__main__":
    main()
