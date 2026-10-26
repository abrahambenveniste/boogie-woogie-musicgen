# Boogie-Woogie MusicGen

An applied generative-music project: prompt a pretrained text-to-music model to make short, piano-led Boogie-Woogie recordings, save them as WAV, and keep the prompt and generation settings beside each output.

> **Listen:** generate a first take with the instructions below. This repository does not yet contain a generated audio sample, so it does not present a mock or hand-made recording as model output.

## What this project does

- Uses Meta’s pretrained [`facebook/musicgen-small`](https://huggingface.co/facebook/musicgen-small) checkpoint through Hugging Face Transformers.
- Turns a concise style brief into an instrumental music prompt, with presets for classic honky-tonk, Chicago club piano, and jump-blues piano.
- Generates sampled audio and writes a WAV file plus a JSON record of the prompt, seed, model, duration, and sampling settings.
- Includes a small Gradio interface for trying prompts without editing code.

This is a **text-to-audio inference project**. It does not train or fine-tune a model, create MIDI, or retrieve examples from a RAG database. The reference repository is about ragtime, not retrieval-augmented generation; this project borrows its clear MIDI-to-listenable-output workflow while choosing a modern audio-generation model.

## Try it

Use Python 3.10 or later. A CUDA GPU makes generation much faster; CPU inference is supported but can take a long time. The first run downloads the model from Hugging Face.

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[app]"
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

## Example prompt

> Instrumental solo piano in a lively classic Boogie-Woogie style, steady swinging 12-bar blues feel, rolling walking left-hand bass, syncopated right-hand blues riffs and turnarounds, bright honky-tonk piano, intimate vintage club sound, no vocals.

Text prompts guide the model; they do **not** lock an exact BPM, chord sequence, bar count, or arrangement. Listen to the result and treat the prompt as a creative brief, not a score.

## How it works

1. Select a style preset or write a prompt.
2. Set duration, seed, temperature, top-k, and classifier-free guidance scale.
3. The text encoder represents the prompt; MusicGen’s autoregressive Transformer samples audio-code tokens conditioned on that representation.
4. The audio decoder reconstructs the sampled tokens into a waveform.
5. The project saves PCM WAV audio and a JSON sidecar so another person can see how that take was produced.

Read the [methodology](docs/METHODOLOGY.md), [data and model notes](docs/DATA_AND_MODEL.md), [reference-repository review](docs/REFERENCE_REVIEW.md), [evaluation plan](docs/EVALUATION.md), and [reproducibility guide](docs/REPRODUCIBILITY.md).

## Model and use terms

The project code is MIT-licensed. The `facebook/musicgen-small` model weights are released under **CC-BY-NC 4.0**. This is a non-commercial model checkpoint; review its license and intended-use terms before using the weights or outputs in commercial work. The model weights and its training data are not included in this repository. See [LICENSE](LICENSE) and [docs/DATA_AND_MODEL.md](docs/DATA_AND_MODEL.md).

## Acknowledgements

This project was inspired by [`s-zeng/rag-shenanigann`](https://github.com/s-zeng/rag-shenanigann), an AGPL-3.0 experiment that turns ragtime MIDI into a character stream, trains a recurrent neural network, and converts generated streams back to MIDI. No code or MIDI files from that repository are copied here. See the [reference review](docs/REFERENCE_REVIEW.md) for the detailed analysis and the reasons for the different representation and model.

MusicGen was introduced in [“Simple and Controllable Music Generation”](https://arxiv.org/abs/2306.05284) and is distributed as part of [AudioCraft](https://github.com/facebookresearch/audiocraft).
