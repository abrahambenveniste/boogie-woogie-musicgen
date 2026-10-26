"""MIDI-to-character utilities inspired by the rag-shenanigann workflow."""

from __future__ import annotations

import csv
import io
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EncodedMidi:
    ppqn: int
    tempo_us_per_quarter: int
    sequence: str
    max_tick: int
    note_on_events: int


def require_program(program: str) -> str:
    """Resolve a command name or explicit path and report an actionable error."""
    found = shutil.which(program)
    if found:
        return found
    path = Path(program)
    if path.is_file():
        return str(path.resolve())
    raise FileNotFoundError(
        f"Could not find {program!r}. Install the MIDIcsv utilities or pass their "
        "executable path with --midicsv / --csvmidi."
    )


def midi_to_csv_text(midi_path: Path, midicsv: str = "midicsv") -> str:
    executable = require_program(midicsv)
    result = subprocess.run(
        [executable, str(midi_path)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout


def parse_midi_csv(csv_text: str) -> EncodedMidi:
    """Read a Type-0 MIDICSV dump into the reference's tick/pitch text format.

    Each absolute MIDI tick is one slot. Positive-velocity note-on events at the
    same tick are concatenated as chr(33 + pitch); a literal space separates
    adjacent tick slots. This intentionally mirrors process.py in the reference.
    """
    rows = [
        [value.strip() for value in row]
        for row in csv.reader(io.StringIO(csv_text), skipinitialspace=True)
        if row and any(value.strip() for value in row)
    ]
    header = next((row for row in rows if len(row) >= 6 and row[2] == "Header"), None)
    if header is None:
        raise ValueError("MIDICSV output has no Header record.")
    if int(header[3]) != 0 or int(header[4]) != 1:
        raise ValueError(
            "Input must be a one-track Type-0 MIDI. Run normalize_type0.py first."
        )
    ppqn = int(header[5])
    if ppqn <= 0:
        raise ValueError(f"Expected PPQN ticks, got MIDI division {ppqn}.")

    tempo_row = next((row for row in rows if len(row) >= 4 and row[2] == "Tempo"), None)
    if tempo_row is None:
        raise ValueError("MIDI has no Tempo event; add one before processing.")
    tempo = int(tempo_row[3])
    if not 1 <= tempo <= 0xFFFFFF:
        raise ValueError(f"Tempo must be in 1..16777215 microseconds/quarter; got {tempo}.")

    notes_by_tick: dict[int, list[str]] = {}
    track_end_ticks: list[int] = []
    for row in rows:
        if len(row) < 3:
            continue
        if row[2] == "End_track" and len(row) >= 2:
            track_end_ticks.append(int(row[1]))
        if row[2] != "Note_on_c" or len(row) < 6 or int(row[5]) <= 0:
            continue
        tick = int(row[1])
        pitch = int(row[4])
        if tick < 0 or not 0 <= pitch <= 127:
            raise ValueError(f"Invalid note-on event at tick {tick}, pitch {pitch}.")
        token = chr(33 + pitch)
        # The historical torch-rnn preprocessing is byte oriented. This corpus
        # stays in printable ASCII (pitches <= 93) so its text remains portable.
        if ord(token) > 126:
            raise ValueError(
                f"Pitch {pitch} maps above printable ASCII in the reference codec. "
                "Transpose/filter the source or use a Unicode-aware token format."
            )
        notes_by_tick.setdefault(tick, []).append(token)

    last_note_tick = max(notes_by_tick, default=-1)
    max_tick = max(max(track_end_ticks, default=0), last_note_tick + 1)
    if max_tick > 10_000_000:
        raise ValueError(f"Refusing to allocate {max_tick:,} tick slots from one MIDI.")
    slots = [""] * max_tick
    for tick, tokens in notes_by_tick.items():
        slots[tick] = "".join(tokens)

    return EncodedMidi(
        ppqn=ppqn,
        tempo_us_per_quarter=tempo,
        sequence=" ".join(slots),
        max_tick=max_tick,
        note_on_events=sum(map(len, notes_by_tick.values())),
    )


def encode_midi_file(midi_path: Path, midicsv: str = "midicsv") -> EncodedMidi:
    return parse_midi_csv(midi_to_csv_text(midi_path, midicsv))


def corpus_records(text: str) -> list[tuple[int, int, str]]:
    """Return the three fields (PPQN, tempo, note stream) in each corpus block."""
    records: list[tuple[int, int, str]] = []
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
    for block in normalized.split("\n\n\n"):
        lines = block.splitlines()
        if len(lines) < 3:
            continue
        ppqn, tempo = int(lines[0]), int(lines[1])
        if ppqn <= 0 or not 1 <= tempo <= 0xFFFFFF:
            raise ValueError("Corpus block contains invalid PPQN or tempo metadata.")
        records.append((ppqn, tempo, "\n".join(lines[2:])))
    return records


def csv_from_record(ppqn: int, tempo_us_per_quarter: int, sequence: str) -> str:
    """Convert a reference-format note stream into one-track MIDI CSV.

    Tick slots, rather than string character offsets, set event times. Note
    lengths are inferred from the gap to the next generated onset group, since
    the source representation has no note-off or duration token.
    """
    if ppqn <= 0 or not 1 <= tempo_us_per_quarter <= 0xFFFFFF:
        raise ValueError("PPQN or tempo metadata is outside MIDI's valid range.")
    groups: list[list[int]] = []
    for slot in sequence.split(" "):
        pitches: list[int] = []
        for token in slot:
            pitch = ord(token) - 33
            if not 0 <= pitch <= 127:
                raise ValueError(f"Invalid pitch token {token!r} (decoded pitch {pitch}).")
            pitches.append(pitch)
        groups.append(pitches)

    lines = [
        f"0, 0, Header, 0, 1, {ppqn}",
        "1, 0, Start_track",
        f"1, 0, Tempo, {tempo_us_per_quarter}",
    ]
    active: set[int] = set()
    for tick, group in enumerate(groups):
        current = set(group)
        for pitch in sorted(active - current):
            lines.append(f"1, {tick}, Note_off_c, 1, {pitch}, 0")
        for pitch in sorted(current - active):
            lines.append(f"1, {tick}, Note_on_c, 1, {pitch}, 96")
        active = current
    end_tick = len(groups)
    for pitch in sorted(active):
        lines.append(f"1, {end_tick}, Note_off_c, 1, {pitch}, 0")
    lines.extend([f"1, {end_tick}, End_track", "0, 0, End_of_file"])
    return "\n".join(lines) + "\n"
