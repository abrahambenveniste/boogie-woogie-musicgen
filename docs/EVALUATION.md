# Evaluation plan

## Current status

The repository contains one MusicGen WAV and one symbolic-RNN MIDI demonstration with its recipes and training log. They show that both pipelines run; they are not benchmark results. No structured listener scores are claimed.

## Reproducible MIDI diagnostics

`scripts/evaluate_symbolic.py` computes descriptive metrics for every MIDI file in `data/normalized_midi/` and the committed generated MIDI with the same Mido parser. Recreate the snapshot with:

```powershell
python scripts/evaluate_symbolic.py
```

The JSON report is saved to [`outputs/symbolic/evaluation.json`](../outputs/symbolic/evaluation.json). It records per-file SHA-256 hashes, MIDI type, PPQN, tempo changes, duration, positive-velocity note-on count and density, pitch histogram and range, adjacent pitch-event intervals, onset-tick occupancy, and exact 8-note pitch-event n-gram overlap against the six source files.

The n-gram diagnostic follows chronological note-on event order; ordering of simultaneous notes follows the parser's event order. A match only means an exact short pitch sequence occurs in both files. None of these metrics measures quality, authenticity, originality, plagiarism, or listener preference. Use them alongside the listening protocol below.

In the committed snapshot, the six source files contain 5,390 positive-velocity note-on events in total, with a median file density of 7.562309 events/second. The generated example contains 38 such events at 7.6 events/second, spans MIDI pitches 28–77, and has no exact 8-event pitch windows in common with the sources under this definition. The zero overlap is only a property of this one diagnostic and does not establish originality.

## Listening protocol

For a small exploratory listening study, generate three takes per method with a documented seed list. Randomize the playback order and ask listeners to score from 1 (weak) to 5 (strong):

| Criterion | Listening question |
| --- | --- |
| Style fit | Does it sound recognizably like Boogie-Woogie or closely related piano blues? |
| Groove | Is there a convincing repeated bass/shuffle pulse and forward motion? |
| Coherence | Does the idea hold together through the take? |
| Variety | Does it avoid simply repeating one short phrase? |
| Artifacts | Are there distracting audio or MIDI-rendering problems? |

For MusicGen, also score prompt adherence. For the symbolic RNN, compare the generated MIDI with the training scores in a piano roll and record pitch range, event density, note lengths reconstructed by the decoder, and repetition. Keep the MusicGen prompt/JSON and RNN MIDI/text/JSON/checkpoint hash together. Record the listener, date, playback setup, model settings, and individual scores; report sample count and median or range rather than a broad claim.

## Symbolic diagnostics

The RNN is trained on only six scores, so these simple diagnostics are exploratory and not sufficient measures of musical quality. The report already includes pitch range/histograms, event density, adjacent intervals, onset-tick occupancy, and pitch n-gram overlap. Future extensions can add:

- repeated-pitch distributions;
- note-length and polyphony summaries, with clear handling of the codec's reconstruction assumptions;
- generated MIDI readability in a piano roll and playback by a listener.

These measurements should be calculated on source and generated MIDI with the same parser. They do not establish plagiarism, originality, style authenticity, or listener preference by themselves.

## Controlled comparisons

- Compare a small range of LSTM temperatures while holding the checkpoint, tick budget, and seed fixed.
- Compare a minimal MusicGen prompt against the full left-hand/right-hand groove brief, with duration and seed fixed.
- Keep symbolic LSTM and MusicGen results in separate groups; their data, conditioning, output format, and learned task differ, so they are not a direct apples-to-apples model benchmark.

Do not state that an output follows exact BPM, 12-bar form, chord progression, or hand pattern unless that property is independently inspected from the generated audio or MIDI.

