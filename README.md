# Higgs Audio V2 (Pinokio)

Local text-to-speech using [Higgs Audio V2](https://github.com/boson-ai/higgs-audio) with a Gradio UI: voice cloning, multi-speaker prompts, and optional background-music tags. This folder is a **Pinokio launcher** around `app.py` at the project root.

## What it does

- **Install** clones `boson-ai/higgs-audio` into `temp_higgs`, installs Python dependencies with `uv`, installs PyTorch via `torch.js`, and downloads Hugging Face model weights into `models/`.
- **Start** runs `python app.py` in the `env` virtualenv and binds Gradio to `127.0.0.1` on an available port. Pinokio captures the printed URL and shows **Open Web UI** when ready.
- **Update** fast-forwards this repo and `temp_higgs`, then runs the installation flow to refresh dependencies, recover missing models, and verify imports.
- **Reset** removes `env`, `temp_higgs`, `models/`, and `voice_preset_cache/` so you can reinstall cleanly.
- **Save Disk Space** (`link.js`) deduplicates library files in the venv via Pinokio `fs.link`.

## How to use (Pinokio)

1. Open this project in Pinokio and run **Install** once.
2. Run **Start** and use **Open Web UI** when the URL appears.
3. Use **Update** after pulling launcher changes or to refresh upstream `higgs-audio`.

Install writes `env/.installed` only after downloads, dependency checks, and application imports succeed. If installation fails, run **Install** again. Existing installations created before this marker was introduced also need one **Install** run; existing repositories and downloaded model files are reused.

NVIDIA uses CUDA PyTorch, Linux AMD uses ROCm, and Windows AMD uses CPU because this UI does not implement DirectML. macOS currently runs inference on CPU. Hardware support and memory requirements still depend on the upstream model.

Voice presets download on demand into `voice_preset_cache/` from the third-party Hugging Face Space `smola/higgs_audio_v2`. Set `HIGGS_VOICE_PRESET_SPACE_REPO` to use another compatible Space. If presets are unavailable, upload a reference recording or use **EMPTY**. Switching away from the voice-clone template clears custom references.

CLI overrides for `app.py` (optional):

```text
python app.py --device cuda|cpu --host 127.0.0.1 --port <port>
```

`start.js` sets `GRADIO_SERVER_NAME` and `GRADIO_SERVER_PORT` so the app listens on `127.0.0.1` without extra flags.
When running `app.py` directly without a port override, Gradio selects an available port.

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
    None,                   # reference_audio; use handle_file(path) for an upload
    "",                     # reference_text
    1024,                   # max_completion_tokens
    1.0,                    # temperature
    0.95,                   # top_p
    50,                     # top_k
    "Generate audio following instruction.",  # system_prompt
    None,                   # stop_strings (DataFrame-like; None uses defaults in the handler)
    7,                      # ras_win_len
    2,                      # ras_win_max_num_repeat
    api_name="/generate_speech",
)
# result: (generated_text, downloaded_audio_filepath | None)
```

To clone a recording, import `handle_file` from `gradio_client`, pass `handle_file("reference.wav")` as the third argument, and provide its transcript as the fourth. The Python handler's internal NumPy audio tuple is serialized by Gradio; clients receive a file instead.

Use the **View API** link in the running Gradio app to copy the exact `predict` signature for your Gradio version, especially for `stop_strings`.

### JavaScript

Install `@gradio/client` and use the server URL shown by Pinokio:

```javascript
import { Client } from "@gradio/client";

const client = await Client.connect("http://127.0.0.1:7860"); // replace port
const result = await client.predict("/generate_speech", [
  "Hello from Higgs Audio.", "EMPTY", null, "", 1024, 1.0, 0.95, 50,
  "Generate audio following instruction.", null, 7, 2
]);
console.log(result.data); // generated text and audio file metadata (or null)
```

### curl

For Gradio 5, submit a job, then read its server-sent events stream (POSIX shell examples):

```sh
curl -X POST http://127.0.0.1:7860/gradio_api/call/generate_speech \
  -H 'Content-Type: application/json' \
  -d '{"data":["Hello from Higgs Audio.","EMPTY",null,"",1024,1.0,0.95,50,"Generate audio following instruction.",null,7,2]}'

# Replace EVENT_ID with event_id from the previous response.
curl -N http://127.0.0.1:7860/gradio_api/call/generate_speech/EVENT_ID
```

Replace port `7860` with the actual server port. This launcher requires Gradio 5.50 or later within version 5; older Gradio clients can fail to build the audio API schema with current Pydantic releases. The running app's **View API** page gives the exact URLs for the installed version. Empty input and generation failures return API errors; silent output returns no audio with a UI warning.

## Development checks

Use an isolated Python environment with NumPy and a supported Gradio version installed:

```text
python -m unittest discover -s tests -v
node --test tests/launcher.test.js
```

The tests cover generation edge cases with a mocked model, real NumPy audio conversion, real Gradio UI construction and API schema, launcher menus, URL capture, and platform branch selection. They do not download model weights or verify GPU inference. The UI smoke test skips if Gradio is unavailable.

## Layout

- Launcher scripts: `install.js`, `start.js`, `update.js`, `reset.js`, `link.js`, `torch.js`, `pinokio.js`, `pinokio.json`
- Application: `app.py`, `requirements.txt` at the project root (not under `app/`)
