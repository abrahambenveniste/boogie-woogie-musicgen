# Data and models

In one line: the MIDI model learns from nine curated scores in this repo; MusicGen is a separate pretrained model that uses a written prompt.

## MIDI data

The nine source MIDI files come from PDMX v8 ([Zenodo DOI 10.5281/zenodo.14984509](https://doi.org/10.5281/zenodo.14984509)). The original six are *Blastin Boogie*, *Boogie and Blues Bass Lines*, *Boogie Ben*, *Boogie Woogie and Blues Piano Exercises*, *Pinetop's Boogie Woogie in F*, and *The Fives Boogie Woogie*. The three additions are *Chompin' at the Bit*, *The Squidgies Boogie*, and *Easy Boogie / Blues etude*.

The additions' PDMX tags and titles point to boogie, blues, or piano-etude material. All nine rows report `cc-zero`, `license_conflict=False`, and inclusion in `subset:no_license_conflict`. PDMX warns that public-facing and embedded license information conflicted for 12.29% of entries and recommends this subset. Those are useful source checks, not a legal opinion; PDMX metadata does not prove every arrangement or transcription is free of third-party rights. The manifest preserves the row-level metadata, IDs, tags, and SHA-256 hashes.

PDMX reports 7,458 score notes across these entries; Mido counts 7,743 positive-velocity MIDI note-on events. Those totals differ because PDMX's score parser and this project's MIDI parser count different representations. The files contain 913,466 MIDI ticks at 480 PPQN. They are a small, selected sample, with exercises and arrangements mixed in, and are not a representative collection of Boogie-Woogie.

## MIDI processing and model

Mido merges each source into a one-track Type-0 MIDI. The current model then pairs note-ons with note-offs, quantizes their start and end to a 120-tick grid, and writes one text symbol per pitch per slot. At 480 PPQN, each slot is a sixteenth note. A new attack uses a pitch token; a held note uses a different token for the same pitch; a space moves to the next slot. If a note is shorter than one grid slot, it is represented for one slot. The output stores PPQN and the first tempo for MIDI reconstruction.

The old onset-only corpus remains in `data/processed/training_data.txt` as a reference baseline. It uses the `midicsv`/text method and cannot preserve note lengths. The current duration-aware corpus is `data/processed/training_data_duration.txt`; its processing manifest and JSON sidecar record the quantization step, per-file counts, software, and SHA-256.

The local model is a character-level PyTorch LSTM with 32-dimensional embeddings, 96 hidden units, two recurrent layers, AdamW, cross-entropy, and gradient clipping. It was trained for 1,000 steps with seed 42 on CPU. The checkpoint records the vocabulary, corpus hash, encoding, grid size, settings, and versions. The training text is small enough to inspect directly, and the checkpoint can be sampled without downloading other weights.

The optional MidiTok workflow tokenizes the same normalized MIDI as REMI events. It is a representation audit; this repository does not train a Transformer on these nine scores.

## Prompt-to-audio model

The audio path uses Meta's pretrained [`facebook/musicgen-small`](https://huggingface.co/facebook/musicgen-small) through Hugging Face Transformers. The prompt describes the target ensemble and groove. MusicGen samples audio-code tokens and decodes them into a WAV file; the project records the prompt, model, duration, seed, sampling controls, device, versions, sample rate, and actual duration in JSON.

The project does not train MusicGen on the MIDI corpus. Its model card says the model was trained on 20,000 hours of licensed music, including Meta Music Initiative Sound Collection, Shutterstock, and Pond5 materials. Those training tracks are not in this repository.

The MusicGen weights are licensed **CC-BY-NC 4.0**. This is separate from the repository's MIT code license and does not settle rights in every generated output. Review the [model card](https://github.com/facebookresearch/audiocraft/blob/main/model_cards/MUSICGEN_MODEL_CARD.md) and applicable terms before reuse.

## Source citations

- Long, Novack, Berg-Kirkpatrick, and McAuley, “PDMX: A Large-Scale Public Domain MusicXML Dataset for Symbolic Music Processing,” ICASSP 2025, [DOI 10.1109/ICASSP49660.2025.10890217](https://doi.org/10.1109/ICASSP49660.2025.10890217).
- Xu et al., “Generating Symbolic Music from Natural Language Prompts using an LLM-Enhanced Dataset,” [arXiv:2410.02084](https://arxiv.org/abs/2410.02084).
- PDMX v8 data release, [Zenodo DOI 10.5281/zenodo.14984509](https://doi.org/10.5281/zenodo.14984509).
- MusicGen, [model card](https://github.com/facebookresearch/audiocraft/blob/main/model_cards/MUSICGEN_MODEL_CARD.md) and [paper](https://arxiv.org/abs/2306.05284).
