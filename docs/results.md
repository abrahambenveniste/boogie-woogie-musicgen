# Results and limits

## Current examples

| Path | Saved output | What it demonstrates |
| --- | --- | --- |
| MusicGen | [10.94-second WAV](../outputs/boogie-woogie-demo.wav) | A text prompt sent to a pretrained audio model; it does not learn from the nine scores. |
| MIDI LSTM | [10-second MIDI](../outputs/symbolic/boogie-rnn-duration-demo-000.mid) | A local model trained on the nine-score corpus, decoded into note events. |

Each output has a JSON recipe beside it. The symbolic measurements and legacy comparison are in [`evaluation.json`](../outputs/symbolic/evaluation.json); per-step training loss is in [`training-loss-duration.csv`](../outputs/symbolic/training-loss-duration.csv).

## What the measurements show

The old onset-only representation stored note attacks but not note releases. Its generated notes were typically 1–2 MIDI ticks long—about 1–2 ms at 480 PPQN and 120 BPM—so playback sounded like clicks.

The duration-aware representation pairs note-ons with note-offs, rounds them to a 120-tick sixteenth-note grid, and gives attacks and holds separate tokens. In the saved MIDI example:

- Duration is 10 seconds, with 51 note starts (5.1 per second).
- Note lengths range from 120 to 720 ticks; the median is 240 ticks (250 ms at 120 BPM).
- Training loss falls from 4.9853 to 1.0953 over 1,000 steps.

These measurements show that the new representation produces usable note lengths. The loss is from training data only; there is no held-out split. The generated note density is below the source-score median (5.1 vs. 8.68 note starts per second), and its pitch range is narrower (31–69 vs. 24–94 across the source set).

## First listening finding

On an informal listen, the MIDI LSTM output sounds somewhat musical and more consistent in tempo. The MusicGen output sounds very poor and has a pronounced tempo problem. This is an initial subjective comparison; the tempo difference has not been measured in BPM, and there has not been a structured listening study.

## What remains unknown

The informal finding is encouraging for the MIDI model, but it is not enough to claim that its music is consistently enjoyable or convincing Boogie-Woogie. The nine-score corpus is small, mixed, and may lead to repetition or weak harmony. A sixteenth-note grid also cannot place every swing triplet exactly. Neither model guarantees a specific tempo, chord progression, or 12-bar form.

The exact 8-note pitch sequence check found no matches among 44 tested source windows. This narrow check is not proof of originality or of generalization.

## Next useful checks

1. Measure the beat stability of the WAV and MIDI, then compare the results with the informal tempo impression.
2. Compare multiple seeds and temperatures while holding the checkpoint and decoder fixed; record ratings for groove, coherence, style fit, variety, and artifacts.
3. If the notes sound thin or repetitive, expand the corpus with more provenance-checked scores, then add held-out evaluation before making broader claims.
