"""
Minimal, clean Gradio interface for HiggsAudio V2 model serving.
Focused on the main public HiggsAudio workflows from the GitHub repo and
Hugging Face model card: text-to-speech, zero-shot voice cloning,
multi-speaker dialogue, and lower-VRAM local loading.
"""

import gradio as gr
import os
import argparse
import torch
import tempfile
import uuid
import logging
import json
import time
import gc
import base64
import soundfile as sf

from typing import Optional, Any, List

# HiggsAudio API imports
from boson_multimodal.serve.serve_engine import HiggsAudioServeEngine
from boson_multimodal.data_types import ChatMLSample, AudioContent, Message

# --- Logging and Constants ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL_PATH = os.path.join(ROOT, "models/higgs-audio-v2-generation-3B-base")
DEFAULT_AUDIO_TOKENIZER_PATH = os.path.join(ROOT, "models/higgs-audio-v2-tokenizer")
DEFAULT_SYSTEM_PROMPT = (
    "Generate audio following instruction. Only speak the provided content.\n"
    "Stay faithful to the text and keep the delivery clear and natural.\n"
    "<|scene_desc_start|>\n"
    "Audio is recorded from a quiet room.\n"
    "<|scene_desc_end|>"
)
DEFAULT_STOP_STRINGS = ["<|end_of_text|>", "<|eot_id|>"]
SAMPLE_RATE = 24000

# --- Preconfigured prompts and parameter sets ---
EXAMPLES = {
    "Simple": {
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "input_text": "The sun rises in the east and sets in the west. This simple fact has been observed by humans for thousands of years.",
        "desc": "Single-speaker smart voice generation without a reference clip."
    },
    "Clone": {
        "system_prompt": "",
        "input_text": "The sun rises in the east and sets in the west. This simple fact has been observed by humans for thousands of years.",
        "desc": "Zero-shot voice cloning with reference audio plus transcript."
    },
    "Dialogue": {
        "system_prompt": (
            "You are an AI assistant designed to convert text into speech.\n"
            "If the user's message includes a [SPEAKER*] tag, do not read out the tag and generate speech for the following text, using the specified voice.\n"
            "If no speaker tag is present, select a suitable voice on your own.\n"
            "<|scene_desc_start|>\n"
            "SPEAKER0: feminine\n"
            "SPEAKER1: masculine\n"
            "<|scene_desc_end|>"
        ),
        "input_text": (
            "[SPEAKER0] I can't believe you did that without even asking me first!\n"
            "[SPEAKER1] Oh, come on! It wasn't a big deal, and I knew you would overreact like this.\n"
            "[SPEAKER0] Overreact? You made a decision that affects both of us without even considering my opinion!\n"
            "[SPEAKER1] Because I didn't have time to sit around waiting for you to make up your mind! Someone had to act."
        ),
        "desc": "Multi-speaker dialogue generation using speaker tags and scene instructions."
    },
}
PARAM_PRESETS = {
    "default": {
        "temperature": 0.2,
        "top_p": 0.9,
        "top_k": 30,
        "max_tokens": 896,
        "desc": "Balanced default tuned for clearer, lower-hallucination speech."
    },
    "faithful": {
        "temperature": 0.0,
        "top_p": 0.85,
        "top_k": 10,
        "max_tokens": 768,
        "desc": "Most conservative preset for transcript-faithful output."
    },
}

VOICE_PRESETS = {"EMPTY": "No reference"}
ENGINE = None

# --- Utility Functions ---

def get_device():
    return "cuda" if torch.cuda.is_available() else "cpu"

def get_gpu_info():
    if not torch.cuda.is_available():
        return "CUDA not available."
    d = torch.cuda.current_device()
    total = torch.cuda.get_device_properties(d).total_memory / 2**30
    used = torch.cuda.memory_allocated(d) / 2**30
    free = total - used
    pct = 100 * used / total
    return f"GPU (CUDA): {used:.1f}GB used / {total:.1f}GB total ({pct:.1f}% used, {free:.1f}GB free)"

def base64_audio(filepath):
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def normalize_text(txt: str) -> str:
    # Could add other normalization here
    return txt.strip() if txt else ""

def stop_strings_from_table(stops: Any) -> List[str]:
    # Handles both pandas.DataFrame and list-like inputs without ambiguous truthiness.
    import pandas as pd

    if stops is None:
        return DEFAULT_STOP_STRINGS

    try:
        # Gradio Dataframe can provide a pandas.DataFrame.
        if isinstance(stops, pd.DataFrame):
            if stops.empty:
                return DEFAULT_STOP_STRINGS
            rows = stops.values.tolist()
        else:
            rows = stops

        flat: List[str] = []
        for row in rows:
            value = row[0] if isinstance(row, (list, tuple)) and len(row) > 0 else row

            if value is None:
                continue
            if isinstance(value, str):
                text = value.strip()
                if text:
                    flat.append(text)
            elif pd.notna(value):
                text = str(value).strip()
                if text:
                    flat.append(text)

        return flat if flat else DEFAULT_STOP_STRINGS
    except Exception as e:
        logger.warning(f"stop_strings_from_table: fallback due to: {e}")
        return DEFAULT_STOP_STRINGS

