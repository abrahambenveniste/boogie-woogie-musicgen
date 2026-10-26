# Methodology

In one line: I use MusicGen for prompt-led audio sketches and a small LSTM to explore note patterns learned from MIDI.

This repository contains two distinct generation experiments. The first uses a pretrained text-to-audio model. The second trains a small symbolic music model from MIDI in this repository using the method described in `s-zeng/rag-shenanigann`.

## Track A: prompt-conditioned MusicGen audio

The MusicGen path asks Meta's `facebook/musicgen-small` checkpoint to generate short audio from a written music brief. A text encoder represents the prompt, an autoregressive Transformer samples discrete audio-code tokens, and an EnCodec decoder reconstructs a waveform. The project uses Hugging Face Transformers and records the prompt, checkpoint, duration, seed, sampling controls, device, library versions, sample rate, and output duration in JSON next to each WAV.

Boogie-Woogie prompts state the intended piano ensemble, left-hand bass role, right-hand riffs, shuffle/swing feel, blues form, and absence of vocals. These are soft conditions: the model can drift from the brief and does not guarantee a BPM, meter, chord sequence, exact 12-bar form, hand independence, or note-level Boogie-Woogie accuracy.

Primary technical references: [MusicGen paper](https://arxiv.org/abs/2306.05284), [AudioCraft MusicGen documentation](https://github.com/facebookresearch/audiocraft/blob/main/docs/MUSICGEN.md), [Hugging Face model documentation](https://huggingface.co/docs/transformers/en/model_doc/musicgen), and the [MusicGen model card](https://github.com/facebookresearch/audiocraft/blob/main/model_cards/MUSICGEN_MODEL_CARD.md).

## Track B: MIDI character LSTM

This path adapts the reference's symbolic sequence method to Boogie-Woogie. It is custom training performed by this repository, not a pretrained music model and not text-prompted generation.

1. Select MIDI scores from PDMX v8, retain their source fields and hashes in a manifest, and convert each multi-track MIDI to Type 0.
2. Use `midicsv` to read the MIDI header and events. Preserve PPQN, the first tempo, and positive-velocity note-on pitches only.
3. Encode each pitch as `chr(33 + pitch)`. Concatenate characters for pitches on the same absolute tick. Put one space between consecutive tick slots, including blank slots. Separate pieces with three newlines.
4. Train a character-level LSTM to predict the next character from fixed-length windows sampled from the concatenated corpus. The modern path uses PyTorch, embeddings, cross-entropy, AdamW, and gradient clipping. The documented legacy path uses upstream Torch7 `torch-rnn` in the `crisbal/torch-rnn:base` Docker image.
5. Sample a new note stream. The modern sampler uses the first record's PPQN/tempo prefix and restricts tokens to the observed pitch alphabet plus space, so generated text remains decodable.
6. Reconstruct a MIDI CSV file and MIDI file. `csvmidi` is preferred when installed; Mido is included as a fallback writer.

The full command sequence, tool versions and roles, training parameters, MIDI format checks, and implementation differences are documented in [`SYMBOLIC_RNN_WORKFLOW.md`](SYMBOLIC_RNN_WORKFLOW.md).

### What the symbolic model can learn

The LSTM estimates the next-character distribution over one compact serialized score representation. It can learn frequent pitch/tick patterns in the six training items. It does not receive a natural-language prompt, explicit chord labels, part labels, bar markers, note durations, or a formal theory representation. The corpus is deliberately small and is useful for demonstrating an end-to-end data/model pipeline, not for a strong claim about genre-wide composition.

### Information loss and decoder assumptions

The text representation drops note-off timing, durations, original velocities, instrument programs, channels, separate hands, later tempo changes, sustain pedal, key/time signatures, and other performance controls. It uses a single note character per note-on, so same-tick chords are represented by adjacent characters. MIDI reconstruction assigns velocity 96 and keeps a pitch active until a later tick group changes or clears it. These are explicit simplifications of the reference method.

The reference decoder uses character-string offsets for event times, so chord width can affect reconstructed timing. This implementation uses tick-slot indices instead and closes final notes before end-of-track. That improves temporal consistency and MIDI validity but does not restore information discarded before training.

## Evaluation

The MusicGen sample is a pipeline demonstration. The symbolic LSTM sample is a generated MIDI continuation with a recorded seed, temperature, checkpoint hash, corpus hash, PPQN, tempo, and requested tick count. Neither is a benchmark. See [`EVALUATION.md`](EVALUATION.md) for a listening and inspection protocol that separates prompt/style fit, rhythmic behavior, form, output validity, and limitations.

