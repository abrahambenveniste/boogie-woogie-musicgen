# Boogie-Woogie MusicGen

I wanted to make a music project that people can listen to and inspect. This repo has two ways to generate Boogie-Woogie: a pretrained model makes audio from a prompt, and a small LSTM learns note patterns from MIDI scores and writes new MIDI.

## Listen

- **MusicGen:** [play the 10+ second WAV](https://raw.githubusercontent.com/abrahambenveniste/boogie-woogie-musicgen/main/outputs/boogie-woogie-demo.wav) · [prompt and settings](outputs/boogie-woogie-demo.json)
- **MIDI LSTM:** [download the 10-second MIDI](outputs/symbolic/boogie-rnn-duration-demo-000.mid) · [generation recipe](outputs/symbolic/boogie-rnn-duration-demo.json) · [analysis](outputs/symbolic/evaluation.json)

The MIDI file needs a MIDI player or DAW. The MusicGen link plays in a browser.

## Make your own

### Generate audio from a prompt

```bash
python -m pip install -e ".[musicgen]"
boogie-woogie-generate --preset classic-honky-tonk --seconds 11 --seed 42 --output outputs/my-take.wav
```

The first run downloads Meta's `facebook/musicgen-small` model. MusicGen's WAV is slightly shorter than the requested time, so 11 seconds makes a file over 10 seconds. You can replace the preset with your own `--prompt`.

### Generate MIDI from the trained LSTM

The saved checkpoint is included, so you can sample without training again:

```bash
python -m pip install -e ".[symbolic]"
python scripts/generate_char_rnn.py --seconds 10 --temperature 0.8 --seed 73
python scripts/unprocess.py outputs/symbolic/boogie-rnn-duration-demo.txt --prefix my-take --midi-backend mido
```

The MIDI and its settings are saved in `outputs/symbolic/`.

To rebuild and train the duration-aware model from the nine included scores:

```bash
python scripts/normalize_type0.py
python scripts/process.py --note-encoding duration --grid-ticks-per-slot 120
python scripts/train_char_rnn.py --steps 1000 --seed 42
```

The 120-tick grid is a sixteenth note at 480 PPQN. One onset token marks a new note; a separate hold token keeps it sounding. This keeps the same MIDI → text → recurrent model → MIDI approach as [`s-zeng/rag-shenanigann`](https://github.com/s-zeng/rag-shenanigann), while preserving note lengths for the new model. The older onset-only text corpus remains available as a reference baseline.

## What I have learned so far

- The original onset-only format dropped note-offs. Its generated MIDI notes lasted just 1–2 ticks, which is why it sounded like a flurry of clicks.
- The new encoding keeps note attacks and note holds on a 16th-note grid. The first 10-second sample has 51 note starts per 10 seconds; its median note lasts 240 ticks (about 250 ms at 120 BPM).
- That is a measurable playback improvement, but it does not prove the phrases sound good. I have not run a structured listening study, and nine scores are still a small training set.
- MusicGen and the LSTM do different things: MusicGen follows a written prompt and outputs audio; the LSTM learns from the MIDI scores and outputs MIDI.

## Data and limits

The LSTM learns from nine Boogie-Woogie, blues, and piano-etude scores selected from PDMX v8. They contain 7,743 locally parsed note-on events. PDMX reports CC0 and no license conflict for all nine; the original source IDs, metadata, and SHA-256 hashes are in [`data/manifest.csv`](data/manifest.csv). Those fields record the dataset's claims and checks; they are not an independent rights review.

The first LSTM run used 1,000 training steps. Its sampled training loss fell from 4.9853 to 1.0953, but there is no held-out set, so that number says nothing about how well the model generalizes. Neither model guarantees an exact tempo, chord progression, 12-bar form, or convincing piano performance.

MusicGen's weights are licensed **CC-BY-NC 4.0**. The code is MIT-licensed. Review those terms before reuse.

## Project map

- `data/` — nine source scores, manifests, Type-0 MIDI, and both old and duration-aware text corpora.
- `docs/` — the method, data provenance, reference review, results, and rerun steps.
- `models/` — the trained LSTM checkpoints and settings.
- `outputs/` — audio and MIDI examples, recipes, and analysis reports.
- `scripts/` — MIDI preparation, training, sampling, decoding, and analysis.
- `src/` — MusicGen prompts, command-line tool, and small web app.

### Read next

- [How it works](docs/how-it-works.md)
- [Data and models](docs/data-and-models.md)
- [Results and limitations](docs/results-and-next-steps.md)
- [Reference project review](docs/reference.md)
- [Reproduce the project](docs/reproduce.md)
- [MIDI tokenization audit](docs/midi-tokens.md)
