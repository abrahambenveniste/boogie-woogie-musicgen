# Boogie-Woogie MusicGen

I wanted to make an AI-music project you can listen to and inspect. This repo has two experiments: a pretrained model turns a written prompt into audio, and a small model learns note patterns from MIDI and generates a new MIDI clip.

Both are short experiments, not finished songs. The MIDI model learns from just six scores, so I keep the data, settings, outputs, and limitations visible.

## Have a listen

- **MusicGen:** [listen to the WAV](https://raw.githubusercontent.com/abrahambenveniste/boogie-woogie-musicgen/main/outputs/boogie-woogie-demo.wav) · [see the prompt and settings](outputs/boogie-woogie-demo.json)
- **MIDI model:** [download a generated MIDI](https://raw.githubusercontent.com/abrahambenveniste/boogie-woogie-musicgen/main/outputs/symbolic/boogie-rnn-demo-000.mid) · [see the note stream](outputs/symbolic/boogie-rnn-demo.txt) · [see its settings](outputs/symbolic/boogie-rnn-demo.json)
- **Three more MIDI takes:** [seed 73](outputs/symbolic/boogie-rnn-seed-073-000.mid) · [seed 74](outputs/symbolic/boogie-rnn-seed-074-000.mid) · [seed 75](outputs/symbolic/boogie-rnn-seed-075-000.mid)

## What we know so far

- MusicGen generated a 3.94-second mono clip at 32 kHz. A listener still needs to judge how well it follows the Boogie-Woogie prompt.
- The symbolic LSTM trains and writes valid MIDI, but its current notes last about 1–2 milliseconds; this is a data-format problem we need to fix before judging it as a piano performance.
- The loss fell during training, but it was measured on sampled windows from only six scores; there is no held-out quality result yet.

## Make a short audio clip

Install Python 3.10+ and the MusicGen tools:

```bash
python -m pip install -e ".[musicgen]"
```

Then run:

```bash
boogie-woogie-generate --preset classic-honky-tonk --seconds 8 --seed 42 --output outputs/my-take.wav
```

The first run downloads Meta's `facebook/musicgen-small` checkpoint. You can also write a prompt with `--prompt`, or launch the small web interface with `python -m pip install -e ".[musicgen,app]"` and `boogie-woogie-app`.

## Make a MIDI clip

The MIDI model is trained on this project's six scores. The processed text corpus is already included, so you can train and sample without rebuilding it:

```bash
python -m pip install -e ".[symbolic]"
python scripts/train_char_rnn.py --steps 1000 --seed 42
python scripts/generate_char_rnn.py --ticks 4800 --seed 73
```

To rebuild the text corpus from the raw MIDI, install Fourmilab's `midicsv` and `csvmidi`, then run:

```bash
python scripts/normalize_type0.py
python scripts/process.py --midicsv midicsv
python scripts/train_char_rnn.py --steps 1000 --seed 42
python scripts/generate_char_rnn.py --ticks 4800 --seed 73
python scripts/unprocess.py outputs/symbolic/boogie-rnn-demo.txt --prefix boogie-rnn-demo --midi-backend csvmidi --csvmidi csvmidi
```

If `csvmidi` is not installed, the last command can use the Mido fallback. See [the full MIDI walkthrough](docs/how-it-works.md) for the exact steps and the original Torch7 option.

## How the two experiments work

### Prompt to audio

1. I describe the sound I want: piano, rolling bass, blues riffs, and a swinging feel.
2. MusicGen turns that prompt into audio tokens and decodes them into a WAV file.
3. The project saves the prompt and generation settings beside the audio, so each take can be checked or repeated.

The prompt is a guide; it does not lock the tempo, chord changes, or 12-bar form.

### MIDI to model to MIDI

1. The corpus uses six Boogie-Woogie or blues-piano scores from PDMX v8, with source details and file hashes recorded.
2. A conversion script merges each score into one MIDI track; `midicsv` reads its tempo, timing, and note events.
3. The processing script turns note pitches into characters on a tick grid; spaces mark ticks without a note.
4. A PyTorch LSTM learned to predict the next character and sampled a new stream.
5. A decoder converts that stream back into MIDI so it can be opened, edited, or played.

This follows the MIDI → text → recurrent model → MIDI idea in [`s-zeng/rag-shenanigann`](https://github.com/s-zeng/rag-shenanigann). The code and Boogie-Woogie data here are separate; no code or MIDI files were copied from that project. The reference's original Torch7 recipe is documented alongside our runnable PyTorch version.

## What is in the data

The six MIDI files contain **5,390 note-on events** across **672,098 MIDI tick slots**. Their source records, license fields, file hashes, and processing counts are in [`data/manifest.csv`](data/manifest.csv) and [`data/processed/processing_manifest.csv`](data/processed/processing_manifest.csv).

PDMX marks the selected entries as CC0 with no recorded license conflict. Those fields are useful provenance, not a legal review; the dataset is also small and should not be treated as representative of the whole genre.

The saved LSTM run used 1,000 training steps. Its first and last minibatch losses were 4.2998 and 0.0480; these are training readings, not a held-out quality score. The three saved MIDI takes are five seconds long. The [evaluation report](outputs/symbolic/evaluation.json) compares their notes with the source scores.

There is also a second view of the MIDI files from MidiTok's REMI tokenizer. It produced **25,158 tokens** and **5,390 note tokens**; it is a tokenization audit, not a Transformer trained on this small corpus. The [report](outputs/symbolic/remi-token-audit.json) includes a channel detail: one source score is marked as percussion by MidiTok.

## Project map

- `data/` — six source scores, their Type-0 copies, processed model input, and source manifests.
- `docs/` — six focused guides covering the workflow, data, results, reference, and reruns.
- `models/` — the saved PyTorch LSTM checkpoint and its settings.
- `outputs/` — the listenable MusicGen WAV, generated MIDI examples, recipes, and analysis reports.
- `scripts/` — commands to prepare MIDI, train and sample the LSTM, tokenize, and inspect results.
- `src/` — the MusicGen generator, prompt presets, command-line tool, and small web app.

## Project notes

- [How it works](docs/how-it-works.md) — both generation paths and the full MIDI walkthrough.
- [Data and models](docs/data-and-models.md) — sources, model details, and license notes.
- [Results and next steps](docs/results-and-next-steps.md) — findings, evaluation, limits, and what to improve.
- [MIDI tokens](docs/midi-tokens.md) — the optional MidiTok REMI audit.
- [Reference project](docs/reference.md) — what `rag-shenanigann` does and what this project adapts.
- [Run it again](docs/reproduce.md) — installs, commands, seeds, and saved run details.

## A few things to know

- MusicGen makes audio directly; the LSTM makes symbolic MIDI. They use different models and different inputs.
- Neither path guarantees a convincing performance or a strict 12-bar blues structure.
- The MusicGen weights are licensed **CC-BY-NC 4.0**. Project code is MIT-licensed; PDMX source records are listed in the data manifest.

The MusicGen experiment uses Meta's [`facebook/musicgen-small`](https://huggingface.co/facebook/musicgen-small), introduced in [“Simple and Controllable Music Generation”](https://arxiv.org/abs/2306.05284). The symbolic experiment is inspired by [`rag-shenanigann`](https://github.com/s-zeng/rag-shenanigann).

