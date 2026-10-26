# Methodology

## Objective

Generate short, listenable, instrumental Boogie-Woogie-inspired piano audio from a human-written text brief. The project prioritizes a reproducible, inspectable inference workflow over training a new foundation model.

## Model

The default checkpoint is Meta’s `facebook/musicgen-small`, a 300-million-parameter text-to-music model. MusicGen uses a frozen text encoder to represent the written prompt, then an autoregressive Transformer to predict discrete audio codes. An EnCodec audio decoder converts those codes to waveform audio. The released MusicGen setup models four codebooks at 50 frames per second and produces 32 kHz audio.

The implementation uses the `MusicgenForConditionalGeneration` and `AutoProcessor` interfaces from Hugging Face Transformers. It samples tokens (`do_sample=True`) and exposes temperature, top-k, and classifier-free guidance scale. Duration maps to the model’s frame budget at approximately 50 generated frames per second. A fixed random seed makes a generation attempt easier to reproduce, but does not promise bit-identical output across different hardware, library versions, or kernels.

Primary references:

- [MusicGen paper: “Simple and Controllable Music Generation”](https://arxiv.org/abs/2306.05284)
- [AudioCraft MusicGen technical documentation](https://github.com/facebookresearch/audiocraft/blob/main/docs/MUSICGEN.md)
- [Hugging Face MusicGen model documentation](https://huggingface.co/docs/transformers/en/model_doc/musicgen)
- [MusicGen model card](https://github.com/facebookresearch/audiocraft/blob/main/model_cards/MUSICGEN_MODEL_CARD.md)

## Boogie-Woogie prompting

The prompt presets make musical intent explicit across a few dimensions:

| Dimension | Prompt language used |
| --- | --- |
| Style | Boogie-Woogie, blues, jump blues |
| Ensemble | Solo piano, piano foreground, instrumental |
| Groove | Swing, shuffle, driving or relaxed |
| Piano role | Repeating left-hand bass, syncopated right-hand riffs and fills |
| Form/color | 12-bar blues feel, turnarounds, club or dance-hall character |
| Exclusions | No vocals |

These are soft text conditions. The checkpoint does not provide hard constraints for BPM, meter, chord progression, hand independence, bar count, or a specific piano technique. It may add other instruments or fail to follow parts of a prompt. The audio must be listened to and judged as a generated interpretation.

## Why audio generation instead of the reference’s MIDI stream

The reference serializes MIDI note events into a character stream and asks a recurrent network to continue it. That is compact and yields MIDI after decoding, but its scripts discard note duration and velocity and reconstruct timing from character positions. This project uses a text-conditioned audio model instead: it can produce a directly listenable WAV without a MIDI tokenizer or a separate synthesizer. The trade-off is that the output is audio rather than editable MIDI, and exact note-level musical constraints are less inspectable.

## Generation recipe

Each run records the prompt, model ID, requested and measured duration, seed, device, sampling parameters, sample rate, channel count, Python version, and library versions in a JSON file beside the WAV. The model ID defaults to the public `facebook/musicgen-small` checkpoint and may be overridden on the CLI. The weights are downloaded at first use and are not stored in Git.

## Evaluation approach

There are no performance claims or generated-sample scores in this repository yet. See the [evaluation plan](EVALUATION.md) for a small listening protocol that separates style fit, groove, prompt adherence, audio quality, and repetition. It avoids presenting subjective judgments as objective model benchmarks.
