# Results and next steps

In one line: the duration problem is fixed in the new MIDI representation, and the first 10-second sample is much easier to play; musical quality still needs a listener.

## What changed

The source set grew from six to nine scores with *Chompin' at the Bit*, *The Squidgies Boogie*, and *Easy Boogie / Blues etude*. The expanded set has 7,743 locally parsed note-ons. PDMX reports CC0 and no license conflict on all nine manifest rows; this is source metadata, not independent legal review.

The old model saw note starts but no note-offs. Its 5-second MIDI samples had 23–38 note-ons and notes typically only 1–2 ticks long. At 480 PPQN and 120 BPM, one tick is about 1.04 milliseconds. That format could not learn duration.

The new processor pairs note-ons with note-offs, rounds them to a 120-tick (16th-note) grid, and uses separate attack and hold tokens. It was trained on all nine scores for 1,000 CPU steps. Its training cross-entropy fell from 4.9853 to 1.0953; there is no validation split, so this is only a training statistic.

## First duration-aware sample

The saved MIDI sample is 10 seconds at 120 BPM. It has 51 note-on events (5.1 per second), note lengths from 120 to 720 ticks, and a median of 240 ticks. With 480 PPQN and 500,000 microseconds per quarter note, those lengths are 125–750 milliseconds, with a 250-millisecond median. The older sample's median was 1 tick.

The new take is sparser than the median source score (5.1 vs. 8.68 note starts per second) and uses a narrower pitch range (31–69 vs. 24–94 across the sources). That could leave it sounding thin or repetitive, but the measurements alone cannot tell us whether it is enjoyable.

The generated sample's exact 8-note pitch sequence did not match any source window in the current diagnostic (0 matches among 44 windows). This is a narrow check; it cannot establish originality or musical quality. See [`evaluation.json`](../outputs/symbolic/evaluation.json) for file hashes, pitch range, note density, durations, and the legacy comparison.

The MusicGen WAV is 10.94 seconds (requested duration: 11 seconds). It is a separate prompt-to-audio experiment and does not learn from these nine MIDI scores. The [audio file](https://raw.githubusercontent.com/abrahambenveniste/boogie-woogie-musicgen/main/outputs/boogie-woogie-demo.wav) and its [generation recipe](../outputs/boogie-woogie-demo.json) are saved in the repo.

## What I can and cannot claim

- The new MIDI is valid and has realistic note-length ranges for playback; that does not mean its rhythm or phrases sound convincing.
- I do not have a structured listening result. Please listen to the WAV and MIDI with a piano sound and rate style fit, groove, coherence, variety, and artifacts before describing it as good Boogie-Woogie.
- Nine scores remain a small, mixed corpus. The model may memorize fragments, repeat itself, or produce weak harmony.
- No held-out evaluation, controlled listener study, or exact 12-bar analysis has been completed.
- The two models should not be ranked against each other: one is a pretrained text-to-audio model, the other is a small MIDI-trained LSTM.

## Simple listening sheet

Rate each item from 1 (weak) to 5 (strong). Keep the playback device and MIDI soundfont fixed when comparing MIDI files.

| Sample | Style fit | Groove | Coherence | Variety | Artifacts | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| MusicGen WAV |  |  |  |  |  |  |
| Duration-aware LSTM MIDI |  |  |  |  |  |  |
| Legacy onset-only MIDI |  |  |  |  |  |  |

## Next steps

1. Listen to the 10-second MIDI with a piano sound and record the scores above.
2. If the groove is still messy, compare a few generation temperatures and seeds while holding the checkpoint, 10-second duration, and decoder fixed.
3. Only if listener feedback says the examples lack variety, add more license-checked scores and record the source fields before retraining.
4. After corpus growth, add a held-out split and compare generated note density, duration, pitch range, and listener ratings against the source set.

The main lesson so far: more scores expand coverage, but fixing what the model sees in each training example was necessary to fix the 1-millisecond notes.
