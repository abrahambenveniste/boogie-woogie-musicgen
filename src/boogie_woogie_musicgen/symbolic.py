"""MIDI-to-character utilities inspired by the rag-shenanigann workflow."""

from __future__ import annotations

import csv
import io
import shutil
import subprocess
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

import mido


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


def encode_midi_file_duration(
    midi_path: Path, grid_ticks_per_slot: int = 120
) -> EncodedMidi:
    """Encode note attacks and holds on a quantized grid, retaining duration.

    An onset uses ``chr(33 + pitch)`` and a continued note uses
    ``chr(256 + pitch)``. A space advances one grid slot. Notes are rounded to
    the nearest grid position and clipped to at least one slot. With 480 PPQN,
    the default grid is a sixteenth note.
    """
    if grid_ticks_per_slot < 1:
        raise ValueError("grid_ticks_per_slot must be positive.")
    midi = mido.MidiFile(midi_path)
    if midi.type != 0 or len(midi.tracks) != 1:
        raise ValueError("Input must be a one-track Type-0 MIDI. Run normalize_type0.py first.")
    ppqn = midi.ticks_per_beat
    if ppqn <= 0:
        raise ValueError(f"Expected PPQN ticks, got MIDI division {ppqn}.")

    tempo = next(
        (message.tempo for message in midi.tracks[0] if message.type == "set_tempo"),
        None,
    )
    if tempo is None:
        raise ValueError("MIDI has no Tempo event; add one before processing.")
    if not 1 <= tempo <= 0xFFFFFF:
        raise ValueError(f"Tempo must be in 1..16777215 microseconds/quarter; got {tempo}.")

    starts: dict[tuple[int, int], deque[int]] = defaultdict(deque)
    intervals: list[tuple[int, int, int, int]] = []
    tick = 0
    note_on_events = 0
    for message in midi.tracks[0]:
        tick += message.time
        if message.type == "note_on" and message.velocity > 0:
            starts[(message.channel, message.note)].append(tick)
            note_on_events += 1
        elif message.type == "note_off" or (
            message.type == "note_on" and message.velocity == 0
        ):
            key = (message.channel, message.note)
            if starts[key]:
                start_tick = starts[key].popleft()
                start_slot = (start_tick + grid_ticks_per_slot // 2) // grid_ticks_per_slot
                end_slot = max(
                    start_slot + 1,
                    (tick + grid_ticks_per_slot // 2) // grid_ticks_per_slot,
                )
                intervals.append((start_slot, end_slot, message.channel, message.note))

    for (channel, pitch), open_ticks in starts.items():
        for start_tick in open_ticks:
            start_slot = (start_tick + grid_ticks_per_slot // 2) // grid_ticks_per_slot
            end_slot = max(
                start_slot + 1,
                (tick + grid_ticks_per_slot // 2) // grid_ticks_per_slot,
            )
            intervals.append((start_slot, end_slot, channel, pitch))

    starts_by_slot: dict[int, list[tuple[int, int]]] = defaultdict(list)
    ends_by_slot: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for start_slot, end_slot, channel, pitch in intervals:
        starts_by_slot[start_slot].append((channel, pitch))
        ends_by_slot[end_slot].append((channel, pitch))
    slot_count = max(
        (tick + grid_ticks_per_slot - 1) // grid_ticks_per_slot,
        max((end for _, end, _, _ in intervals), default=0),
    )
    if slot_count > 10_000_000:
        raise ValueError(f"Refusing to allocate {slot_count:,} grid slots from one MIDI.")

    active: dict[tuple[int, int], int] = {}
    slots: list[str] = []
    for slot in range(slot_count):
        for key in ends_by_slot.get(slot, ()):
            if active.get(key, 0) > 1:
                active[key] -= 1
            else:
                active.pop(key, None)
        new_pitches = {pitch for _, pitch in starts_by_slot.get(slot, ())}
        for key in starts_by_slot.get(slot, ()):
            active[key] = active.get(key, 0) + 1
        pitches = {pitch for (_, pitch), count in active.items() if count > 0}
        slots.append(
            "".join(
                chr((33 if pitch in new_pitches else 256) + pitch)
                for pitch in sorted(pitches)
            )
        )

    return EncodedMidi(
        ppqn=ppqn,
        tempo_us_per_quarter=tempo,
        sequence=" ".join(slots),
        max_tick=slot_count,
        note_on_events=note_on_events,
    )


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


def csv_from_record(
    ppqn: int,
    tempo_us_per_quarter: int,
    sequence: str,
    note_encoding: str = "onset",
    grid_ticks_per_slot: int = 1,
) -> str:
    """Convert a reference-format note stream into one-track MIDI CSV.

    Tick slots, rather than string character offsets, set event times. A pitch
    In duration mode, attack tokens retrigger pitches and hold tokens keep them
    active. Legacy onset-only text lacks explicit holds and therefore keeps its
    historical one-tick behavior.
    """
    if ppqn <= 0 or not 1 <= tempo_us_per_quarter <= 0xFFFFFF or grid_ticks_per_slot < 1:
        raise ValueError("PPQN or tempo metadata is outside MIDI's valid range.")
    groups: list[tuple[set[int], set[int]]] = []
    for slot in sequence.split(" "):
        pitches: list[int] = []
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
                raise ValueError(f"Invalid pitch token {token!r} (decoded pitch {pitch}).")
            pitches.append(pitch)
        groups.append((set(pitches), attacks))

    lines = [
        f"0, 0, Header, 0, 1, {ppqn}",
        "1, 0, Start_track",
        f"1, 0, Tempo, {tempo_us_per_quarter}",
    ]
    active: set[int] = set()
    for slot, (current, attacks) in enumerate(groups):
        tick = slot * grid_ticks_per_slot
        for pitch in sorted((active - current) | (active & attacks)):
            lines.append(f"1, {tick}, Note_off_c, 1, {pitch}, 0")
        for pitch in sorted((current - active) | attacks):
            lines.append(f"1, {tick}, Note_on_c, 1, {pitch}, 96")
        active = current
    end_tick = len(groups) * grid_ticks_per_slot
    for pitch in sorted(active):
        lines.append(f"1, {end_tick}, Note_off_c, 1, {pitch}, 0")
    lines.extend([f"1, {end_tick}, End_track", "0, 0, End_of_file"])
    return "\n".join(lines) + "\n"
