# Modern MIDI event tokenization

## Purpose

This optional workflow adds a modern, inspectable representation alongside the reference-compatible character stream. It uses [MidiTok](https://github.com/Natooz/MidiTok) and its REMI tokenization to turn the same normalized MIDI files into events suitable for Transformer-style symbolic-music workflows.

REMI represents note pitch, velocity, and duration and places notes on bar/position events. This gives a useful comparison with the reference representation, which stores pitch onsets on a dense tick grid and drops duration, original velocity, and much of the MIDI structure. The audit does not train a Transformer and does not claim that six pieces are enough for one.

## Install and run

Install only the optional tokenizer extra:

```powershell
python -m pip install -e ".[symbolic-modern]"
python scripts/tokenize_corpus.py
```

The default command tokenizes all normalized MIDI files in `data/normalized_midi/` and the three controlled seed takes in `outputs/symbolic/`. To tokenize selected outputs, pass `--generated` once for each path:

```powershell
python scripts/tokenize_corpus.py `
  --generated outputs/symbolic/boogie-rnn-seed-073-000.mid `
  --generated outputs/symbolic/boogie-rnn-seed-074-000.mid
```

The report is written to `outputs/symbolic/remi-token-audit.json`. Use `--sources`, `--reference-manifest`, and `--output` to select alternate input and output paths.

## Representation settings

The script records the versions of MidiTok, Symusic (its MIDI I/O engine), and the Hugging Face `tokenizers` package, plus the complete MidiTok `TokenizerConfig`, in the JSON report. The report's REMI run does not train a BPE/Unigram/WordPiece vocabulary, so it does not use the Hugging Face tokenizer-training feature. The current configuration:

- uses a 12-position-per-quarter-note grid, allowing common triplet and 16th-note subdivisions on the same grid;
- quantizes velocity to 16 bins and tempo to 32 bins between 40 and 250 BPM;
- includes tempo, time-signature, and General MIDI program tokens;
- uses the full standard MIDI pitch span (0–127) for both pitched and percussion notes.

The report includes the tokenizer's base vocabulary size, each MIDI file's SHA-256, token count, observed unique-token count, counts by token type, pitched and percussion note-token totals, source note-on counts, any per-file difference after tokenization, and a 48-token preview. It also records a stable fingerprint for the sorted normalized source corpus. For source MIDI, it compares REMI token count to the reference character-stream length from `processing_manifest.csv` as a representation-size diagnostic.

## Interpreting the comparison

The two encodings serve different design goals. The reference stream has one character per positive-velocity note-on plus a character for every tick slot. REMI emits structured musical events and quantizes some values according to the saved configuration. MidiTok preprocessing can also change the event count; the audit reports source note-on counts beside note tokens so differences are visible rather than silently assumed away. The first audit surfaced 14 omitted events in `Blastin Boogie`: MidiTok had interpreted its channel-10 notes as percussion and used the narrower default percussion-pitch range. The project now records the full MIDI 0–127 range for percussion as well, preserving all 321 source note-ons in that file. It still labels them `PitchDrum`, while the reference character stream ignores channel semantics and treats the note numbers as pitch symbols. This is a source-data caveat, not a claim that the MIDI sounds like piano.

Therefore, the ratio between REMI tokens and reference characters is not a compression benchmark, quality metric, or information-retention score.

This audit is data profiling and tokenizer exploration, not model training. It makes the data transformation visible and gives a concrete next representation if the corpus is later expanded. Keep the current six-file dataset and its existing LSTM results as a fixed baseline. A separate Transformer experiment should begin only with a larger, curated corpus and its own provenance, split strategy, and evaluation.

## References

- MidiTok [documentation](https://miditok.readthedocs.io/en/latest/) and [REMI tokenization description](https://miditok.readthedocs.io/en/latest/tokenizations.html).
- Fradet et al. (2021), [“MidiTok: A Python package for MIDI file tokenization”](https://archives.ismir.net/ismir2021/latebreaking/000005.pdf).
- Huang and Yang (2020), [“Pop Music Transformer: Beat-based Modeling and Generation of Expressive Pop Piano Compositions”](https://arxiv.org/abs/2002.00212).
