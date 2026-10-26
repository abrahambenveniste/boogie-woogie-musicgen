# Boogie-Woogie MusicGen

I built this project to try two ways of making Boogie-Woogie with AI: prompt a pretrained audio model, or train a small MIDI model on scores I can inspect.

## Listen

- **Audio:** [play the 11-second MusicGen example](https://raw.githubusercontent.com/abrahambenveniste/boogie-woogie-musicgen/main/outputs/boogie-woogie-demo.wav) · [prompt and settings](outputs/boogie-woogie-demo.json)
- **MIDI:** [download the 10-second LSTM example](outputs/symbolic/boogie-rnn-duration-demo-000.mid) · [generation settings](outputs/symbolic/boogie-rnn-duration-demo.json) · [file analysis](outputs/symbolic/evaluation.json)

The WAV plays in a browser. Open the MIDI in a piano app or DAW.

## Generate music

### Prompt-to-audio

```bash
python -m pip install -e ".[musicgen]"
boogie-woogie-generate --preset classic-honky-tonk --seconds 11 --seed 42 --output outputs/my-take.wav
```

The first run downloads Meta's `facebook/musicgen-small` checkpoint. You can also pass your own prompt with `--prompt`.

### Score-trained MIDI

The trained checkpoint is included, so sampling does not require another training run:

```bash
python -m pip install -e ".[symbolic]"
python scripts/generate_char_rnn.py --seconds 10 --temperature 0.8 --seed 73
python scripts/unprocess.py outputs/symbolic/boogie-rnn-duration-demo.txt --prefix my-take --midi-backend mido
```

To rebuild the corpus and train the model:

```bash
python scripts/normalize_type0.py
python scripts/process.py --note-encoding duration --grid-ticks-per-slot 120
python scripts/train_char_rnn.py --steps 1000 --seed 42
```

## The scores behind the MIDI model

I trained the LSTM on nine source scores from [PDMX v8](https://doi.org/10.5281/zenodo.14984509). Counts below are positive-velocity note-on events parsed from the local MIDI files.

| Score | Note-on events |
| --- | ---: |
| *Blastin Boogie* | 321 |
| *Boogie and Blues Bass Lines* | 711 |
| *Boogie Ben* | 163 |
| *Boogie Woogie and Blues Piano Exersices* (title spelling in PDMX) | 339 |
| *Chompin' at the Bit* | 1,258 |
| *Easy Boogie / Blues etude* | 171 |
| *Pinetop's Boogie Woogie in F* | 2,416 |
| *The Fives Boogie Woogie piano solo* | 1,440 |
| *The Squidgies Boogie* | 924 |
| **Total** | **7,743** |

The source IDs, metadata, license fields, and file hashes are in [`data/manifest.csv`](data/manifest.csv). PDMX labels these files CC0 and marks them as having no license conflict; these dataset fields are not an independent rights review.

## How it works

The MIDI path follows the reference project's broad workflow—MIDI → text → recurrent model → MIDI—while adding note lengths:

1. Mido merges each source score into one Type-0 MIDI track.
2. The processor pairs note-ons with note-offs and puts notes on a 120-tick grid. At 480 PPQN, one slot is a sixteenth note.
3. A pitch token marks a new note; a hold token keeps it sounding; a space advances one slot.
4. A character-level PyTorch LSTM predicts the next token from the score corpus.
5. The sampler generates a token stream, and the decoder turns grid positions and holds back into MIDI note-on and note-off events.

The reference project used `midicsv`, Torch7 `torch-rnn` in Docker, and `csvmidi`. This repo keeps its simple MIDI/text/RNN/MIDI idea and its onset-only baseline, and uses Mido and PyTorch for the duration-aware model. The optional MidiTok script audits the same scores with REMI tokens; it does not train a Transformer. MusicGen is a separate pretrained prompt-to-audio model and is not trained on these nine scores.

## What the current results say

The new 10-second MIDI sample has 51 note starts. Its note lengths are 120–720 ticks, with a median of 240 ticks (250 ms at 120 BPM). That fixes the old representation's 1–2 tick notes, which happened because it stored attacks but no releases.

My first listen: the MIDI LSTM sounds somewhat musical and steadier in tempo; the MusicGen example sounds poor, with a pronounced tempo problem. This is a subjective impression, not a measured BPM comparison or structured listening study.

The first training run used 1,000 steps; training cross-entropy fell from 4.9853 to 1.0953. There is no held-out test, so this does not demonstrate generalization. Nine scores are a small, mixed corpus, and a sixteenth-note grid cannot exactly represent every swing triplet.

## Project notes

- [Method, reference workflow, data provenance, and tools](docs/method.md)
- [Results, limitations, and next steps](docs/results.md)
- [Dataset files and processing details](data/README.md)

The code is MIT-licensed. The downloaded MusicGen weights are CC-BY-NC 4.0; review the [official MusicGen model card](https://github.com/facebookresearch/audiocraft/blob/main/model_cards/MUSICGEN_MODEL_CARD.md) before reuse.
