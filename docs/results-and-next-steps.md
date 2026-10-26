# Results and next steps

In one line: both pipelines run, and the MIDI audit shows why valid generated files still need musical improvement.

## What the current runs show

- **MusicGen:** it produced a non-silent 3.94-second mono WAV at 32 kHz; no listener ratings have been collected, so style fit and enjoyment remain open questions.
- **Symbolic LSTM:** it trained and produced valid Type-0 MIDI that changes across seeds, but the three takes contain only 23–38 note-on events each.
- **A playback problem:** the MIDI takes give notes a duration of just 1–2 ticks (about 1–2 ms at 120 BPM and 480 PPQN). The text representation stores note onsets but loses original note lengths, so the current symbolic output is not yet a satisfying piano performance.
- **Training evidence:** minibatch loss fell from 4.2998 to 0.0480 in 1,000 steps, but there is no held-out set; this does not show that the model generalizes.
- **Data evidence:** six source MIDI files contain 5,390 note-on events; the separate REMI audit found a MIDI channel marked as percussion in one source file.
- **Similarity check:** none of the sampled outputs shared an exact 8-note pitch sequence with the six sources, but there were only 16–31 windows per sample; this is a narrow check, not proof of originality.

## Evaluation details

### Current status

The repository contains one MusicGen WAV and three controlled symbolic-RNN MIDI takes with recipes and a shared diagnostic report. They show that both pipelines run and that the symbolic output changes with the random seed; they are not benchmark results. No structured listener scores are claimed.

### Reproducible MIDI diagnostics

`scripts/evaluate_symbolic.py` computes descriptive metrics for every MIDI file in `data/normalized_midi/` and one or more generated MIDI files with the same Mido parser. Recreate the committed three-take snapshot with:

```powershell
python scripts/evaluate_symbolic.py `
  --generated outputs/symbolic/boogie-rnn-seed-073-000.mid `
  --generated outputs/symbolic/boogie-rnn-seed-074-000.mid `
  --generated outputs/symbolic/boogie-rnn-seed-075-000.mid
