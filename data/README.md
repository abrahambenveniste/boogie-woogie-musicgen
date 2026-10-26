# Training MIDI data

The raw MIDI files in `raw_midi/` are six selected entries from the PDMX dataset, version v8. They were extracted from PDMX's `mid.tar.gz` archive (archive MD5 `d920a21b2fcd99a56d9c381b39debbb2`, Zenodo record `10.5281/zenodo.14984509`). The complete PDMX archive is not included; only the six listed MIDI files are redistributed here.

Dataset citations requested by the PDMX authors:

- Phillip Long, Zachary Novack, Taylor Berg-Kirkpatrick, and Julian McAuley. “PDMX: A Large-Scale Public Domain MusicXML Dataset for Symbolic Music Processing.” ICASSP 2025. [DOI: 10.1109/ICASSP49660.2025.10890217](https://doi.org/10.1109/ICASSP49660.2025.10890217).
- Weihan Xu, Julian McAuley, Taylor Berg-Kirkpatrick, Shlomo Dubnov, and Hao-Wen Dong. “Generating Symbolic Music from Natural Language Prompts using an LLM-Enhanced Dataset.” [arXiv:2410.02084](https://arxiv.org/abs/2410.02084).
- PDMX v8 dataset archive. [Zenodo DOI: 10.5281/zenodo.14984509](https://doi.org/10.5281/zenodo.14984509).

`manifest.csv` is the source and integrity record. For each MIDI it records the PDMX object ID and archive path, title, uploader/artist, composer, source license fields, PDMX `n_notes`, locally parsed positive-velocity note-on count and pitch range, local SHA-256, and a brief curation note. The PDMX metadata rows label all six files `cc-zero`, `license_conflict=False`, and `subset:no_license_conflict=True`.

PDMX explains that a discrepancy between public-facing and embedded copyright metadata affected 12.29% of its songs and recommends using the `no_license_conflict` subset. The six selected rows pass that dataset check. This is documented provenance, not independent legal advice or a guarantee that every uploaded arrangement is rights-free. See [`docs/data-and-models.md`](../docs/data-and-models.md) for the project’s rights and data caveats.

The two historical compositions have `is_original=False` in PDMX; the other four are marked original by their PDMX rows. We keep these metadata values as published and do not infer ownership from them. One selected title retains the source spelling “Exersices.”

## Derived files

- `normalized_midi/` contains the six sources converted to one-track Type 0 by `scripts/normalize_type0.py`.
- `processed/normalization_manifest.csv` records source and output hashes, MIDI formats/track counts, PPQN, and Mido version for the conversion.
- `processed/training_data.txt` is the exact character corpus consumed by the RNN scripts.
- `processed/processing_manifest.csv` stores the per-file normalized MIDI hash, PPQN, first tempo, tick-slot count, positive-velocity note-on count, and encoded character count.
- `processed/training_data.json` stores the corpus hash/size, processing totals, input file metadata, Python version, and MIDICSV version label.

Regenerate them with:

```powershell
python scripts/normalize_type0.py
python scripts/process.py --midicsv midicsv
```

PDMX's `n_notes` and this project's MIDI note-on count are intentionally separate columns: they are counted by different PDMX and MIDI parsing paths and do not always match.

