# MIDI training data

The project now has nine MIDI scores selected from PDMX v8: the six original Boogie-Woogie/blues examples plus *Chompin' at the Bit*, *The Squidgies Boogie*, and *Easy Boogie / Blues etude*. The additions were selected because PDMX titles or tags identify them as boogie, blues, or piano-etude material. They expand the experiment; they do not make nine scores representative of the genre.

All nine source rows report `cc-zero`, `license_conflict=False`, and `subset:no_license_conflict=True`. The PDMX v8 archive checksum was `d920a21b2fcd99a56d9c381b39debbb2`; source paths, object IDs, PDMX tags, counts, and local SHA-256 hashes are recorded in [`manifest.csv`](manifest.csv). These are dataset provenance fields, not an independent legal review.

The MIDI files were extracted from [PDMX v8 on Zenodo](https://doi.org/10.5281/zenodo.14984509). Please also cite the PDMX paper by Long et al. ([DOI 10.1109/ICASSP49660.2025.10890217](https://doi.org/10.1109/ICASSP49660.2025.10890217)) and the related dataset paper by Xu et al. ([arXiv:2410.02084](https://arxiv.org/abs/2410.02084)).

## What is in this folder

- `raw_midi/` — the nine source files, as supplied by PDMX.
- `normalized_midi/` — the same scores merged into one-track Type-0 MIDI by Mido.
- `manifest.csv` — per-score source records, license fields, local note counts, and hashes.
- `processed/normalization_manifest.csv` — source and normalized MIDI hashes, format, PPQN, and Mido version.
- `processed/training_data.txt` — the original six-score onset-only corpus retained as a historical baseline.
- `processed/processing_manifest.csv` — processing counts for that original baseline.
- `processed/training_data_duration.txt` — the new nine-score corpus used by the current LSTM.
- `processed/duration_processing_manifest.csv` and `training_data_duration.json` — grid, counts, software details, and corpus hash for the current run.

## The two encodings

The baseline follows the original reference representation: a pitch character marks a note-on tick, and spaces mark tick slots. It does not store note-off events or duration.

The current corpus uses a 120-tick grid at 480 PPQN. That is one sixteenth-note slot. An onset token marks a new note, a different hold token marks a pitch that continues, and a space moves to the next grid slot. The grid is quantized to preserve practical note lengths and keep generation short. Event times and durations are rounded to the nearest grid slot; notes shorter than one slot are lengthened to one slot.

The new corpus has 7,614 grid slots and 7,743 MIDI note-on events in 33,270 UTF-8 bytes. The original MIDI files span 913,466 ticks; the processed text compresses that timeline by representing one 120-tick slice per slot. PDMX's nine `n_notes` values total 7,458. That differs from the locally parsed event count because the measurements come from different parsers.

Regenerate the current corpus and model:

```powershell
python scripts/normalize_type0.py
python scripts/process.py --note-encoding duration --grid-ticks-per-slot 120
python scripts/train_char_rnn.py --steps 1000 --seed 42
```

To recreate the historical onset-only representation, use `--note-encoding onset` and install Fourmilab `midicsv`. That baseline corpus and checkpoint are kept for comparison; the nine-score duration model does not use them.
