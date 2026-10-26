# Evaluation plan

## Current status

No model-output audio has been committed and no listening scores are claimed yet. The project code creates JSON metadata so future comparisons can be tied to the exact prompt and generation settings.

## Small listening study

Generate three takes for each of the three presets using the same duration and seed list. Listen in randomized order and score each take from 1 (weak) to 5 (strong) on:

| Criterion | Listening question |
| --- | --- |
| Style fit | Does this sound recognizably Boogie-Woogie or closely related piano blues? |
| Groove | Is there a convincing repeated bass/shuffle pulse and forward motion? |
| Prompt adherence | Does the take reflect the described solo piano, mood, and arrangement? |
| Audio quality | Are there distracting artifacts, abrupt cuts, or unstable timbres? |
| Coherence | Does the musical idea hold together through the short take? |

Keep the generated WAV and JSON sidecar together. Record the date, listener, headphone/speaker setup, prompt, seed, model ID, and scores. Report the number of takes and show individual or median scores; do not treat a small subjective sample as a benchmark.

## Useful comparisons

- **Prompt ablation:** compare a minimal “Boogie-Woogie piano” prompt with the full left-hand/right-hand groove description.
- **Sampling:** compare a small set of temperatures while holding prompt and seed fixed, noting that same-seed comparisons across settings are not a controlled musical A/B in every backend.
- **Style presets:** compare classic honky-tonk, Chicago-club, and jump-blues directions.

Do not state that the model follows an exact BPM, 12-bar form, chord progression, or hand pattern unless that property is independently verified from the audio. The text prompt alone does not enforce those constraints.
