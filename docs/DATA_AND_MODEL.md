# Data and model provenance

This repository has two model paths with different data and rights profiles. The MusicGen checkpoint is pretrained outside this project. The character LSTM checkpoint is trained here on the six MIDI files listed in [`data/manifest.csv`](../data/manifest.csv).

## Symbolic MIDI training data

### Source and filtering

The six MIDI files are from PDMX v8, [Zenodo DOI 10.5281/zenodo.14984509](https://doi.org/10.5281/zenodo.14984509). PDMX is a large collection of public-domain symbolic scores with per-entry metadata and optional MIDI exports. We selected entries whose titles/tags identify Boogie-Woogie or blues piano/bass material, whose PDMX `license` value is `cc-zero`, whose `license_conflict` value is `False`, and whose MIDI file is present. The project contains only these six MIDI files, not the full PDMX archive.

The exact PDMX object identifier, `mid` archive path, title, artist/uploader, composer, source license URL, PDMX score-level note count, locally parsed note-on count and pitch range, and local SHA-256 are recorded in the manifest. Raw files are in [`data/raw_midi/`](../data/raw_midi/). The PDMX v8 MIDI archive MD5 was `d920a21b2fcd99a56d9c381b39debbb2`.

Following the PDMX authors' citation guidance, cite the dataset paper (Long et al., ICASSP 2025, [DOI 10.1109/ICASSP49660.2025.10890217](https://doi.org/10.1109/ICASSP49660.2025.10890217)), the related paper listed in the PDMX repository (Xu et al., [arXiv:2410.02084](https://arxiv.org/abs/2410.02084)), and the versioned [PDMX v8 Zenodo record](https://doi.org/10.5281/zenodo.14984509).

PDMX reports a discrepancy between public-facing copyright metadata and embedded metadata that affected 31,221 (12.29%) entries and recommends the `no_license_conflict` subset. All six selected entries are in that subset. This is a documented data-source check, not an independent legal review. A per-entry CC0 field and no-conflict flag do not guarantee that a user-uploaded arrangement or transcription is free of every third-party right. Four selected entries are marked `is_original=True` by PDMX; two historical score entries are marked `False`. These are preserved as source metadata, not treated as ownership determinations.

The PDMX score-level `n_notes` values total 5,020. A local MIDI parser counts 5,390 positive-velocity `Note_on_c` events. These counts differ because PDMX's score-level statistic and this project's MIDI event parser are distinct measurement paths. Both are retained; the processed corpus's per-file event counts are in [`data/processed/processing_manifest.csv`](../data/processed/processing_manifest.csv).

### Corpus size and limitations

The six Type-0-processed MIDI files use 480 PPQN and encode 672,098 tick slots and 5,390 positive-velocity note-on events. The resulting training text is 677,566 ASCII bytes. All local source MIDI hashes are in the manifest. This is a small, curated starter corpus, not a representative sample of all Boogie-Woogie performance practice. It contains exercises, short examples, and historical pieces, with no held-out test split or benchmark claim.

The optional MidiTok audit exposed a MIDI-channel caveat: `blastin_boogie.mid` stores its notes on zero-indexed channel 9 (General MIDI channel 10), which MidiTok classifies as percussion. The reference-compatible character encoder drops channel identity and learns only from note numbers and tick positions, so this score contributes key numbers as if they were ordinary pitch symbols. Keep this limitation in mind when describing the corpus as piano data. The MidiTok audit widens its percussion pitch range to 0–127 so none of this file's 321 note-on events is discarded by the tokenizer's default narrower drum range.

The text encoder drops duration, note-off, velocity, instrument, channel, separate parts, later tempo changes, and performance controls. The model learns this lossy serialization; it does not train directly on the original full MIDI event stream.

## MusicGen training data and checkpoint

The prompt-to-audio path uses Meta's pretrained `facebook/musicgen-small` checkpoint through Hugging Face Transformers. The model card describes training on 20,000 hours of licensed music, including Meta's Music Initiative Sound Collection plus Shutterstock and Pond5 music. The underlying training tracks are not distributed in this repository, and this project cannot inspect them individually.

Sources:

- [MusicGen model card](https://github.com/facebookresearch/audiocraft/blob/main/model_cards/MUSICGEN_MODEL_CARD.md)
- [AudioCraft MusicGen documentation](https://github.com/facebookresearch/audiocraft/blob/main/docs/MUSICGEN.md)
- [MusicGen checkpoint on Hugging Face](https://huggingface.co/facebook/musicgen-small)

The MusicGen weights are licensed **CC-BY-NC 4.0**. They are downloaded at runtime and are not checked into Git. Review the model card and license before commercial use. The code license and the model-weight license are separate.

## Generated artifact rights

The project does not make a blanket rights claim over MusicGen audio or generated MIDI. The model-weight license, PDMX metadata, and this repository's MIT code license do not by themselves determine rights in every generated output or source transcription. Review current upstream terms and applicable third-party rights before redistribution or commercial reuse.

## Reference repository

[`s-zeng/rag-shenanigann`](https://github.com/s-zeng/rag-shenanigann) includes 512 MIDI files and a preprocessed text corpus but does not provide a per-file data provenance/license manifest. Its code repository is AGPL-3.0; that code license should not be assumed to settle the rights status of the included MIDI files. This project reads the reference code and method for analysis but does not copy its code, MIDI files, sample corpus, or model checkpoints.

## Project code and dependencies

The original code in this repository is under the MIT license. Fourmilab MIDICSV, Mido, PyTorch, Transformers, MusicGen, MidiTok, Symusic, and Hugging Face `tokenizers` are separate upstream projects with their own licenses. The REMI audit uses MidiTok and Symusic; it does not train a Hugging Face BPE/Unigram/WordPiece tokenizer. `torch-rnn` is included only as an optional documented reproduction path; no Torch7 source code is vendored here. See [`LICENSE`](../LICENSE), [`SYMBOLIC_RNN_WORKFLOW.md`](SYMBOLIC_RNN_WORKFLOW.md), and [`MODERN_TOKENIZATION.md`](MODERN_TOKENIZATION.md) for tool roles and version caveats.
