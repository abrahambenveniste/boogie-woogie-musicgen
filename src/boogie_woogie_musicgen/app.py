"""Gradio prompt studio."""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

import gradio as gr

from .generator import DEFAULT_MODEL, MAX_SECONDS, generate_audio
from .prompting import PRESETS, build_prompt


def generate_from_ui(
    preset: str,
    extra_direction: str,
    seconds: int,
    seed: int,
    temperature: float,
    guidance_scale: float,
):
    prompt = build_prompt(preset, extra_direction)
    output_dir = Path(tempfile.gettempdir()) / "boogie-woogie-musicgen"
    output_path = output_dir / f"take-{uuid.uuid4().hex}.wav"
    wav_path, _ = generate_audio(
        prompt=prompt,
        output_path=output_path,
        seconds=seconds,
        seed=seed,
        model_id=DEFAULT_MODEL,
        temperature=temperature,
        guidance_scale=guidance_scale,
    )
    return str(wav_path), prompt


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Boogie-Woogie MusicGen") as demo:
        gr.Markdown(
            "# Boogie-Woogie MusicGen\n"
            "Describe the feel, generate a short instrumental take, and compare prompts. "
            "The first take downloads the pretrained model."
        )
        with gr.Row():
            with gr.Column():
                preset = gr.Dropdown(
                    choices=sorted(PRESETS),
                    value="classic-honky-tonk",
                    label="Starting style",
                )
                extra = gr.Textbox(
                    label="Extra direction",
                    placeholder="For example: slower, relaxed swing with a warm upright-piano tone",
                )
                seconds = gr.Slider(4, MAX_SECONDS, value=11, step=1, label="Duration (seconds)")
                seed = gr.Number(value=42, precision=0, label="Seed")
                temperature = gr.Slider(0.5, 1.5, value=1.0, step=0.05, label="Temperature")
                guidance = gr.Slider(1.0, 5.0, value=3.0, step=0.1, label="Guidance scale")
                button = gr.Button("Generate take", variant="primary")
            with gr.Column():
                audio = gr.Audio(label="Generated WAV", type="filepath")
                prompt = gr.Textbox(label="Prompt sent to MusicGen", lines=5, interactive=False)
        button.click(
            fn=generate_from_ui,
            inputs=[preset, extra, seconds, seed, temperature, guidance],
            outputs=[audio, prompt],
        )
        gr.Markdown(
            "Model: `facebook/musicgen-small` · weights: CC-BY-NC 4.0 · "
            "Prompt guidance does not guarantee exact tempo or song form."
        )
    return demo


def main() -> None:
    build_app().launch()
