# Method and data

This project follows the reference repo's small, inspectable pipeline—MIDI → text → recurrent model → MIDI—then changes the representation so the model can learn note lengths. It also includes a separate pretrained model for prompt-to-audio generation.

## Reference workflow

The reference is [`s-zeng/rag-shenanigann`](https://github.com/s-zeng/rag-shenanigann), an experiment in ragtime composition (here, RAG does not mean retrieval-augmented generation). Its README lists Python 3, Fourmilab `midicsv`, Docker `torch-rnn`, and optional `gnmidifmt`; its output path uses `csvmidi` after decoding.

The repository includes 512 MIDI files under `rag/`, an optional `scripts/grab.py` scraper for two MIDI-library pages, `scripts/process.py`, a preprocessed character corpus, and `scripts/unprocess.py`. The README's workflow is:

1. Download or provide ragtime MIDI and convert it to Type 0 so all notes share one track.
2. Run `midicsv`; store PPQN and the first tempo, then map each positive-velocity note-on to a pitch character and each tick to a space-separated slot.
3. Train the character-level Torch7 RNN using the `torch-rnn` Docker project.
4. Decode generated text to MIDI CSV with `unprocess.py`, then convert CSV to MIDI with `csvmidi`.

That compact stream does not encode note-offs, durations, velocity, instrument, hand, channel, or later tempo changes. The reference README describes recognizable harmony in coherent passages, but also inconsistent tempo and style. It does not pin its training configuration or checkpoint, so its exact sample training run cannot be reconstructed from the README alone. The scraper is a convenience script, not a provenance or rights-management system.

## What this project keeps and changes

The project uses its own Boogie-Woogie/blues scores; it does not copy the reference's MIDI, code, or training corpus. It keeps the same broad data/model/decoder sequence and retains an onset-only corpus as a baseline. The current path is:

1. **Normalize:** Mido merges each source score into one Type-0 track. PPQN and the first tempo are retained.
2. **Encode:** pair note-ons with note-offs and quantize start/end to a 120-tick grid. With 480 PPQN, each slot is a sixteenth note. A pitch token marks an attack, a separate token represents a held pitch, and a space advances one slot. Notes shorter than a slot are represented for one slot.
3. **Train:** a character-level PyTorch LSTM predicts the next corpus character from random 128-character windows. The saved run uses 8 windows per batch, 32-dimensional embeddings, 96 hidden units, two LSTM layers, AdamW at 0.002, cross-entropy, gradient clipping at 1.0, seed 42, and 1,000 steps. The checkpoint and JSON metadata retain the vocabulary, corpus hash, settings, and software versions.
4. **Generate and decode:** sample from pitch/hold and space tokens until the requested number of slots, then decode slot positions to MIDI note-on/off events. This uses musical grid positions for time and closes held notes at the end.

The onset-only baseline cannot recover duration because it never encoded note-offs. The duration-aware representation addresses that specific failure; it does not model velocity, pedal, separate hands, explicit harmony, form, exact swing, or tempo changes.

## Training data and provenance

The nine source files are from PDMX v8, released on [Zenodo](https://doi.org/10.5281/zenodo.14984509). The PDMX metadata reports `cc-zero`, `license_conflict=False`, and inclusion in its no-license-conflict subset for each selected row. The manifest stores source object IDs, archive paths, tags, note counts, and hashes. These are provenance checks based on dataset metadata, not an independent legal review.

PDMX counts 7,458 notes for the nine entries; this project's Mido pass parses 7,743 positive-velocity note-on events. The measures differ because the dataset and MIDI parsers count different representations. The corpus is deliberately small and mixed; it is useful for a reproducible experiment, not a representative Boogie-Woogie dataset.

The raw inputs, normalized Type-0 files, corpus text, and per-file manifests are under [`data/`](../data/README.md). Regenerate the processed corpus and model with:

```bash
python -m pip install -e ".[symbolic]"
python scripts/normalize_type0.py
python scripts/process.py --note-encoding duration --grid-ticks-per-slot 120
python scripts/train_char_rnn.py --steps 1000 --seed 42
```

## Tools and model boundaries

- **Mido:** parse, merge, normalize, and write MIDI.
- **PyTorch:** train and sample the local character LSTM.
- **MusicGen via Transformers:** generate prompt-conditioned WAV with Meta's pretrained `facebook/musicgen-small`. This model is not trained on the nine MIDI files; its weights are downloaded separately and licensed CC-BY-NC 4.0. Review the [official model card](https://github.com/facebookresearch/audiocraft/blob/main/model_cards/MUSICGEN_MODEL_CARD.md) before reuse.
- **MidiTok (optional):** tokenize source and generated MIDI as REMI events for a representation audit. [`scripts/tokenize_corpus.py`](../scripts/tokenize_corpus.py) does not train a Transformer. Refresh [`remi-token-audit.json`](../outputs/symbolic/remi-token-audit.json) before using its counts as a current nine-score comparison.

The source papers and dataset:

- Long et al., “PDMX: A Large-Scale Public Domain MusicXML Dataset for Symbolic Music Processing,” ICASSP 2025, [DOI](https://doi.org/10.1109/ICASSP49660.2025.10890217).
- Xu et al., “Generating Symbolic Music from Natural Language Prompts using an LLM-Enhanced Dataset,” [arXiv:2410.02084](https://arxiv.org/abs/2410.02084).
- PDMX v8 release, [Zenodo](https://doi.org/10.5281/zenodo.14984509).
- MusicGen paper, [arXiv:2306.05284](https://arxiv.org/abs/2306.05284), and [model card](https://github.com/facebookresearch/audiocraft/blob/main/model_cards/MUSICGEN_MODEL_CARD.md).
