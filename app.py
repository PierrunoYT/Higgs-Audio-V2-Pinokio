"""
Gradio UI for Text-to-Speech using HiggsAudioServeEngine
"""

import argparse
import base64
import inspect
import os
import uuid
import json
from typing import Optional
import gradio as gr
from loguru import logger
import numpy as np
import time
from functools import lru_cache
import re
import torch

try:
    import spaces
except Exception:
    def _gpu_decorator(*args, **kwargs):
        if args and callable(args[0]) and len(args) == 1 and not kwargs:
            return args[0]

        def _inner(func):
            return func

        return _inner

    class _SpacesFallback:
        GPU = staticmethod(_gpu_decorator)

    spaces = _SpacesFallback()

# Import HiggsAudio components (support both package layouts)
try:
    from higgs_audio.serve.serve_engine import HiggsAudioServeEngine
    from higgs_audio.data_types import ChatMLSample, AudioContent, Message
except ImportError:
    from boson_multimodal.serve.serve_engine import HiggsAudioServeEngine
    from boson_multimodal.data_types import ChatMLSample, AudioContent, Message

# Global engine instance
engine = None

# Default model configuration
ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL_PATH = "bosonai/higgs-audio-v2-generation-3B-base"
DEFAULT_AUDIO_TOKENIZER_PATH = "bosonai/higgs-audio-v2-tokenizer"
LOCAL_MODEL_PATH = os.path.join(ROOT, "models", "higgs-audio-v2-generation-3B-base")
LOCAL_AUDIO_TOKENIZER_PATH = os.path.join(ROOT, "models", "higgs-audio-v2-tokenizer")
SAMPLE_RATE = 24000
VOICE_PRESET_SPACE_REPO = "smola/higgs_audio_v2"
VOICE_PRESET_DIR = "voice_examples"
TEMP_HIGGS_VOICE_DIR = os.path.join(ROOT, "temp_higgs", "voice_examples")

DEFAULT_SYSTEM_PROMPT = (
    "Generate audio following instruction.\n\n"
    "<|scene_desc_start|>\n"
    "Audio is recorded from a quiet room.\n"
    "<|scene_desc_end|>"
)

DEFAULT_STOP_STRINGS = ["<|end_of_text|>", "<|eot_id|>"]

# Predefined examples for system and input messages
PREDEFINED_EXAMPLES = {
    "voice-clone": {
        "system_prompt": "",
        "input_text": "Hey there! I'm your friendly voice twin in the making. Pick a voice preset below or upload your own audio - let's clone some vocals and bring your voice to life! ",
        "description": "Voice clone to clone the reference audio. Leave the system prompt empty.",
    },
    "smart-voice": {
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "input_text": "The sun rises in the east and sets in the west. This simple fact has been observed by humans for thousands of years.",
        "description": "Smart voice to generate speech based on the context",
    },
    "multispeaker-voice-description": {
        "system_prompt": "You are an AI assistant designed to convert text into speech.\n"
        "If the user's message includes a [SPEAKER*] tag, do not read out the tag and generate speech for the following text, using the specified voice.\n"
        "If no speaker tag is present, select a suitable voice on your own.\n\n"
        "<|scene_desc_start|>\n"
        "SPEAKER0: feminine\n"
        "SPEAKER1: masculine\n"
        "<|scene_desc_end|>",
        "input_text": "[SPEAKER0] I can't believe you did that without even asking me first!\n"
        "[SPEAKER1] Oh, come on! It wasn't a big deal, and I knew you would overreact like this.\n"
        "[SPEAKER0] Overreact? You made a decision that affects both of us without even considering my opinion!\n"
        "[SPEAKER1] Because I didn't have time to sit around waiting for you to make up your mind! Someone had to act.",
        "description": "Multispeaker with different voice descriptions in the system prompt",
    },
    "single-speaker-voice-description": {
        "system_prompt": "Generate audio following instruction.\n\n"
        "<|scene_desc_start|>\n"
        "SPEAKER0: He speaks with a clear British accent and a conversational, inquisitive tone. His delivery is articulate and at a moderate pace, and very clear audio.\n"
        "<|scene_desc_end|>",
        "input_text": "Hey, everyone! Welcome back to Tech Talk Tuesdays.\n"
        "It's your host, Alex, and today, we're diving into a topic that's become absolutely crucial in the tech world — deep learning.\n"
        "And let's be honest, if you've been even remotely connected to tech, AI, or machine learning lately, you know that deep learning is everywhere.\n"
        "\n"
        "So here's the big question: Do you want to understand how deep learning works?\n",
        "description": "Single speaker with voice description in the system prompt",
    },
    "single-speaker-zh": {
        "system_prompt": "Generate audio following instruction.\n\n"
        "<|scene_desc_start|>\n"
        "Audio is recorded from a quiet room.\n"
        "<|scene_desc_end|>",
        "input_text": "大家好, 欢迎收听本期的跟李沐学AI. 今天沐哥在忙着洗数据, 所以由我, 希格斯主播代替他讲这期视频.\n"
        "今天我们要聊的是一个你绝对不能忽视的话题: 多模态学习.\n"
        "那么, 问题来了, 你真的了解多模态吗? 你知道如何自己动手构建多模态大模型吗.\n"
        "或者说, 你能察觉到我其实是个机器人吗?",
        "description": "Single speaker speaking Chinese",
    },
    "single-speaker-bgm": {
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "input_text": "[music start] I will remember this, thought Ender, when I am defeated. To keep dignity, and give honor where it's due, so that defeat is not disgrace. And I hope I don't have to do it often. [music end]",
        "description": "Single speaker with BGM using music tag. This is an experimental feature and you may need to try multiple times to get the best result.",
    },
}


