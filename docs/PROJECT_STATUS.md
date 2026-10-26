# Project status

## Implemented in this repository

- MusicGen small inference wrapper with auto-detected CUDA, Apple MPS, or CPU device.
- Boogie-Woogie prompt presets and optional free-text direction.
- CLI and Gradio prompt studio.
- WAV output and a metadata JSON sidecar for each generation.
- Technical methodology, data/model provenance, licensing, reference analysis, reproducibility, and evaluation documentation.

## Not claimed

- No custom model training or fine-tuning.
- No project-owned Boogie-Woogie training dataset.
- No generated audio sample or benchmark result has been added yet.
- No exact BPM, MIDI, score, or song-form guarantee.

## Next iteration

1. Generate and listen to several short takes on a CUDA-capable machine.
2. Choose one representative output, retain its JSON recipe, and publish it only after listening and checking applicable model terms.
3. Run the small listening protocol in `EVALUATION.md` and record the actual results.
4. Explore melody conditioning or MIDI-aware constraints only if exact note control becomes a project requirement.