```

The JSON report is saved to [`outputs/symbolic/evaluation.json`](../outputs/symbolic/evaluation.json). It records per-file SHA-256 hashes, MIDI type, PPQN, tempo changes, duration, note-on count and density, paired note-length summaries in ticks, pitch histogram and range, adjacent pitch-event intervals, onset-tick occupancy, exact 8-note pitch-event n-gram overlap, and each generated take's seed, temperature, checkpoint hash, and decoder recipe.

The n-gram diagnostic follows chronological note-on event order; ordering of simultaneous notes follows the parser's event order. A match only means an exact short pitch sequence occurs in both files. None of these metrics measures quality, authenticity, originality, plagiarism, or listener preference. Use them alongside the listening protocol below.

The three symbolic takes use the same checkpoint, 4,800 tick slots (5 seconds at the stored 480 PPQN and 120 BPM), temperature 1.0, and Mido decoder. Only the random seed changes. The six source files contain 5,390 positive-velocity note-on events in total, with a median file density of 7.562309 events/second.

| Seed | Note-on events | Events/second | Median note length (ticks) | MIDI pitch range | Exact 8-event windows shared with sources |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 73 | 38 | 7.6 | 1 | 28–77 | 0 / 31 |
| 74 | 23 | 4.6 | 1 | 28–86 | 0 / 16 |
| 75 | 27 | 5.4 | 1 | 36–81 | 0 / 20 |

The density and pitch range vary across these three samples. This is descriptive evidence of seed-dependent variation, not evidence of musical quality. The zero exact-window overlap is only a property of this narrow diagnostic and does not establish originality.

### Listening protocol

For a small exploratory listening study, first score MusicGen takes with fixed, recorded prompts and seeds. Revisit the symbolic takes after note durations are represented properly and the MIDI is rendered with the same piano sound. Randomize playback order within each method and ask listeners to score from 1 (weak) to 5 (strong):

| Criterion | Listening question |
| --- | --- |
| Style fit | Does it sound recognizably like Boogie-Woogie or closely related piano blues? |
| Groove | Is there a convincing repeated bass/shuffle pulse and forward motion? |
| Coherence | Does the idea hold together through the take? |
| Variety | Does it avoid simply repeating one short phrase? |
| Artifacts | Are there distracting audio or MIDI-rendering problems? |

For MusicGen, also score prompt adherence. For the symbolic RNN, compare the generated MIDI with the training scores in a piano roll and record pitch range, event density, note lengths reconstructed by the decoder, and repetition. Keep the MusicGen prompt/JSON and RNN MIDI/text/JSON/checkpoint hash together. Record the listener, date, playback setup, model settings, and individual scores; report sample count and median or range rather than a broad claim.

#### Blank score sheet

Fill this in only after listening. Use 1 (weak) to 5 (strong); prompt adherence applies only to MusicGen. Leave the symbolic rows blank until the note-duration issue is fixed and all MIDI files use the same piano rendering.

| Listener | Date | Sample | Style fit | Groove | Coherence | Variety | Artifacts | Prompt adherence | Comments |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
|  |  | MusicGen WAV |  |  |  |  |  |  |  |
|  |  | Symbolic seed 73 |  |  |  |  |  | n/a |  |
|  |  | Symbolic seed 74 |  |  |  |  |  | n/a |  |
|  |  | Symbolic seed 75 |  |  |  |  |  | n/a |  |

### Symbolic diagnostics

The RNN is trained on only six scores, so these simple diagnostics are exploratory and not sufficient measures of musical quality. The report already includes pitch range/histograms, event density, adjacent intervals, onset-tick occupancy, and pitch n-gram overlap. Future extensions can add:

- repeated-pitch distributions;
- note-length and polyphony summaries, with clear handling of the codec's reconstruction assumptions;
- generated MIDI readability in a piano roll and playback by a listener.

The separate [`remi-token-audit.json`](../outputs/symbolic/remi-token-audit.json) reports MidiTok REMI token counts for the same source corpus and generated MIDI takes. It records the tokenizer version, configuration, per-file source hash, event-token type counts, and a short token preview. The character-stream length and REMI token count have different definitions, so their ratio describes representation size only; it is not a quality or information-retention score. See [the tokenization note](midi-tokens.md) for quantization and scope limits.

These measurements should be calculated on source and generated MIDI with the same parser. They do not establish plagiarism, originality, style authenticity, or listener preference by themselves.

### Controlled comparisons

- Compare a small range of LSTM temperatures while holding the checkpoint, tick budget, and seed fixed; the committed baseline holds temperature at 1.0 and varies seeds 73, 74, and 75.
- Compare a minimal MusicGen prompt against the full left-hand/right-hand groove brief, with duration and seed fixed.
- Keep symbolic LSTM and MusicGen results in separate groups; their data, conditioning, output format, and learned task differ, so they are not a direct apples-to-apples model benchmark.

Do not state that an output follows exact BPM, 12-bar form, chord progression, or hand pattern unless that property is independently inspected from the generated audio or MIDI.

## Scope and next steps

In one line: this page says what runs now, what stays fixed for the baseline, and what could come next.

### Current scope decision

- Keep the symbolic training corpus fixed at the six source MIDI files listed in `data/manifest.csv` for this baseline. This is the project owner's chosen scope, not a claim that six pieces represent the full genre.
- Preserve the six-item corpus and its recorded source IDs, license metadata, hashes, and processing results so the baseline remains auditable.
- Treat future corpus expansions as separately documented experiments, with provenance and license review for every added file.
- Keep the pretrained MusicGen prompt experiment distinct: it is not trained on these six MIDI files.

### Implemented

- Prompt-conditioned MusicGen inference with Boogie-Woogie presets, CLI, Gradio UI, WAV output, and JSON provenance.
- A parallel symbolic pipeline based on the MIDI → text → RNN → MIDI workflow documented in `s-zeng/rag-shenanigann`.
- Six PDMX v8 source MIDI files with source IDs, per-item license fields, no-conflict flags, file hashes, and source/local note counts.
- Python/Mido Type-0 normalization, actual `midicsv` parsing, deterministic character-corpus generation, per-file processing metrics, and `csvmidi`-based decode.
- A PyTorch character LSTM training and sampling implementation, plus the legacy Torch7 Docker training recipe.
- Three controlled symbolic MIDI takes from seeds 73, 74, and 75, with text, MIDI CSV, MIDI, and per-run metadata.
- A reproducible Mido-based MIDI diagnostics script and a committed JSON comparison of the six source scores with all three generated takes.
- An optional MidiTok REMI audit of the six normalized source files and three controlled generated takes, with per-file hashes, token-type counts, configuration, previews, and independent Mido channel/note-on counts.
- A fresh public checkout reproduced an additional five-second symbolic MIDI take using the available Python environment; dependency installation from a blank environment remains unverified.
- Documentation for both model paths, corpus curation and licenses, exact representation, tool roles, limitations, and reproducibility.

### Not claimed

- The six-score MIDI corpus is too small to support claims of broad musical generalization or a benchmark result.
- No structured listening study has been completed. The samples are demonstrations, not evaluated performance claims.
- The MIDI character codec does not preserve note durations, velocities, part labels, or expressive controls. Reconstructed note lengths are inferred from the generated tick sequence.
- MusicGen prompts and the symbolic RNN do not guarantee exact BPM, chord progression, 12-bar form, or piano technique.
- The documented legacy Torch7 container was not run in the authoring environment; the included checkpoint uses the runnable PyTorch implementation.
- The MidiTok extension tokenizes and profiles the data; it does not train or evaluate a Transformer model.

### Suggested next work

1. Record listener scores for MusicGen; revisit symbolic listening after note durations are represented properly.
2. Compare LSTM temperatures while holding the six-file corpus, checkpoint, tick count, and seed fixed; save each recipe.
3. Keep the MidiTok event-token audit as a representation comparison. Consider Transformer training only after increasing and curating the licensed corpus; six scores are too small for a credible modern-model comparison.