@lru_cache(maxsize=20)
def encode_audio_file(file_path):
    """Encode an audio file to base64."""
    with open(file_path, "rb") as audio_file:
        return base64.b64encode(audio_file.read()).decode("utf-8")


def get_current_device():
    """Get the current device."""
    return "cuda" if torch.cuda.is_available() else "cpu"


def resolve_model_and_tokenizer_paths():
    """Prefer locally downloaded artifacts, fallback to HF repo IDs."""
    model_path = LOCAL_MODEL_PATH if os.path.exists(LOCAL_MODEL_PATH) else DEFAULT_MODEL_PATH
    tokenizer_path = LOCAL_AUDIO_TOKENIZER_PATH if os.path.exists(LOCAL_AUDIO_TOKENIZER_PATH) else DEFAULT_AUDIO_TOKENIZER_PATH
    return model_path, tokenizer_path


def _download_voice_preset_file(filename: str):
    """Resolve a voice preset file from local temp_higgs first, then HF."""
    local_path = os.path.join(TEMP_HIGGS_VOICE_DIR, filename)
    if os.path.exists(local_path):
        return local_path

    try:
        from huggingface_hub import hf_hub_download
    except Exception as e:
        logger.warning(f"huggingface_hub not available for voice presets: {e}")
        return None

    rel_path = f"{VOICE_PRESET_DIR}/{filename}"
    try:
        return hf_hub_download(
            repo_id=VOICE_PRESET_SPACE_REPO,
            repo_type="space",
            filename=rel_path,
        )
    except Exception as e:
        logger.warning(f"Failed downloading {rel_path} from {VOICE_PRESET_SPACE_REPO}: {e}")
        return None


def load_voice_presets():
    """Load voice presets from Hugging Face Space assets."""
    try:
        cfg_path = _download_voice_preset_file("config.json")
        if not cfg_path:
            raise FileNotFoundError("Unable to download voice_examples/config.json from HF")
        with open(cfg_path, "r", encoding="utf-8") as f:
            voice_dict = json.load(f)
        voice_presets = {k: v["transcript"] for k, v in voice_dict.items()}
        voice_presets["EMPTY"] = "No reference voice"
        logger.info(f"Loaded voice presets: {list(voice_presets.keys())}")
        return voice_presets
    except FileNotFoundError:
        logger.warning("Voice presets config not found on HF. Using empty voice presets.")
        return {"EMPTY": "No reference voice"}
    except Exception as e:
        logger.error(f"Error loading voice presets: {e}")
        return {"EMPTY": "No reference voice"}


