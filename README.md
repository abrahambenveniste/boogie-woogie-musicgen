# Boogie-Woogie Music Generation

An applied generative-music project with two inspectable AI workflows: text-conditioned MusicGen audio inference, and a custom character-level PyTorch LSTM trained on Boogie-Woogie MIDI. The symbolic pipeline follows the MIDI → text → recurrent model → MIDI approach in [`s-zeng/rag-shenanigann`](https://github.com/s-zeng/rag-shenanigann), adapted to a small Boogie-Woogie dataset with an auditable source manifest.

> **Listen to the MusicGen take:** [4-second WAV](outputs/boogie-woogie-demo.wav) · [generation recipe](outputs/boogie-woogie-demo.json).  
> **Inspect a symbolic-RNN output:** [generated MIDI](outputs/symbolic/boogie-rnn-demo-000.mid) · [generated text](outputs/symbolic/boogie-rnn-demo.txt) · [generation recipe](outputs/symbolic/boogie-rnn-demo.json).

## Two generation paths

| Path | Model and data | Output | What it demonstrates |
| --- | --- | --- | --- |
| MusicGen | Pretrained `facebook/musicgen-small`; written style prompt | WAV audio | Prompt design, model inference, sampling controls, and generation metadata |
| Symbolic RNN | PyTorch character LSTM trained on six curated PDMX MIDI files | MIDI plus decoded text/CSV | Python data audit, Type-0 conversion, MIDI-to-text encoding, model training, sampling, and MIDI reconstruction |

The symbolic route adopts the reference’s core representation: PPQN and tempo headers, one pitch character for each positive-velocity note-on, and spaces for MIDI tick slots. It uses Fourmilab `midicsv`/`csvmidi` where available. The repository also includes the original Torch7 `torch-rnn` Docker recipe for compatibility and a modern PyTorch LSTM that can be trained with the project’s Python environment. See [the full symbolic workflow](docs/SYMBOLIC_RNN_WORKFLOW.md) for exact details and deviations.

MusicGen and the symbolic LSTM are separate experiments. MusicGen is pretrained and prompt-conditioned; the LSTM is trained here from symbolic MIDI and is not text-prompted. The project does not claim either model guarantees strict 12-bar form, exact tempo, or professional performance quality.

## What is included

- A prompt-driven MusicGen CLI and Gradio interface, with WAV plus JSON generation recipes.
- Six source MIDI files with PDMX IDs, licenses, source paths, SHA-256 hashes, and parsed note statistics in [`data/manifest.csv`](data/manifest.csv).
- Python scripts to normalize MIDI to Type 0, serialize MIDI through `midicsv`, train and sample a character LSTM, and decode generated text to MIDI CSV/MIDI.
- A committed symbolic-RNN checkpoint, training-loss history, and generated MIDI/text example so visitors can inspect the training and output artifacts.
- Documentation of the data selection, representation, model, tools, limitations, licenses, and reproducibility.

The six-score corpus is a transparent portfolio-scale demonstration, not a broad or balanced Boogie-Woogie benchmark. PDMX records each selected item as CC0 with `license_conflict=False`; this is dataset metadata, not an independent legal determination. See [data provenance and model terms](docs/DATA_AND_MODEL.md).

### Recorded symbolic run

The committed corpus contains **6 MIDI files**, **672,098 tick slots**, **5,390 positive-velocity note-on events**, and **677,566 bytes** of processed text. The included CPU training run used 1,000 stochastic optimization steps (seed 42); its first and last minibatch cross-entropy values were 4.2998 and 0.0480. Those are training-loss readings, not a held-out performance score. The included generated MIDI is 5 seconds at 480 PPQN and 120 BPM, with 38 decoded note-on events spanning pitches 28–77. The checkpoint, training log, generated text, MIDI CSV, MIDI, and JSON recipes are in the repository so the run can be inspected end to end.

## Try it

Use Python 3.10 or later. A CUDA GPU makes MusicGen inference and LSTM training faster; CPU execution is supported. The first MusicGen run downloads its checkpoint from Hugging Face.

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[app,symbolic]"
```

Generate a WAV from the command line:

```powershell
boogie-woogie-generate `
  --preset classic-honky-tonk `
  --seconds 8 `
  --seed 42 `
  --output outputs/boogie-woogie-demo.wav
```

Or launch the prompt studio:

```powershell
boogie-woogie-app
```

The default model generates no more than 30 seconds per take. Short takes are easier to compare and are less likely to drift away from the requested groove. You can set a custom prompt with `--prompt`; it takes precedence over `--preset`.

## Train and generate symbolic MIDI

The checked-in MIDI corpus is already preprocessed. To reproduce it from the raw MIDI files, install [Fourmilab MIDIcsv](https://www.fourmilab.ch/webtools/midicsv/) and run:

```powershell
python scripts/normalize_type0.py
python scripts/process.py --midicsv midicsv
python scripts/train_char_rnn.py --steps 1000 --seed 42
python scripts/generate_char_rnn.py --ticks 4800 --seed 73
python scripts/unprocess.py outputs/symbolic/boogie-rnn-demo.txt `
  --prefix boogie-rnn-demo --midi-backend csvmidi --csvmidi csvmidi
```

If `csvmidi` is unavailable, `unprocess.py` can write the MIDI with its Mido fallback. The original Dockerized Torch7 recipe and its commands are documented separately; the legacy container is not needed for the PyTorch run above.

## Example prompt

> Instrumental solo piano in a lively classic Boogie-Woogie style, steady swinging 12-bar blues feel, rolling walking left-hand bass, syncopated right-hand blues riffs and turnarounds, bright honky-tonk piano, intimate vintage club sound, no vocals.

Text prompts guide the model; they do **not** lock an exact BPM, chord sequence, bar count, or arrangement. Listen to the result and treat the prompt as a creative brief, not a score.

## How the MusicGen path works

1. Select a style preset or write a prompt.
2. Set duration, seed, temperature, top-k, and classifier-free guidance scale.
3. The text encoder represents the prompt; MusicGen’s autoregressive Transformer samples audio-code tokens conditioned on that representation.
4. The audio decoder reconstructs the sampled tokens into a waveform.
5. The project saves PCM WAV audio and a JSON sidecar so another person can see how that take was produced.

Read the [methodology](docs/METHODOLOGY.md), [symbolic RNN workflow](docs/SYMBOLIC_RNN_WORKFLOW.md), [data and model notes](docs/DATA_AND_MODEL.md), [reference-repository review](docs/REFERENCE_REVIEW.md), [evaluation plan](docs/EVALUATION.md), and [reproducibility guide](docs/REPRODUCIBILITY.md).

## Model and use terms

The project code is MIT-licensed. The `facebook/musicgen-small` model weights are released under **CC-BY-NC 4.0**, a non-commercial checkpoint. The symbolic training MIDI files have per-item license metadata recorded in the manifest. Model licenses and dataset metadata do not settle every question about generated outputs; see [LICENSE](LICENSE) and [docs/DATA_AND_MODEL.md](docs/DATA_AND_MODEL.md).

## Acknowledgements

The symbolic pipeline was inspired by [`s-zeng/rag-shenanigann`](https://github.com/s-zeng/rag-shenanigann), an AGPL-3.0 experiment that turns ragtime MIDI into a character stream, trains a recurrent neural network, and converts generated streams back to MIDI. No code or MIDI files from that repository are copied here; this project independently implements the described method and uses a separate Boogie-Woogie dataset. See the [reference review](docs/REFERENCE_REVIEW.md) for a detailed analysis.

MusicGen was introduced in [“Simple and Controllable Music Generation”](https://arxiv.org/abs/2306.05284) and is distributed as part of [AudioCraft](https://github.com/facebookresearch/audiocraft).
