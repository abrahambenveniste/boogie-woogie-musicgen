# Modern MIDI event tokenization

In one line: this optional audit gives the same MIDI files a modern event-token view that can be compared with the character stream.

## Purpose

This optional workflow adds a modern, inspectable representation alongside the character stream. It uses [MidiTok](https://github.com/Natooz/MidiTok) and its REMI tokenization to turn the same normalized MIDI files into events suitable for Transformer-style symbolic-music workflows.

REMI represents note pitch, velocity, and duration and places notes on bar/position events. This gives a useful comparison with the older onset-only representation, which drops duration, original velocity, and much of the MIDI structure. The audit does not train a Transformer and does not claim that nine pieces are enough for one.

## Install and run

Install only the optional tokenizer and cross-check extra:

```powershell
python -m pip install -e ".[symbolic-modern]"
python scripts/tokenize_corpus.py
```

The default command tokenizes all normalized MIDI files in `data/normalized_midi/` and all generated MIDI files in `outputs/symbolic/`. To select specific outputs, pass `--generated` once for each path:

```powershell
python scripts/tokenize_corpus.py `
  --generated outputs/symbolic/boogie-rnn-seed-073-000.mid `
  --generated outputs/symbolic/boogie-rnn-seed-074-000.mid
```

The report is written to `outputs/symbolic/remi-token-audit.json`. Use `--sources`, `--reference-manifest`, and `--output` to select alternate input and output paths.

## Representation settings

The script records versions of MidiTok, Symusic (its MIDI I/O engine), Hugging Face `tokenizers`, and Mido, plus the complete MidiTok `TokenizerConfig`, in the JSON report. Mido independently reports MIDI type, track count, PPQN, note-on counts, and note-on counts by channel. The report's REMI run does not train a BPE/Unigram/WordPiece vocabulary, so it does not use the Hugging Face tokenizer-training feature. The current configuration:

- uses a 12-position-per-quarter-note grid, allowing common triplet and 16th-note subdivisions on the same grid;
- quantizes velocity to 16 bins and tempo to 32 bins between 40 and 250 BPM;
- includes tempo, time-signature, and General MIDI program tokens;
- uses the full standard MIDI pitch span (0–127) for both pitched and percussion notes.

The report includes the tokenizer's base vocabulary size, each MIDI file's SHA-256, token count, observed unique-token count, counts by token type, pitched and percussion note-token totals, Mido's channel-by-channel note-on counts, the duration-processing manifest's note-on count, any per-file count differences across these parsers, and a 48-token preview. It also records a stable fingerprint for the sorted normalized source corpus. For source MIDI, it compares REMI token count to the duration-aware character-stream length from `duration_processing_manifest.csv` as a representation-size diagnostic.

## Interpreting the comparison

The encodings serve different design goals. The old onset stream has one character per positive-velocity note-on plus a character for every tick slot. The current model uses separate attack and hold tokens on a 16th-note grid. REMI emits structured musical events and quantizes some values according to the saved configuration. The saved audit predates the nine-score model; refresh it before using it to compare current corpus counts. The first audit surfaced 14 omitted events in `Blastin Boogie`: MidiTok had interpreted its channel-10 notes as percussion and used the narrower default percussion-pitch range. The project now records the full MIDI 0–127 range for percussion as well, preserving all 321 source note-ons in that file. It still labels them `PitchDrum`, while the character model ignores channel semantics and treats the note numbers as pitch symbols. This is a source-data caveat, not a claim that the MIDI sounds like piano.

Therefore, the ratio between REMI tokens and character-stream length is not a compression benchmark, quality metric, or information-retention score.

This audit is data profiling and tokenizer exploration, not model training. The saved JSON is an older snapshot of the six-score onset-only baseline. Re-run `python scripts/tokenize_corpus.py` after installing the optional extra to refresh it for all nine current source scores and generated examples. A separate Transformer experiment should begin only with a larger, curated corpus and its own provenance, split strategy, and evaluation.

## References

- MidiTok [documentation](https://miditok.readthedocs.io/en/latest/) and [REMI tokenization description](https://miditok.readthedocs.io/en/latest/tokenizations.html).
- Fradet et al. (2021), [“MidiTok: A Python package for MIDI file tokenization”](https://archives.ismir.net/ismir2021/latebreaking/000005.pdf).
- Huang and Yang (2020), [“Pop Music Transformer: Beat-based Modeling and Generation of Expressive Pop Piano Compositions”](https://arxiv.org/abs/2002.00212).
