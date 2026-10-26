# Evaluation plan

In one line: these repeatable note-level measurements describe the MIDI files; they do not score musical quality.

## Current status

The repository contains one MusicGen WAV and three controlled symbolic-RNN MIDI takes with recipes and a shared diagnostic report. They show that both pipelines run and that the symbolic output changes with the random seed; they are not benchmark results. No structured listener scores are claimed.

## Reproducible MIDI diagnostics

`scripts/evaluate_symbolic.py` computes descriptive metrics for every MIDI file in `data/normalized_midi/` and one or more generated MIDI files with the same Mido parser. Recreate the committed three-take snapshot with:

```powershell
python scripts/evaluate_symbolic.py `
  --generated outputs/symbolic/boogie-rnn-seed-073-000.mid `
  --generated outputs/symbolic/boogie-rnn-seed-074-000.mid `
  --generated outputs/symbolic/boogie-rnn-seed-075-000.mid
```

The JSON report is saved to [`outputs/symbolic/evaluation.json`](../outputs/symbolic/evaluation.json). It records per-file SHA-256 hashes, MIDI type, PPQN, tempo changes, duration, positive-velocity note-on count and density, pitch histogram and range, adjacent pitch-event intervals, onset-tick occupancy, exact 8-note pitch-event n-gram overlap against the six source files, and each generated take's seed, temperature, checkpoint hash, and decoder recipe.

The n-gram diagnostic follows chronological note-on event order; ordering of simultaneous notes follows the parser's event order. A match only means an exact short pitch sequence occurs in both files. None of these metrics measures quality, authenticity, originality, plagiarism, or listener preference. Use them alongside the listening protocol below.

The three symbolic takes use the same checkpoint, 4,800 tick slots (5 seconds at the stored 480 PPQN and 120 BPM), temperature 1.0, and Mido decoder. Only the random seed changes. The six source files contain 5,390 positive-velocity note-on events in total, with a median file density of 7.562309 events/second.

| Seed | Note-on events | Events/second | MIDI pitch range | Exact 8-event windows shared with sources |
| ---: | ---: | ---: | ---: | ---: |
| 73 | 38 | 7.6 | 28–77 | 0 / 31 |
| 74 | 23 | 4.6 | 28–86 | 0 / 16 |
| 75 | 27 | 5.4 | 36–81 | 0 / 20 |

The density and pitch range vary across these three samples. This is descriptive evidence of seed-dependent variation, not evidence of musical quality. The zero exact-window overlap is only a property of this narrow diagnostic and does not establish originality.

## Listening protocol

For a small exploratory listening study, use the three committed symbolic takes and generate three MusicGen takes with a documented seed list. Randomize playback order within each method and ask listeners to score from 1 (weak) to 5 (strong):

| Criterion | Listening question |
| --- | --- |
| Style fit | Does it sound recognizably like Boogie-Woogie or closely related piano blues? |
| Groove | Is there a convincing repeated bass/shuffle pulse and forward motion? |
| Coherence | Does the idea hold together through the take? |
| Variety | Does it avoid simply repeating one short phrase? |
| Artifacts | Are there distracting audio or MIDI-rendering problems? |

For MusicGen, also score prompt adherence. For the symbolic RNN, compare the generated MIDI with the training scores in a piano roll and record pitch range, event density, note lengths reconstructed by the decoder, and repetition. Keep the MusicGen prompt/JSON and RNN MIDI/text/JSON/checkpoint hash together. Record the listener, date, playback setup, model settings, and individual scores; report sample count and median or range rather than a broad claim.

### Blank score sheet

Fill this in only after listening. Use 1 (weak) to 5 (strong); prompt adherence applies only to MusicGen. Render the MIDI takes with the same piano sound for a fair within-method comparison.

| Listener | Date | Sample | Style fit | Groove | Coherence | Variety | Artifacts | Prompt adherence | Comments |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
|  |  | MusicGen WAV |  |  |  |  |  |  |  |
|  |  | Symbolic seed 73 |  |  |  |  |  | n/a |  |
|  |  | Symbolic seed 74 |  |  |  |  |  | n/a |  |
|  |  | Symbolic seed 75 |  |  |  |  |  | n/a |  |

## Symbolic diagnostics

The RNN is trained on only six scores, so these simple diagnostics are exploratory and not sufficient measures of musical quality. The report already includes pitch range/histograms, event density, adjacent intervals, onset-tick occupancy, and pitch n-gram overlap. Future extensions can add:

- repeated-pitch distributions;
- note-length and polyphony summaries, with clear handling of the codec's reconstruction assumptions;
- generated MIDI readability in a piano roll and playback by a listener.

The separate [`remi-token-audit.json`](../outputs/symbolic/remi-token-audit.json) reports MidiTok REMI token counts for the same source corpus and generated MIDI takes. It records the tokenizer version, configuration, per-file source hash, event-token type counts, and a short token preview. The character-stream length and REMI token count have different definitions, so their ratio describes representation size only; it is not a quality or information-retention score. See [the tokenization note](MODERN_TOKENIZATION.md) for quantization and scope limits.

These measurements should be calculated on source and generated MIDI with the same parser. They do not establish plagiarism, originality, style authenticity, or listener preference by themselves.

## Controlled comparisons

- Compare a small range of LSTM temperatures while holding the checkpoint, tick budget, and seed fixed; the committed baseline holds temperature at 1.0 and varies seeds 73, 74, and 75.
- Compare a minimal MusicGen prompt against the full left-hand/right-hand groove brief, with duration and seed fixed.
- Keep symbolic LSTM and MusicGen results in separate groups; their data, conditioning, output format, and learned task differ, so they are not a direct apples-to-apples model benchmark.

Do not state that an output follows exact BPM, 12-bar form, chord progression, or hand pattern unless that property is independently inspected from the generated audio or MIDI.

