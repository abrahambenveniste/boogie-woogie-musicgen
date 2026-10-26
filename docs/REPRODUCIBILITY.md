# Reproducibility and operation

## Python environment

Use Python 3.10 or newer. Install only the dependencies for the workflow you plan to run:

```powershell
python -m pip install -e ".[musicgen]"          # WAV generation CLI
python -m pip install -e ".[musicgen,app]"      # WAV CLI and Gradio interface
python -m pip install -e ".[symbolic]"          # MIDI generation/training and Mido tools
python -m pip install -e ".[musicgen,app,symbolic]"  # all features
```

The symbolic-only extra installs PyTorch and Mido without the Transformers, audio, or Gradio packages. The audio interface requires both the `musicgen` and `app` extras.

MusicGen downloads `facebook/musicgen-small` from Hugging Face at first use. Its CC-BY-NC 4.0 weights are not stored in this repository. CUDA is preferred for practical speed; CPU fallback works but can be slow.

## Rebuild the symbolic corpus

Install Fourmilab MIDICSV 1.1, which supplies both `midicsv` and `csvmidi`, and place those executables on `PATH` or provide explicit executable paths. Then run:

```powershell
python scripts/normalize_type0.py `
  --input data/raw_midi `
  --output data/normalized_midi `
  --manifest data/processed/normalization_manifest.csv
python scripts/process.py `
  --input data/normalized_midi `
  --output data/processed/training_data.txt `
  --manifest data/processed/processing_manifest.csv `
  --metadata data/processed/training_data.json `
  --midicsv midicsv `
  --midicsv-version "Fourmilab MIDICSV 1.1"
```

`data/manifest.csv` contains PDMX source paths, IDs, metadata, and raw file hashes. `data/processed/processing_manifest.csv` contains the actual PPQN, first tempo, tick slots, note-on count, and encoded length measured by this project's processing run.

## Train and sample the PyTorch LSTM

The committed demonstration uses a checkpoint and JSON sidecar under `models/`. To reproduce a new run, keep the same corpus bytes, Python/PyTorch versions, model settings, and seed:

```powershell
python scripts/train_char_rnn.py `
  --input data/processed/training_data.txt `
  --checkpoint models/boogie-char-lstm.pt `
  --log outputs/symbolic/training-loss.csv `
  --steps 1000 `
  --sequence-length 128 `
  --batch-size 8 `
  --embedding-size 32 `
  --hidden-size 96 `
  --layers 2 `
  --learning-rate 0.002 `
  --seed 42
python scripts/generate_char_rnn.py `
  --checkpoint models/boogie-char-lstm.pt `
  --output outputs/symbolic/boogie-rnn-demo.txt `
  --ticks 4800 `
  --temperature 1.0 `
  --seed 73
```

The checkpoint JSON records corpus SHA-256, vocabulary, architecture, training hyperparameters, seed, device, library versions, final cross-entropy, and creation time. The output JSON records checkpoint and corpus hashes, generation seed, temperature, tick count, tempo, PPQN, device, and output length. Random seeds do not ensure byte-for-byte identical results across all hardware/library versions.

## Decode to MIDI

```powershell
python scripts/unprocess.py outputs/symbolic/boogie-rnn-demo.txt `
  --output-dir outputs/symbolic `
  --prefix boogie-rnn-demo `
  --midi-backend csvmidi `
  --csvmidi csvmidi `
  --csvmidi-version "Fourmilab MIDICSV 1.1"
```

This writes a `.csv` intermediate and calls `csvmidi -z` to produce the MIDI file. If `csvmidi` is not installed, set `--midi-backend mido`; the Mido fallback implements the same tick/pitch decode and writes a one-track Type-0 MIDI. `--midi-backend auto` chooses `csvmidi` when available and otherwise uses Mido.

The generated MIDI is symbolic. To make a WAV rendering, open it in a DAW or use a local SoundFont renderer such as TiMidity++; the soundfont is a separate dependency and is not bundled here.

## Reproduce the controlled seed comparison

The committed comparison holds the checkpoint, 4,800 tick slots, temperature 1.0, CPU device, and Mido decoder fixed. Seeds 73, 74, and 75 produce separate five-second MIDI takes. For each seed, generate and decode a take; for example:

```powershell
python scripts/generate_char_rnn.py `
  --checkpoint models/boogie-char-lstm.pt `
  --output outputs/symbolic/boogie-rnn-seed-073.txt `
  --ticks 4800 --temperature 1.0 --seed 73 --device cpu
python scripts/unprocess.py outputs/symbolic/boogie-rnn-seed-073.txt `
  --output-dir outputs/symbolic `
  --prefix boogie-rnn-seed-073 --midi-backend mido
```

Repeat with seeds `74` and `75`, changing both the output/prefix suffix and `--seed`. Then recreate the metrics:

```powershell
python scripts/evaluate_symbolic.py `
  --generated outputs/symbolic/boogie-rnn-seed-073-000.mid `
  --generated outputs/symbolic/boogie-rnn-seed-074-000.mid `
  --generated outputs/symbolic/boogie-rnn-seed-075-000.mid
```

The MIDI outputs are short examples, not complete songs. Random seeds do not guarantee identical files across all hardware or library versions; each run's JSON sidecar records its settings and environment.

## Fresh-checkout smoke check

On 2026-10-26, a fresh shallow clone of the public repository generated, decoded, and evaluated another five-second Type-0 MIDI take (seed 76). This used the already-installed local Python environment (Python 3.13.15 and CPU PyTorch 2.14.1); it confirms the committed checkout, checkpoint, and symbolic scripts work together. It did not reinstall dependencies into an empty environment, so it is not a clean-install test. The symbolic workflow did not download MusicGen weights.

## Legacy Torch7 route

The exact historical workflow uses `crisbal/torch-rnn:base` and its upstream Torch7 `torch-rnn` checkout. See [`SYMBOLIC_RNN_WORKFLOW.md`](SYMBOLIC_RNN_WORKFLOW.md) for `scripts/preprocess.py`, `th train.lua`, and `th sample.lua` commands. The Docker image is based on Ubuntu 14.04 and is not pinned to a modern, maintained software stack. Docker was unavailable in the authoring environment, so the committed model and generated MIDI use the modern PyTorch implementation instead.

## MusicGen inference recipe

The committed audio sample uses the recipe in `outputs/boogie-woogie-demo.json`. A new take can be generated with:

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

The first call downloads model weights. Runtime, waveform details, and sampling settings are written to the matching JSON sidecar. Text prompts do not hard-constrain musical form or exact notes.

