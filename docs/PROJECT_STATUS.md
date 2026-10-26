# Project status

## Current scope decision

- Keep the symbolic training corpus fixed at the six source MIDI files listed in `data/manifest.csv` for this baseline. This is the project owner's chosen scope, not a claim that six pieces represent the full genre.
- Preserve the six-item corpus and its recorded source IDs, license metadata, hashes, and processing results so the baseline remains auditable.
- Treat future corpus expansions as separately documented experiments, with provenance and license review for every added file.
- Keep the pretrained MusicGen prompt experiment distinct: it is not trained on these six MIDI files.

## Implemented

- Prompt-conditioned MusicGen inference with Boogie-Woogie presets, CLI, Gradio UI, WAV output, and JSON provenance.
- A parallel symbolic pipeline based on the MIDI → text → RNN → MIDI workflow documented in `s-zeng/rag-shenanigann`.
- Six PDMX v8 source MIDI files with source IDs, per-item license fields, no-conflict flags, file hashes, and source/local note counts.
- Python/Mido Type-0 normalization, actual `midicsv` parsing, deterministic character-corpus generation, per-file processing metrics, and `csvmidi`-based decode.
- A PyTorch character LSTM training and sampling implementation, plus the legacy Torch7 Docker training recipe.
- Three controlled symbolic MIDI takes from seeds 73, 74, and 75, with text, MIDI CSV, MIDI, and per-run metadata.
- A reproducible Mido-based MIDI diagnostics script and a committed JSON comparison of the six source scores with all three generated takes.
- A fresh public checkout reproduced an additional five-second symbolic MIDI take using the available Python environment; dependency installation from a blank environment remains unverified.
- Documentation for both model paths, corpus curation and licenses, exact representation, tool roles, limitations, and reproducibility.

## Not claimed

- The six-score MIDI corpus is too small to support claims of broad musical generalization or a benchmark result.
- No structured listening study has been completed. The samples are demonstrations, not evaluated performance claims.
- The MIDI character codec does not preserve note durations, velocities, part labels, or expressive controls. Reconstructed note lengths are inferred from the generated tick sequence.
- MusicGen prompts and the symbolic RNN do not guarantee exact BPM, chord progression, 12-bar form, or piano technique.
- The documented legacy Torch7 container was not run in the authoring environment; the included checkpoint uses the runnable PyTorch implementation.

## Suggested next work

1. Listen to the MusicGen WAV and three symbolic takes, then record human scores using `EVALUATION.md`.
2. Compare LSTM temperatures while holding the six-file corpus, checkpoint, tick count, and seed fixed; save each recipe.
3. Consider event-based or duration-aware MIDI encodings as a separately documented follow-up while keeping this reference-compatible baseline intact.

