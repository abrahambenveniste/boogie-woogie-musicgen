# Reference repository review: `s-zeng/rag-shenanigann`

In one line: this review traces the reference pipeline and shows which ideas this project follows, adapts, and leaves out.

Reviewed repository: [github.com/s-zeng/rag-shenanigann](https://github.com/s-zeng/rag-shenanigann), default branch `master`. The repository describes experiments in automated ragtime composition. “Rag” here means ragtime; this is not retrieval-augmented generation (RAG).

## Contents and stated stack

- `rag/`: 512 raw MIDI files included with the project.
- `scripts/grab.py`: an optional scraper for two MIDI Library listing pages.
- `scripts/process.py`: uses the external `midicsv` command to encode MIDI into text.
- `samples/training_data`: the preprocessed training corpus, about 38 MB.
- `samples/sample-A` through `sample-E`: raw model continuations and reconstructed CSV/MIDI examples; one WAV rendition is included.
- `scripts/unprocess.py`: converts generated text into MIDI CSV; the README then instructs using `csvmidi` to create MIDI.
- Requirements named in the README: `midicsv`, `torch-rnn` (the linked Docker project), Python 3, and optional `gnmidifmt` for converting MIDI formats.
- License displayed by GitHub: AGPL-3.0. Data licensing is not separately documented file by file.

The README reports nine commits. The repository does not pin a `torch-rnn` revision, training command, model configuration, seed, or training log, so the exact published samples are not fully reproducible from the repository alone.

## End-to-end approach

1. Download or provide MIDI files. `grab.py` scrapes filenames from two hard-coded HTTP pages and downloads matching `.mid` files.
2. Convert files to MIDI type 0 so notes from both hands are on one track. The README suggests `gnmidifmt` or an equivalent converter.
3. Run `midicsv` on each file. `process.py` writes the MIDI header’s ticks-per-quarter-note value, the first tempo event, then a character stream of positive-velocity `Note_on_c` pitches grouped by tick with spaces between ticks. It separates source files with three newlines.
4. Train the external character-level recurrent neural network (torch-rnn) on the generated text.
5. Run the generated text through `unprocess.py`, then `csvmidi`, to produce MIDI files for listening.

The model learns correlations in a serialized note-event sequence; it is not conditioned on an explicit text description or a symbolic Boogie-Woogie control interface. The README’s qualitative reflection reports recognizable harmony/chords when a sample stays coherent, alongside inconsistent tempo and style.

## Encoding details and limitations

### `grab.py`

The script fetches two listing pages using `requests.get` over plain HTTP, extracts names with a regular expression matching `ragsmid/<name>.mid`, and downloads each file to the current directory. It has no explicit timeout, status validation, retry, pacing, destination directory, or provenance/license record. It is a convenience scraper rather than a robust or auditable ingestion pipeline.

### `process.py`

- Uses `os.listdir('rag')`, so the input folder is hard-coded and file order is not recorded.
- Invokes the external `midicsv` executable and splits output rows on comma-space.
- Copies header field 5 and the first tempo value into the text sample.
- Allocates a list indexed by MIDI tick (based on the penultimate track-end assumption in `data[-3]`).
- For each positive-velocity `Note_on_c`, appends `chr(33 + pitch)` to that tick’s slot.
- Joins all tick slots with spaces and writes a record separated from the next by three newline characters.
- Does not encode note-off events, note lengths, original velocities, instruments/program changes, channels, expressive controls, key/time signature, or multiple simultaneous tracks as separate parts. Only the first tempo event is retained.

The pitch-to-character mapping is compact but opaque. Chords become multiple adjacent characters, so simultaneity is inferred from adjacency rather than represented as a typed chord token. The script assumes parse rows and end-of-track structure are present and does not validate MIDI files or parse errors.

### `unprocess.py`

It splits model text on triple newlines, treats the first two lines as PPQN and tempo, then scans the third line. At each space it emits note-offs for the preceding group and note-ons for the current group, always using velocity 96. It calculates event ticks from character index, so a chord with more pitch characters occupies more serialized positions than a single-note tick; this can change relative rhythmic spacing. The final held group is not explicitly switched off before end-of-track, and the output directory `test/` must already exist.

### Main trade-offs

The representation is simple and gives a small RNN a single sequence to learn. It loses important performance information, conflates pitch tokens with timing separators, and has no explicit normalization for tempo or PPQN. MIDI type 0 avoids separate hand tracks but also removes explicit part structure. The README itself flags inconsistent tempo and style and suggests tempo/PPQN normalization as future work.

## What this project adopts and changes

The first version of this project used only prompt-conditioned MusicGen audio inference. The symbolic extension follows the reference's MIDI → text → recurrent model → MIDI outline: it normalizes Boogie-Woogie MIDI to Type 0, serializes note events with tick separators, trains a character-level recurrent model, and decodes a generated stream back to MIDI. The saved onset-only baseline uses `midicsv`; the current duration-aware route uses Mido to pair note-on/note-off events and write attack/hold tokens on a quantized grid. It uses a modern PyTorch LSTM for the runnable training path and documents the legacy Torch7 Docker option named by the reference.

The project keeps MusicGen as a separate modern audio-generation path. The two models have different conditioning and outputs: MusicGen accepts text prompts and emits WAV; the symbolic LSTM learns a small MIDI corpus and emits a note stream/MIDI, with no natural-language prompt interface. The Boogie-Woogie corpus and source manifest are new. No reference code, MIDI files, or preprocessed training corpus are copied into this project.

The new implementation corrects the reference decoder's timing and note closure: it uses grid-slot positions rather than character offsets as MIDI time and emits note-offs for the final group before end-of-track. The old onset-only model still cannot recover durations because they were omitted from its training text; the current model learns durations rounded to its sixteenth-note grid.
