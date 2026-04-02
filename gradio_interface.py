"""
Completely rewritten: Minimal, clean Gradio interface for HiggsAudio model serving.
Focus: Modular, extensible, robust, and straightforward UI for text-to-speech with cloning.
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
        "input_text": "The road not taken by Robert Frost.",
        "desc": "Simple single-speaker TTS."
    },
    "Clone": {
        "system_prompt": "",
        "input_text": "Say something in the style of the sample clip.",
        "desc": "Voice cloning via reference audio."
    },
}
PARAM_PRESETS = {
    "default": {
        "temperature": 0.2,
        "top_p": 0.9,
        "top_k": 30,
        "max_tokens": 896,
        "desc": "Balanced default."
    },
    "faithful": {
        "temperature": 0.0,
        "top_p": 0.85,
        "top_k": 10,
        "max_tokens": 768,
        "desc": "Faithful, less hallucination."
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
    # Handles both pandas.DataFrame and list input, avoiding ambiguous truth value error.
    import pandas as pd

    # Handle case where stops is a pandas.DataFrame from Gradio Dataframe component
    if hasattr(stops, "values") and hasattr(stops, "columns"):
        try:
            stops_list = stops.values.tolist()
        except Exception:
            stops_list = []
    else:
        stops_list = stops

    # If stops_list is a DataFrame and is empty, just return default
    if stops_list is None:
        return DEFAULT_STOP_STRINGS

    try:
        flat = []
        for row in stops_list:
            # Row can be a list/tuple or just a string
            if isinstance(row, (list, tuple)):
                v = row[0] if row else ""
            else:
                v = row
            if v and isinstance(v, str) and v.strip():
                flat.append(v.strip())
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

    with gr.Blocks(title="HiggsAudio Minimal Interface") as demo:
        gr.Markdown("## HiggsAudio Text-to-Speech")
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
        example_drop.change(set_example, inputs=example_drop, outputs=[sys_prompt, txt_input])
        preset_drop.change(set_params, inputs=preset_drop, outputs=[temperature, top_p, top_k, max_tokens])
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
