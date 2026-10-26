# Reproducibility and operation

## Environment

- Python 3.10 or newer.
- Install from this repository with `python -m pip install -e ".[app]"`.
- The first generation downloads model files from Hugging Face; keep enough disk space for the checkpoint and cache.
- CUDA is preferred for practical generation speed. The code also selects Apple MPS when available and otherwise falls back to CPU. CPU generation may be slow.

## Run recipe

```powershell
boogie-woogie-generate `
  --preset classic-honky-tonk `
  --seconds 8 `
  --seed 42 `
  --temperature 1.0 `
  --top-k 250 `
  --guidance-scale 3.0 `
  --output outputs/boogie-woogie-demo.wav
```

For a custom prompt, pass `--prompt "..."`; custom prompt text overrides the preset and any extra notes. The WAV is accompanied by `outputs/boogie-woogie-demo.json`.

## What the sidecar records

The JSON sidecar records the actual prompt, requested and measured duration, checkpoint ID, seed, sampling parameters, selected device, sample rate, channel count, Python/PyTorch/Transformers versions, generation time, and a rights note. Keep it beside the audio when sharing the output.

A seed is useful provenance, not a guarantee of bit-for-bit reproduction. Checkpoint updates, dependency changes, device differences, nondeterministic kernels, or changes in generation code can alter the waveform.

The repository's current short sample is `outputs/boogie-woogie-demo.wav`; its companion JSON file records the prompt, checkpoint, seed, parameters, software versions, and device used for that particular generation. It was generated on CPU, so runtime was substantially slower than expected on a CUDA GPU.

## Boundaries

- A prompt does not impose exact BPM, meter, notes, chord progression, bar count, or piano technique.
- The default checkpoint has a 30-second generation limit; this project is aimed at short examples.
- No generated output is committed by default. Review a take before deciding whether to publish it.
- Generated audio rights are not settled solely by the model-weight license. Review current checkpoint terms and applicable rights before reuse.

