# Higgs Audio V2 (Pinokio)

Local text-to-speech using [Higgs Audio V2](https://github.com/boson-ai/higgs-audio) with a Gradio UI: voice cloning, multi-speaker prompts, and optional background-music tags. This folder is a **Pinokio launcher** around `app.py` at the project root.

## What it does

- **Install** clones `boson-ai/higgs-audio` into `temp_higgs`, installs Python dependencies with `uv`, installs PyTorch via `torch.js`, and downloads Hugging Face model weights into `models/`.
- **Start** runs `python app.py` in the `env` virtualenv and binds Gradio to `127.0.0.1` on an available port. Pinokio captures the printed URL and shows **Open Web UI** when ready.
- **Update** runs `git pull` on this repo and on `temp_higgs`, then refreshes dependencies (same order as install) and re-runs `torch.js`.
- **Reset** removes `env`, `temp_higgs`, and `models/` so you can reinstall cleanly.
- **Save Disk Space** (`link.js`) deduplicates library files in the venv via Pinokio `fs.link`.

## How to use (Pinokio)

1. Open this project in Pinokio and run **Install** once.
2. Run **Start** and use **Open Web UI** when the URL appears.
3. Use **Update** after pulling launcher changes or to refresh upstream `higgs-audio`.

CLI overrides for `app.py` (optional):

```text
python app.py --device cuda|cpu --host 127.0.0.1 --port <port>
```

`start.js` sets `GRADIO_SERVER_NAME` and `GRADIO_SERVER_PORT` so the app listens on `127.0.0.1` without extra flags.

## API (programmatic access)

The main Gradio endpoint is named **`generate_speech`** (`api_name="generate_speech"` in `app.py`). After the server is up, use the URL shown in Pinokio (for example `http://127.0.0.1:<port>`).

### Python (`gradio_client`)

Argument order matches `submit_btn.click` in `app.py`: `input_text`, `voice_preset`, `reference_audio`, `reference_text`, `max_completion_tokens`, `temperature`, `top_p`, `top_k`, `system_prompt`, `stop_strings`, `ras_win_len`, `ras_win_max_num_repeat`.

```python
from gradio_client import Client

client = Client("http://127.0.0.1:<port>")  # replace with your URL
result = client.predict(
    "Your text here",       # input_text
    "EMPTY",                # voice_preset
    None,                   # reference_audio (filepath or None)
    "",                     # reference_text
    1024,                   # max_completion_tokens
    1.0,                    # temperature
    0.95,                   # top_p
    50,                     # top_k
    "...",                  # system_prompt (see DEFAULT_SYSTEM_PROMPT in app.py)
    None,                   # stop_strings (DataFrame-like; None uses defaults in the handler)
    7,                      # ras_win_len
    2,                      # ras_win_max_num_repeat
    api_name="/generate_speech",
)
# result: (generated_text, (sample_rate, audio_numpy) | None)
```

Use the **View API** link in the running Gradio app to copy the exact `predict` signature for your Gradio version, especially for `stop_strings`.

### JavaScript

Use the Gradio REST API from the same origin as the UI, or call the backend through a small server you control. Gradio’s HTTP API is version-specific; prefer **`gradio_client`** in Python or the official Gradio JS client for the version pinned in `requirements.txt`.

### curl

Gradio’s JSON-RPC shape depends on the installed Gradio version. Prefer opening `http://127.0.0.1:<port>` and using the **View API** / API recorder in the UI, or use `gradio_client` as above for stable programmatic access.

## Layout

- Launcher scripts: `install.js`, `start.js`, `update.js`, `reset.js`, `link.js`, `torch.js`, `pinokio.js`, `pinokio.json`
- Application: `app.py`, `requirements.txt` at the project root (not under `app/`)
