# Evaluation plan

## Current status

The repository contains one MusicGen WAV and one symbolic-RNN MIDI demonstration with its recipes and training log. They show that both pipelines run; they are not benchmark results. No structured listener scores are claimed.

## Listening protocol

For a small exploratory listening study, generate three takes per method with a documented seed list. Randomize the playback order and ask listeners to score from 1 (weak) to 5 (strong):

| Criterion | Listening question |
| --- | --- |
| Style fit | Does it sound recognizably like Boogie-Woogie or closely related piano blues? |
| Groove | Is there a convincing repeated bass/shuffle pulse and forward motion? |
| Coherence | Does the idea hold together through the take? |
| Variety | Does it avoid simply repeating one short phrase? |
| Artifacts | Are there distracting audio or MIDI-rendering problems? |

For MusicGen, also score prompt adherence. For the symbolic RNN, compare the generated MIDI with the training scores in a piano roll and record pitch range, event density, note lengths reconstructed by the decoder, and repetition. Keep the MusicGen prompt/JSON and RNN MIDI/text/JSON/checkpoint hash together. Record the listener, date, playback setup, model settings, and individual scores; report sample count and median or range rather than a broad claim.

## Symbolic diagnostics

The RNN is trained on only six scores, so simple diagnostics are useful but not sufficient measures of musical quality. A future evaluation can compare generated and source sequences on:

- pitch histogram and register;
- positive-velocity note-on density per second;
- interval and repeated-pitch distributions;
- fraction of empty tick slots;
- repeated n-grams or exact substring overlap with training data;
- generated MIDI readability in a piano roll and playback by a listener.

These measurements should be calculated on source and generated MIDI with the same parser. They do not establish plagiarism, originality, style authenticity, or listener preference by themselves.

## Controlled comparisons

- Compare a small range of LSTM temperatures while holding the checkpoint, tick budget, and seed fixed.
- Compare a minimal MusicGen prompt against the full left-hand/right-hand groove brief, with duration and seed fixed.
- Keep symbolic LSTM and MusicGen results in separate groups; their data, conditioning, output format, and learned task differ, so they are not a direct apples-to-apples model benchmark.

Do not state that an output follows exact BPM, 12-bar form, chord progression, or hand pattern unless that property is independently inspected from the generated audio or MIDI.