# --- Model Initialization & TTS ---

def load_engine(model_path, audio_tokenizer_path, device, fp16):
    global ENGINE
    try:
        if not model_path: model_path = DEFAULT_MODEL_PATH
        if not audio_tokenizer_path: audio_tokenizer_path = DEFAULT_AUDIO_TOKENIZER_PATH

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()
        dtype = torch.float16 if fp16 else "auto"
        ENGINE = HiggsAudioServeEngine(
            model_name_or_path=model_path,
            audio_tokenizer_name_or_path=audio_tokenizer_path,
            device=device or get_device(),
            torch_dtype=dtype,
            kv_cache_lengths=[768, 1024] if fp16 else [1024, 2048]
        )
        return f"Model loaded on {device or get_device()} (fp16={fp16})\n{get_gpu_info()}"
    except Exception as e:
        ENGINE = None
        return f"Loading error: {e}"

def tts(
    input_text,
    system_prompt,
    voice_preset,
    reference_audio,
    reference_text,
    temperature,
    top_p,
    top_k,
    max_tokens,
    stops,
):
    global ENGINE
    if ENGINE is None:
        return "Model not loaded!", None
    try:
        # ChatML-style input
        messages = []
        if system_prompt and system_prompt.strip():
            messages.append(Message(role="system", content=system_prompt.strip()))
        # Ref audio (preset or custom)
        ref_audio64, ref_text = None, ""
        if reference_audio:
            ref_audio64 = base64_audio(reference_audio)
            ref_text = reference_text or ""
        elif voice_preset and voice_preset != "EMPTY":
            # Try to load a sample .wav from voice_examples/voice_preset.wav
            preset_path = os.path.join(ROOT, "voice_examples", f"{voice_preset}.wav")
            if os.path.exists(preset_path):
                ref_audio64 = base64_audio(preset_path)
                ref_text = VOICE_PRESETS.get(voice_preset, "")
        if ref_audio64:
            messages.append(Message(role="user", content=ref_text))
            messages.append(Message(role="assistant", content=[AudioContent(raw_audio=ref_audio64, audio_url="")]))
        # Main content
        messages.append(Message(role="user", content=normalize_text(input_text)))
        chatml = ChatMLSample(messages=messages)

        params = {
            "chat_ml_sample": chatml,
            "max_new_tokens": int(max_tokens),
            "temperature": float(temperature),
            "top_p": float(top_p),
            "top_k": int(top_k) if int(top_k) > 0 else None,
            "stop_strings": stop_strings_from_table(stops)
        }
        t0 = time.time()
        out = ENGINE.generate(**params)
        t1 = time.time()

        if hasattr(out, "audio") and out.audio is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tf:
                sf.write(tf.name, out.audio, out.sampling_rate)
            msg = f"Success. Took {t1-t0:.2f}s"
            return msg, tf.name
        else:
            return "No audio generated.", None
    except Exception as e:
        return f"Error: {e}", None

# --- Gradio Interface ---