def get_voice_preset(voice_preset):
    """Get cached voice wav path + transcript for a given voice preset."""
    voice_path = _download_voice_preset_file(f"{voice_preset}.wav")
    if not voice_path or not os.path.exists(voice_path):
        logger.warning(f"Voice preset file not found on HF: {voice_preset}.wav")
        return None, "Voice preset not found"

    text = VOICE_PRESETS.get(voice_preset, "No transcript available")
    return voice_path, text


def normalize_chinese_punctuation(text):
    """
    Convert Chinese (full-width) punctuation marks to English (half-width) equivalents.
    """
    # Mapping of Chinese punctuation to English punctuation
    chinese_to_english_punct = {
        "，": ", ",  # comma
        "。": ".",  # period
        "：": ":",  # colon
        "；": ";",  # semicolon
        "？": "?",  # question mark
        "！": "!",  # exclamation mark
        "（": "(",  # left parenthesis
        "）": ")",  # right parenthesis
        "【": "[",  # left square bracket
        "】": "]",  # right square bracket
        "《": "<",  # left angle quote
        "》": ">",  # right angle quote
        "“": '"',  # left double quotation
        "”": '"',  # right double quotation
        "‘": "'",  # left single quotation
        "’": "'",  # right single quotation
        "、": ",",  # enumeration comma
        "—": "-",  # em dash
        "…": "...",  # ellipsis
        "·": ".",  # middle dot
        "「": '"',  # left corner bracket
        "」": '"',  # right corner bracket
        "『": '"',  # left double corner bracket
        "』": '"',  # right double corner bracket
    }

    # Replace each Chinese punctuation with its English counterpart
    for zh_punct, en_punct in chinese_to_english_punct.items():
        text = text.replace(zh_punct, en_punct)

    return text


def normalize_text(transcript: str):
    transcript = normalize_chinese_punctuation(transcript)
    # Other normalizations (e.g., parentheses and other symbols. Will be improved in the future)
    transcript = transcript.replace("(", " ")
    transcript = transcript.replace(")", " ")
    transcript = transcript.replace("°F", " degrees Fahrenheit")
    transcript = transcript.replace("°C", " degrees Celsius")

    for tag, replacement in [
        ("[laugh]", "<SE>[Laughter]</SE>"),
        ("[humming start]", "<SE>[Humming]</SE>"),
        ("[humming end]", "<SE_e>[Humming]</SE_e>"),
        ("[music start]", "<SE_s>[Music]</SE_s>"),
        ("[music end]", "<SE_e>[Music]</SE_e>"),
        ("[music]", "<SE>[Music]</SE>"),
        ("[sing start]", "<SE_s>[Singing]</SE_s>"),
        ("[sing end]", "<SE_e>[Singing]</SE_e>"),
        ("[applause]", "<SE>[Applause]</SE>"),
        ("[cheering]", "<SE>[Cheering]</SE>"),
        ("[cough]", "<SE>[Cough]</SE>"),
    ]:
        transcript = transcript.replace(tag, replacement)

    lines = transcript.split("\n")
    transcript = "\n".join([" ".join(line.split()) for line in lines if line.strip()])
    transcript = transcript.strip()

    if not any([transcript.endswith(c) for c in [".", "!", "?", ",", ";", '"', "'", "</SE_e>", "</SE>"]]):
        transcript += "."

    return transcript


@spaces.GPU
def initialize_engine(model_path, audio_tokenizer_path) -> bool:
    """
    Initialize the HiggsAudioServeEngine with the specified model and tokenizer.

    Args:
        model_path: Path to the model to load
        audio_tokenizer_path: Path to the audio tokenizer to load

    Returns:
        True if initialization was successful, False otherwise
    """
    global engine
    try:
        logger.info(f"Initializing engine with model: {model_path} and audio tokenizer: {audio_tokenizer_path}")
        engine = HiggsAudioServeEngine(
            model_name_or_path=model_path,
            audio_tokenizer_name_or_path=audio_tokenizer_path,
            device=get_current_device(),
        )
        logger.info(f"Successfully initialized HiggsAudioServeEngine with model: {model_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize engine: {e}")
        return False


