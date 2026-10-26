# Project status

## Implemented

- Prompt-conditioned MusicGen inference with Boogie-Woogie presets, CLI, Gradio UI, WAV output, and JSON provenance.
- A parallel symbolic pipeline based on the MIDI → text → RNN → MIDI workflow documented in `s-zeng/rag-shenanigann`.
- Six PDMX v8 source MIDI files with source IDs, per-item license fields, no-conflict flags, file hashes, and source/local note counts.
- Python/Mido Type-0 normalization, actual `midicsv` parsing, deterministic character-corpus generation, per-file processing metrics, and `csvmidi`-based decode.
- A PyTorch character LSTM training and sampling implementation, plus the legacy Torch7 Docker training recipe.
- A generated symbolic MIDI/text example, training checkpoint and metadata, and a per-step cross-entropy log.
- Documentation for both model paths, corpus curation and licenses, exact representation, tool roles, limitations, and reproducibility.

## Not claimed

- The six-score MIDI corpus is too small to support claims of broad musical generalization or a benchmark result.
- No structured listening study has been completed. The samples are demonstrations, not evaluated performance claims.
- The MIDI character codec does not preserve note durations, velocities, part labels, or expressive controls. Reconstructed note lengths are inferred from the generated tick sequence.
- MusicGen prompts and the symbolic RNN do not guarantee exact BPM, chord progression, 12-bar form, or piano technique.
- The documented legacy Torch7 container was not run in the authoring environment; the included checkpoint uses the runnable PyTorch implementation.

## Suggested next work

1. Listen to the MusicGen WAV and generated MIDI rendering, then record human scores using `EVALUATION.md`.
2. Grow the curated MIDI corpus only after reviewing each candidate's provenance and per-item license fields.
3. Compare the character LSTM with event-based or duration-aware MIDI encodings while keeping the reference-compatible baseline intact.
