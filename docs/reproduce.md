# Run it again

In one line: install the tool for the output you want, then use the saved checkpoint or rebuild it from the included MIDI files.

## Install

Use Python 3.10 or newer:

```powershell
python -m pip install -e ".[symbolic]"          # MIDI LSTM, Mido
python -m pip install -e ".[musicgen]"          # prompt-to-audio CLI
python -m pip install -e ".[musicgen,app]"      # prompt-to-audio CLI and Gradio app
python -m pip install -e ".[symbolic-modern]"   # optional MidiTok audit
```

MusicGen downloads `facebook/musicgen-small` the first time and may run slowly on CPU. Its weights are CC-BY-NC 4.0 and are not checked into Git.

## Make a MIDI take

The trained duration-aware checkpoint is included, so start with sampling and decoding:

```powershell
python scripts/generate_char_rnn.py `
  --seconds 10 `
  --temperature 0.8 `
  --seed 73
python scripts/unprocess.py outputs/symbolic/boogie-rnn-duration-demo.txt `
  --output-dir outputs/symbolic `
  --prefix new-take `
  --midi-backend mido
```

The `.mid` is symbolic. Open it in a MIDI player or DAW and select a piano sound.

## Rebuild and train the duration-aware model

```powershell
python scripts/normalize_type0.py
python scripts/process.py --note-encoding duration --grid-ticks-per-slot 120
python scripts/train_char_rnn.py --steps 1000 --seed 42
```

The processor defaults to the duration-aware corpus paths. Its JSON sidecar records the corpus hash, nine input files, MIDI counts, grid resolution, and Python version. The checkpoint records its training settings and corpus hash.

## Recreate the onset-only reference baseline

The old six-score corpus and checkpoint remain in the repository. To rebuild that corpus from the normalized MIDI, install Fourmilab `midicsv` and select the original six files:

```powershell
python scripts/process.py `
  --input data/normalized_midi `
  --files blastin_boogie.mid boogie_and_blues_bass_lines.mid boogie_ben.mid boogie_woogie_blues_exercises.mid pinetops_boogie_woogie_in_f.mid the_fives_boogie_woogie.mid `
  --note-encoding onset `
  --output data/processed/training_data.txt `
  --manifest data/processed/processing_manifest.csv `
  --metadata data/processed/training_data.json `
  --midicsv midicsv
```

This older text format stores note starts but not note-offs, so it cannot teach the model note lengths. That is why the current model uses the duration-aware format.

## Make a MusicGen clip over 10 seconds

```powershell
boogie-woogie-generate `
  --preset classic-honky-tonk `
  --seconds 11 `
  --seed 42 `
  --temperature 1.0 `
  --top-k 250 `
  --guidance-scale 3.0 `
  --output outputs/boogie-woogie-demo.wav
```

The JSON beside the WAV records the prompt and runtime settings.

## What the saved results show

The current 10-second LSTM take has 51 note-on events, a median note length of 240 ticks, and zero exact 8-note matches in the limited source comparison. Those are reproducible MIDI measurements, not a listener score. The old onset-only samples and current duration-aware sample are both listed in [`evaluation.json`](../outputs/symbolic/evaluation.json).

The first and final training losses are in [`training-loss-duration.csv`](../outputs/symbolic/training-loss-duration.csv). They are training readings only; no held-out evaluation is included.