def check_return_audio(audio_wv: np.ndarray):
    # check if the audio returned is all silent
    if np.all(audio_wv == 0):
        logger.warning("Audio is silent, returning None")


def process_text_output(text_output: str):
    # remove all the continuous <|AUDIO_OUT|> tokens with a single <|AUDIO_OUT|>
    text_output = re.sub(r"(<\|AUDIO_OUT\|>)+", r"<|AUDIO_OUT|>", text_output)
    return text_output


def extract_stop_strings(stop_strings):
    """Parse stop strings from Gradio dataframe payloads robustly."""
    if stop_strings is None:
        return DEFAULT_STOP_STRINGS
    try:
        if isinstance(stop_strings, dict) and "stops" in stop_strings:
            values = stop_strings["stops"]
        elif hasattr(stop_strings, "columns") and hasattr(stop_strings, "values"):
            if "stops" in list(stop_strings.columns):
                values = stop_strings["stops"].tolist()
            else:
                values = [row[0] for row in stop_strings.values.tolist() if row]
        elif isinstance(stop_strings, list):
            values = [row[0] if isinstance(row, (list, tuple)) and row else row for row in stop_strings]
        else:
            values = []

        cleaned = [str(v).strip() for v in values if v is not None and str(v).strip()]
        return cleaned if cleaned else DEFAULT_STOP_STRINGS
    except Exception:
        return DEFAULT_STOP_STRINGS


def prepare_chatml_sample(
    voice_preset: str,
    text: str,
    reference_audio: Optional[str] = None,
    reference_text: Optional[str] = None,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
):
    """Prepare a ChatMLSample for the HiggsAudioServeEngine."""
    messages = []

    # Add system message if provided
    if len(system_prompt) > 0:
        messages.append(Message(role="system", content=system_prompt))

    # Add reference audio if provided
    audio_base64 = None
    ref_text = ""

    if reference_audio:
        # Custom reference audio
        audio_base64 = encode_audio_file(reference_audio)
        ref_text = reference_text or ""
    elif voice_preset != "EMPTY":
        # Voice preset
        voice_path, ref_text = get_voice_preset(voice_preset)
        if voice_path is None:
            logger.warning(f"Voice preset {voice_preset} not found, skipping reference audio")
        else:
            audio_base64 = encode_audio_file(voice_path)

    # Only add reference audio if we have it
    if audio_base64 is not None:
        # Add user message with reference text
        messages.append(Message(role="user", content=ref_text))

        # Add assistant message with audio content
        audio_content = AudioContent(raw_audio=audio_base64, audio_url="")
        messages.append(Message(role="assistant", content=[audio_content]))

    # Add the main user message
    text = normalize_text(text)
    messages.append(Message(role="user", content=text))

    return ChatMLSample(messages=messages)


