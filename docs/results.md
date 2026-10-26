# Results and limits

## Current examples

| Model | How it generates music | Listening result |
| --- | --- | --- |
| MusicGen | [10.94-second WAV](../outputs/boogie-woogie-demo.wav); generated from a text prompt by a pretrained model, not trained on the nine scores. | Very bad; has a huge tempo issue. |
| MIDI LSTM | [10-second MIDI](../outputs/symbolic/boogie-rnn-duration-demo-000.mid); trained on the nine-score corpus and decoded into note events. | Okay-ish; sounds musical and stays more in tempo. |

Each output has a JSON recipe beside it. The symbolic measurements and legacy comparison are in [`evaluation.json`](../outputs/symbolic/evaluation.json); per-step training loss is in [`training-loss-duration.csv`](../outputs/symbolic/training-loss-duration.csv).

## What the measurements show

The old onset-only representation stored note attacks but not note releases. Its generated notes were typically 1–2 MIDI ticks long—about 1–2 ms at 480 PPQN and 120 BPM—so playback sounded like clicks.

The duration-aware representation pairs note-ons with note-offs, rounds them to a 120-tick sixteenth-note grid, and gives attacks and holds separate tokens. In the saved MIDI example:

- Duration is 10 seconds, with 51 note starts (5.1 per second).
- Note lengths range from 120 to 720 ticks; the median is 240 ticks (250 ms at 120 BPM).
- Training loss falls from 4.9853 to 1.0953 over 1,000 steps.

These measurements show that the new representation produces usable note lengths. The loss is from training data only; there is no held-out split. The generated note density is below the source-score median (5.1 vs. 8.68 note starts per second), and its pitch range is narrower (31–69 vs. 24–94 across the source set).

## First listening finding

This is an informal listening comparison: the MIDI LSTM output is okay-ish, sounds musical, and stays more in tempo; the MusicGen output is very bad and has a huge tempo issue. These are listening judgments, not measured BPM results, and there has not been a structured listening study.

## What remains unknown

The informal finding is encouraging for the MIDI model, but it is not enough to claim that its music is consistently enjoyable or convincing Boogie-Woogie. The nine-score corpus is small, mixed, and may lead to repetition or weak harmony. A sixteenth-note grid also cannot place every swing triplet exactly. Neither model guarantees a specific tempo, chord progression, or 12-bar form.

The exact 8-note pitch sequence check found no matches among 44 tested source windows. This narrow check is not proof of originality or of generalization.

## Next useful checks

1. Measure the beat stability of the WAV and MIDI, then compare the results with the informal tempo impression.
2. Compare multiple seeds and temperatures while holding the checkpoint and decoder fixed; record ratings for groove, coherence, style fit, variety, and artifacts.
3. If the notes sound thin or repetitive, expand the corpus with more provenance-checked scores, then add held-out evaluation before making broader claims.
