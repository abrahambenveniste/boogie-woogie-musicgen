"""Load MusicGen and generate one prompt-conditioned WAV take."""

from __future__ import annotations

import json
import platform
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import transformers
from transformers import AutoProcessor, MusicgenForConditionalGeneration

DEFAULT_MODEL = "facebook/musicgen-small"
TOKENS_PER_SECOND = 50
MAX_SECONDS = 30


def resolve_device(requested: str = "auto") -> str:
    """Select an available accelerator, or use the explicitly requested device."""
    if requested != "auto":
        return requested
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


@lru_cache(maxsize=2)
def load_model(model_id: str, device: str):
    """Load and cache the processor/model pair for repeated UI generations."""
    processor = AutoProcessor.from_pretrained(model_id)
    model = MusicgenForConditionalGeneration.from_pretrained(model_id)
    model.to(device)
    model.eval()
    return processor, model


def generate_audio(
    *,
    prompt: str,
    output_path: str | Path,
    seconds: int = 8,
    seed: int = 42,
    model_id: str = DEFAULT_MODEL,
    device: str = "auto",
    temperature: float = 1.0,
    top_k: int = 250,
    guidance_scale: float = 3.0,
) -> tuple[Path, Path]:
    """Generate a WAV file and a JSON sidecar containing the generation recipe."""
    seconds = int(seconds)
    seed = int(seed)
    top_k = int(top_k)
    temperature = float(temperature)
    guidance_scale = float(guidance_scale)
    if not prompt.strip():
        raise ValueError("Prompt cannot be empty.")
    if not 1 <= seconds <= MAX_SECONDS:
        raise ValueError(f"Duration must be between 1 and {MAX_SECONDS} seconds.")
    if temperature <= 0:
        raise ValueError("Temperature must be greater than zero.")
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    selected_device = resolve_device(device)

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    processor, model = load_model(model_id, selected_device)
    inputs = processor(text=[prompt.strip()], padding=True, return_tensors="pt")
    inputs = {key: value.to(selected_device) for key, value in inputs.items()}

    with torch.inference_mode():
        generated = model.generate(
            **inputs,
            do_sample=True,
            max_new_tokens=seconds * TOKENS_PER_SECOND,
            temperature=temperature,
            top_k=top_k,
            guidance_scale=guidance_scale,
        )

    # MusicGen returns (batch, channels, samples). SoundFile expects
    # (samples, channels) for multichannel audio.
    waveform = generated[0].detach().cpu().numpy().T
    waveform = np.asarray(np.clip(waveform, -1.0, 1.0), dtype=np.float32)
    sample_rate = int(model.config.audio_encoder.sampling_rate)
    sf.write(output_path, waveform, sample_rate, subtype="PCM_16")

    metadata_path = output_path.with_suffix(".json")
    metadata = {
        "prompt": prompt.strip(),
        "model_id": model_id,
        "model_weights_license": "CC-BY-NC 4.0",
        "duration_requested_seconds": seconds,
        "duration_actual_seconds": round(len(waveform) / sample_rate, 3),
        "sample_rate_hz": sample_rate,
        "channels": 1 if waveform.ndim == 1 else int(waveform.shape[1]),
        "seed": seed,
        "temperature": temperature,
        "top_k": top_k,
        "guidance_scale": guidance_scale,
        "device": selected_device,
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "python_version": platform.python_version(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "rights_note": (
            "The model-weights license is not a grant of rights in generated audio. "
            "Review applicable model terms and third-party rights before reuse."
        ),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return output_path, metadata_path