@spaces.GPU(duration=120)
def text_to_speech(
    text,
    voice_preset,
    reference_audio=None,
    reference_text=None,
    max_completion_tokens=1024,
    temperature=1.0,
    top_p=0.95,
    top_k=50,
    system_prompt=DEFAULT_SYSTEM_PROMPT,
    stop_strings=None,
    ras_win_len=7,
    ras_win_max_num_repeat=2,
):
    """
    Convert text to speech using HiggsAudioServeEngine.

    Args:
        text: The text to convert to speech
        voice_preset: The voice preset to use (or "EMPTY" for no preset)
        reference_audio: Optional path to reference audio file
        reference_text: Optional transcript of the reference audio
        max_completion_tokens: Maximum number of tokens to generate
        temperature: Sampling temperature for generation
        top_p: Top-p sampling parameter
        top_k: Top-k sampling parameter
        system_prompt: System prompt to guide the model
        stop_strings: Dataframe containing stop strings
        ras_win_len: Window length for repetition avoidance sampling
        ras_win_max_num_repeat: Maximum number of repetitions allowed in the window

    Returns:
        Tuple of (generated_text, (sample_rate, audio_data)) where audio_data is int16 numpy array
    """
    global engine

    if engine is None:
        model_path, tokenizer_path = resolve_model_and_tokenizer_paths()
        initialize_engine(model_path, tokenizer_path)

    try:
        # Prepare ChatML sample
        chatml_sample = prepare_chatml_sample(voice_preset, text, reference_audio, reference_text, system_prompt)

        # Convert stop strings format
        stop_list = extract_stop_strings(stop_strings)

        request_id = f"tts-playground-{str(uuid.uuid4())}"
        logger.info(
            f"{request_id}: Generating speech for text: {text[:100]}..., \n"
            f"with parameters: temperature={temperature}, top_p={top_p}, top_k={top_k}, stop_list={stop_list}, "
            f"ras_win_len={ras_win_len}, ras_win_max_num_repeat={ras_win_max_num_repeat}"
        )
        start_time = time.time()

        # Generate using the engine
        response = engine.generate(
            chat_ml_sample=chatml_sample,
            max_new_tokens=max_completion_tokens,
            temperature=temperature,
            top_k=top_k if top_k > 0 else None,
            top_p=top_p,
            stop_strings=stop_list,
            ras_win_len=ras_win_len if ras_win_len > 0 else None,
            ras_win_max_num_repeat=max(ras_win_len, ras_win_max_num_repeat),
        )

        generation_time = time.time() - start_time
        logger.info(f"{request_id}: Generated audio in {generation_time:.3f} seconds")
        gr.Info(f"Generated audio in {generation_time:.3f} seconds")

        # Process the response
        text_output = process_text_output(response.generated_text)

        if response.audio is not None:
            # Convert to int16 for Gradio
            audio_data = (response.audio * 32767).astype(np.int16)
            check_return_audio(audio_data)
            return text_output, (response.sampling_rate, audio_data)
        else:
            logger.warning("No audio generated")
            return text_output, None

    except Exception as e:
        error_msg = f"Error generating speech: {e}"
        logger.error(error_msg)
        gr.Error(error_msg)
        return f"❌ {error_msg}", None


