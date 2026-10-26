# Data and model provenance

## Data used by this project

This project does not assemble or train on a custom Boogie-Woogie audio or MIDI dataset. At runtime it sends a text prompt to a publicly released pretrained checkpoint, `facebook/musicgen-small`, and receives generated audio from that model. Generated WAV files and their JSON recipes are the project’s outputs; model weights and training files are not included in the repository.

The MusicGen model card says the model was trained on 20,000 hours of licensed music, using Meta’s Music Initiative Sound Collection plus Shutterstock and Pond5 music. AudioCraft’s documentation gives the same high-level provenance and states that the training datasets themselves are not released with the code. This project therefore cannot independently inspect or redistribute the underlying tracks.

Sources:

- [MusicGen model card](https://github.com/facebookresearch/audiocraft/blob/main/model_cards/MUSICGEN_MODEL_CARD.md)
- [AudioCraft MusicGen documentation](https://github.com/facebookresearch/audiocraft/blob/main/docs/MUSICGEN.md)
- [MusicGen checkpoint on Hugging Face](https://huggingface.co/facebook/musicgen-small)

## Checkpoint and license

The default checkpoint is a text-to-music model with 300M parameters. AudioCraft’s code is MIT-licensed; the MusicGen weights are **CC-BY-NC 4.0**. The project does not download or redistribute those weights in Git. Anyone using the checkpoint should read the current model card and license, especially before commercial use.

The checkpoint license does not, by itself, establish the licensing status of every generated output. This repository makes no blanket rights claim over generated audio. Review the model terms and any applicable third-party rights before publishing or reusing a take.

## Reference repository data audit

The referenced [`s-zeng/rag-shenanigann`](https://github.com/s-zeng/rag-shenanigann) repository contains 512 `.mid` files in `rag/` and a roughly 38 MB preprocessed text corpus at `samples/training_data`. Its README says the MIDI corpus is bundled and points to a MIDI Library as a download source. The repository does not provide a per-file provenance manifest or a separate data license for those MIDI files. The code repository declares AGPL-3.0, which should not be assumed to settle the rights for every bundled recording or transcription.

This project does not copy those MIDI files, sample files, or scripts. The reference data is analyzed for methodology only; it is not an input to MusicGen inference here.