def gradio_ui():
    # Preset loading
    def set_example(name):
        d = EXAMPLES[name]
        return d["system_prompt"], d["input_text"]

    def set_params(name):
        d = PARAM_PRESETS[name]
        return d["temperature"], d["top_p"], d["top_k"], d["max_tokens"]

    with gr.Blocks(title="HiggsAudio V2 Interface") as demo:
        gr.Markdown("## HiggsAudio V2 Text-to-Speech")
        gr.Markdown(
            "Local UI for the `bosonai/higgs-audio-v2-generation-3B-base` model and `bosonai/higgs-audio-v2-tokenizer`."
        )
        gr.Markdown(
            "HiggsAudio V2 is a text-audio foundation model trained on `10M+` hours of audio data. Public docs describe a unified audio tokenizer, a `DualFFN` audio adapter, `24kHz` generation, zero-shot voice cloning, and multi-speaker dialogue support."
        )
        with gr.Accordion("About HiggsAudio V2", open=False):
            gr.Markdown(
                """
                - GitHub repo: `boson-ai/higgs-audio`
                - Hugging Face model: `bosonai/higgs-audio-v2-generation-3B-base`
                - Hugging Face tokenizer: `bosonai/higgs-audio-v2-tokenizer`
                - Pipeline tag on Hugging Face: `text-to-speech`
                - Supported public workflows: smart voice TTS, zero-shot voice cloning, multi-speaker dialogue, narration, and some speech-plus-audio effects
                - Recommended usage pattern: build a chat-style prompt with `system` and `user` messages, then optionally add reference audio for cloning
                """
            )
        model_status = gr.Markdown("Status: Not loaded")
        # Model config
        with gr.Accordion("Model Config", open=False):
            mpath = gr.Textbox(label="Model path", value=DEFAULT_MODEL_PATH)
            apath = gr.Textbox(label="Audio tokenizer path", value=DEFAULT_AUDIO_TOKENIZER_PATH)
            devsel = gr.Radio(["cuda", "cpu"], value=get_device(), label="Device")
            fp16box = gr.Checkbox(label="FP16/low VRAM", value=False)
            init_btn = gr.Button("Initialize Model")
            gpuinfo_btn = gr.Button("Show GPU Info")
            model_msg = gr.Textbox(interactive=False)

        # Prompt and params
        example_drop = gr.Dropdown(list(EXAMPLES.keys()), value="Simple", label="Prompt Example")
        preset_drop = gr.Dropdown(list(PARAM_PRESETS.keys()), value="default", label="Parameter Preset")
        example_info = gr.Markdown(EXAMPLES["Simple"]["desc"])
        preset_info = gr.Markdown(PARAM_PRESETS["default"]["desc"])
        sys_prompt = gr.TextArea(label="System Prompt", value=EXAMPLES["Simple"]["system_prompt"], lines=2)
        txt_input = gr.TextArea(label="Input Text", value=EXAMPLES["Simple"]["input_text"], lines=3)
        voice_preset_drop = gr.Dropdown(list(VOICE_PRESETS.keys()), value="EMPTY", label="Voice Preset")
        ref_audio = gr.Audio(label="Reference Audio", type="filepath")
        ref_text = gr.TextArea(label="Reference Transcript", lines=2)
        temperature = gr.Slider(0., 1.5, value=PARAM_PRESETS["default"]["temperature"], label="Temperature")
        top_p = gr.Slider(0.1, 1.0, value=PARAM_PRESETS["default"]["top_p"], label="Top P")
        top_k = gr.Slider(-1, 100, value=PARAM_PRESETS["default"]["top_k"], step=1, label="Top K")
        max_tokens = gr.Slider(64, 4096, value=PARAM_PRESETS["default"]["max_tokens"], step=8, label="Max Tokens")
        stops = gr.Dataframe(headers=["stop"], value=[[s] for s in DEFAULT_STOP_STRINGS], col_count=(1, "fixed"))

        out_msg = gr.Textbox(label="Status", interactive=False)
        out_audio = gr.Audio(label="Output Audio", interactive=False)
        gen_btn = gr.Button("Generate Speech")

        # Bindings
        example_drop.change(
            lambda name: (EXAMPLES[name]["system_prompt"], EXAMPLES[name]["input_text"], EXAMPLES[name]["desc"]),
            inputs=example_drop,
            outputs=[sys_prompt, txt_input, example_info]
        )
        preset_drop.change(
            lambda name: (
                PARAM_PRESETS[name]["temperature"],
                PARAM_PRESETS[name]["top_p"],
                PARAM_PRESETS[name]["top_k"],
                PARAM_PRESETS[name]["max_tokens"],
                PARAM_PRESETS[name]["desc"],
            ),
            inputs=preset_drop,
            outputs=[temperature, top_p, top_k, max_tokens, preset_info]
        )
        init_btn.click(
            fn=lambda m, a, d, f: load_engine(m, a, d, f),
            inputs=[mpath, apath, devsel, fp16box],
            outputs=model_msg
        )
        gpuinfo_btn.click(fn=get_gpu_info, outputs=model_msg)
        gen_btn.click(
            fn=tts,
            inputs=[txt_input, sys_prompt, voice_preset_drop, ref_audio, ref_text,
                    temperature, top_p, top_k, max_tokens, stops],
            outputs=[out_msg, out_audio]
        )

    return demo

# --- Main Entrypoint ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Minimal HiggsAudio Gradio UI")
    parser.add_argument("--host", default=os.environ.get("GRADIO_SERVER_NAME", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("GRADIO_SERVER_PORT", "7860")))
    parser.add_argument("--share", action="store_true")
    args = parser.parse_args()

    # Load voice presets if available
    presets_config = os.path.join(ROOT, "voice_examples", "config.json")
    if os.path.exists(presets_config):
        try:
            with open(presets_config, "r", encoding="utf-8") as f:
                cfgd = json.load(f)
            VOICE_PRESETS = {k: v["transcript"] for k, v in cfgd.items()}
            VOICE_PRESETS["EMPTY"] = "No reference"
        except Exception as e:
            logger.error(f"Failed to load voice presets: {e}")

    print(f"Launching HiggsAudio UI on {args.host}:{args.port} (share={args.share})")
    ui = gradio_ui()
    ui.launch(server_name=args.host, server_port=args.port, share=args.share)