def create_ui():
    my_theme = gr.Theme.load("theme.json")

    # Add custom CSS to disable focus highlighting on textboxes
    custom_css = """
    .gradio-container input:focus,
    .gradio-container textarea:focus,
    .gradio-container select:focus,
    .gradio-container .gr-input:focus,
    .gradio-container .gr-textarea:focus,
    .gradio-container .gr-textbox:focus,
    .gradio-container .gr-textbox:focus-within,
    .gradio-container .gr-form:focus-within,
    .gradio-container *:focus {
        box-shadow: none !important;
        border-color: var(--border-color-primary) !important;
        outline: none !important;
        background-color: var(--input-background-fill) !important;
    }

    /* Override any hover effects as well */
    .gradio-container input:hover,
    .gradio-container textarea:hover,
    .gradio-container select:hover,
    .gradio-container .gr-input:hover,
    .gradio-container .gr-textarea:hover,
    .gradio-container .gr-textbox:hover {
        border-color: var(--border-color-primary) !important;
        background-color: var(--input-background-fill) !important;
    }

    /* Style for checked checkbox */
    .gradio-container input[type="checkbox"]:checked {
        background-color: var(--primary-500) !important;
        border-color: var(--primary-500) !important;
    }
    """

    default_template = "smart-voice"

    """Create the Gradio UI."""
    with gr.Blocks(theme=my_theme, css=custom_css) as demo:
        gr.Markdown("# Higgs Audio Text-to-Speech Playground")

        # Main UI section
        with gr.Row():
            with gr.Column(scale=2):
                # Template selection dropdown
                template_dropdown = gr.Dropdown(
                    label="TTS Template",
                    choices=list(PREDEFINED_EXAMPLES.keys()),
                    value=default_template,
                    info="Select a predefined example for system and input messages.",
                )

                # Template description display
                template_description = gr.HTML(
                    value=f'<p style="font-size: 0.85em; color: var(--body-text-color-subdued); margin: 0; padding: 0;"> {PREDEFINED_EXAMPLES[default_template]["description"]}</p>',
                    visible=True,
                )

                system_prompt = gr.TextArea(
                    label="System Prompt",
                    placeholder="Enter system prompt to guide the model...",
                    value=PREDEFINED_EXAMPLES[default_template]["system_prompt"],
                    lines=2,
                )

                input_text = gr.TextArea(
                    label="Input Text",
                    placeholder="Type the text you want to convert to speech...",
                    value=PREDEFINED_EXAMPLES[default_template]["input_text"],
                    lines=5,
                )

                voice_preset = gr.Dropdown(
                    label="Voice Preset",
                    choices=list(VOICE_PRESETS.keys()),
                    value="EMPTY",
                    interactive=False,  # Disabled by default since default template is not voice-clone
                    visible=False,
                )

                with gr.Accordion(
                    "Custom Reference (Optional)", open=False, visible=False
                ) as custom_reference_accordion:
                    reference_audio = gr.Audio(label="Reference Audio", type="filepath")
                    reference_text = gr.TextArea(
                        label="Reference Text (transcript of the reference audio)",
                        placeholder="Enter the transcript of your reference audio...",
                        lines=3,
                    )

                with gr.Accordion("Advanced Parameters", open=False):
                    max_completion_tokens = gr.Slider(
                        minimum=128,
                        maximum=4096,
                        value=1024,
                        step=10,
                        label="Max Completion Tokens",
                    )
                    temperature = gr.Slider(
                        minimum=0.0,
                        maximum=1.5,
                        value=1.0,
                        step=0.1,
                        label="Temperature",
                    )
                    top_p = gr.Slider(minimum=0.1, maximum=1.0, value=0.95, step=0.05, label="Top P")
                    top_k = gr.Slider(minimum=-1, maximum=100, value=50, step=1, label="Top K")
                    ras_win_len = gr.Slider(
                        minimum=0,
                        maximum=10,
                        value=7,
                        step=1,
                        label="RAS Window Length",
                        info="Window length for repetition avoidance sampling",
                    )
                    ras_win_max_num_repeat = gr.Slider(
                        minimum=1,
                        maximum=10,
                        value=2,
                        step=1,
                        label="RAS Max Num Repeat",
                        info="Maximum number of repetitions allowed in the window",
                    )
                    # Add stop strings component
                    stop_strings = gr.Dataframe(
                        label="Stop Strings",
                        headers=["stops"],
                        datatype=["str"],
                        value=[[s] for s in DEFAULT_STOP_STRINGS],
                        interactive=True,
                        col_count=(1, "fixed"),
                    )

                submit_btn = gr.Button("Generate Speech", variant="primary", scale=1)

            with gr.Column(scale=2):
                output_text = gr.TextArea(label="Model Response", lines=2)

                # Audio output
                output_audio = gr.Audio(label="Generated Audio", interactive=False, autoplay=True)

                stop_btn = gr.Button("Stop Playback", variant="primary")

        # Example voice
        with gr.Row(visible=False) as voice_samples_section:
            voice_samples_table = gr.Dataframe(
                headers=["Voice Preset", "Sample Text"],
                datatype=["str", "str"],
                value=[[preset, text] for preset, text in VOICE_PRESETS.items() if preset != "EMPTY"],
                interactive=False,
            )
            sample_audio = gr.Audio(label="Voice Sample")

        # Function to play voice sample when clicking on a row
        def play_voice_sample(evt: gr.SelectData):
            """
            Play a voice sample when a row is clicked in the voice samples table.

            Args:
                evt: The select event containing the clicked row index

            Returns:
                Path to the voice sample audio file, or None if not found
            """
            try:
                # Get the preset name from the clicked row
                preset_names = [preset for preset in VOICE_PRESETS.keys() if preset != "EMPTY"]
                if evt.index[0] < len(preset_names):
                    preset = preset_names[evt.index[0]]
                    voice_path, _ = get_voice_preset(preset)
                    if voice_path and os.path.exists(voice_path):
                        return voice_path
                    else:
                        gr.Warning(f"Voice sample file not found for preset: {preset}")
                        return None
                else:
                    gr.Warning("Invalid voice preset selection")
                    return None
            except Exception as e:
                logger.error(f"Error playing voice sample: {e}")
                gr.Error(f"Error playing voice sample: {e}")
                return None

        voice_samples_table.select(fn=play_voice_sample, outputs=[sample_audio])

        # Function to handle template selection
        def apply_template(template_name):
            """
            Apply a predefined template to the UI components.

            Args:
                template_name: Name of the template to apply

            Returns:
                Tuple of updated values for system_prompt, input_text, template_description,
                voice_preset, custom_reference_accordion, voice_samples_section, and ras_win_len
            """
            if template_name in PREDEFINED_EXAMPLES:
                template = PREDEFINED_EXAMPLES[template_name]
                # Enable voice preset and custom reference only for voice-clone template
                is_voice_clone = template_name == "voice-clone"
                voice_preset_value = "belinda" if is_voice_clone else "EMPTY"
                # Set ras_win_len to 0 for single-speaker-bgm, 7 for others
                ras_win_len_value = 0 if template_name == "single-speaker-bgm" else 7
                description_text = f'<p style="font-size: 0.85em; color: var(--body-text-color-subdued); margin: 0; padding: 0;"> {template["description"]}</p>'
                return (
                    template["system_prompt"],  # system_prompt
                    template["input_text"],  # input_text
                    description_text,  # template_description
                    gr.update(
                        value=voice_preset_value, interactive=is_voice_clone, visible=is_voice_clone
                    ),  # voice_preset (value and interactivity)
                    gr.update(visible=is_voice_clone),  # custom reference accordion visibility
                    gr.update(visible=is_voice_clone),  # voice samples section visibility
                    ras_win_len_value,  # ras_win_len
                )
            else:
                return (
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                )  # No change if template not found

        # Set up event handlers

        # Connect template dropdown to handler
        template_dropdown.change(
            fn=apply_template,
            inputs=[template_dropdown],
            outputs=[
                system_prompt,
                input_text,
                template_description,
                voice_preset,
                custom_reference_accordion,
                voice_samples_section,
                ras_win_len,
            ],
        )

        # Connect submit button to the TTS function
        submit_btn.click(
            fn=text_to_speech,
            inputs=[
                input_text,
                voice_preset,
                reference_audio,
                reference_text,
                max_completion_tokens,
                temperature,
                top_p,
                top_k,
                system_prompt,
                stop_strings,
                ras_win_len,
                ras_win_max_num_repeat,
            ],
            outputs=[output_text, output_audio],
            api_name="generate_speech",
        )

        # Stop button functionality
        stop_btn.click(
            fn=lambda: None,
            inputs=[],
            outputs=[output_audio],
            js="() => {const audio = document.querySelector('audio'); if(audio) audio.pause(); return null;}",
        )

    return demo


def main():
    """Main function to parse arguments and launch the UI."""
    global DEFAULT_MODEL_PATH, DEFAULT_AUDIO_TOKENIZER_PATH, VOICE_PRESETS

    parser = argparse.ArgumentParser(description="Gradio UI for Text-to-Speech using HiggsAudioServeEngine")
    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        choices=["cuda", "cpu"],
        help="Device to run the model on.",
    )
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host for the Gradio interface.")
    parser.add_argument("--port", type=int, default=7860, help="Port for the Gradio interface.")

    args = parser.parse_args()

    # Update default values if provided via command line
    VOICE_PRESETS = load_voice_presets()

    # Create and launch the UI
    demo = create_ui()
    launch_kwargs = {
        "server_name": args.host,
        "server_port": args.port,
    }
    if "mcp_server" in inspect.signature(demo.launch).parameters:
        launch_kwargs["mcp_server"] = True
    demo.launch(**launch_kwargs)


if __name__ == "__main__":
    main()
