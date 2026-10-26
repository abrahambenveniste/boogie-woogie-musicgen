# How it works

In one line: MusicGen turns a written brief into audio; the MIDI LSTM learns from nine scores and turns its sampled note stream back into MIDI.

## Audio from a prompt

The MusicGen path uses Meta's pretrained `facebook/musicgen-small` through Transformers. A prompt names the piano, bass role, blues riffs, shuffle feel, and intended form; the model samples audio-code tokens and decodes them to a WAV file. The JSON beside each WAV records the prompt, model, seed, duration, settings, device, and software versions.

The prompt is a guide. It does not force a precise BPM, chord progression, hand pattern, or 12-bar structure. The weights are licensed CC-BY-NC 4.0; see [data and models](data-and-models.md).

## Notes from MIDI

The symbolic experiment follows the reference project's broad workflow: MIDI → text → recurrent model → MIDI. It differs in the detail of the text encoding so note lengths survive.

1. Mido merges each source score to one Type-0 track. The full source list and hashes are in `data/manifest.csv`.
2. The current processor pairs note-ons with note-offs and maps each note to a 120-tick grid at 480 PPQN. That is a sixteenth-note grid. Start and end times are rounded to the nearest slot; notes shorter than one slot become one slot long.
3. A new note uses a pitch token; the same pitch held into the next slot uses a separate hold token. A space marks the next grid slot. Three newlines separate source scores. The text corpus keeps PPQN and the first tempo of each score.
4. A PyTorch character LSTM learns to predict the next character from sampled 128-character windows. It uses embeddings, a two-layer LSTM, AdamW, cross-entropy, and gradient clipping.
5. The sampler restricts output to the learned pitch/hold tokens and spaces, and generates a selected duration. The decoder reads token groups at grid positions, creates note-on/note-off events, and writes a Type-0 MIDI.

The current 10-second example uses seed 73 and temperature 0.8. It contains 51 note starts; the median note lasts two grid slots (240 ticks, about 250 ms at 120 BPM). The [analysis report](../outputs/symbolic/evaluation.json) records this and other source/generated MIDI statistics. These describe the file, not its musical quality.

## What the reference teaches, and what changed

The [reference repository](https://github.com/s-zeng/rag-shenanigann) uses `midicsv` to make tick/pitch text, trains Torch7 `torch-rnn`, and converts the generated text back to MIDI through `csvmidi`. This project retains that outline and keeps the onset-only corpus/checkpoint as a historical baseline. It adds a PyTorch LSTM that can be run in the current environment and an optional legacy Docker recipe.

The reference-style onset format stores only where notes begin. The decoder cannot recover note lengths it never saw, so its earlier output lasted only 1–2 MIDI ticks. The current model uses Mido to pair starts with ends, then writes attack and hold tokens on a sixteenth-note grid. The decode therefore reflects learned source durations, rounded to the chosen grid.

The project does not copy the reference code, MIDI, corpus, or checkpoints. Its source scores and manifests are new.

## What the MIDI model omits

- Exact onset and release times are rounded to the 16th-note grid; swing triplets cannot always land exactly on this grid.
- Original velocity, pedal use, instrument, channel, separate parts/hands, later tempo changes, and expressive controls are not learned.
- Type-0 conversion merges tracks, and the text format does not identify left and right hands.
- The LSTM models token patterns; it does not receive a text prompt or explicit harmony, form, or groove labels.
- Nine scores are too few for broad style claims or a meaningful benchmark. There is no held-out set or listener study.

See [results and next steps](results-and-next-steps.md) for measured findings and limits.
