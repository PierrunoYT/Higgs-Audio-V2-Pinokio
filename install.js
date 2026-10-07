module.exports = {
  requires: {
    bundle: "ai"
  },
  run: [
    {
      method: "fs.rm",
      when: "{{exists('env/.installed')}}",
      params: { path: "env/.installed" }
    },
    // Clone the official Higgs Audio package from Boson AI
    {
      method: "shell.run",
      when: "{{!exists('temp_higgs')}}",
      params: {
        message: [
          "git clone https://github.com/boson-ai/higgs-audio.git temp_higgs"
        ]
      }
    },

    // Install Higgs Audio package requirements
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: [
          "uv pip install -r temp_higgs/requirements.txt -r requirements.txt -e temp_higgs/"
        ]
      }
    },

    // Install PyTorch with appropriate CUDA support LAST to overwrite any CPU-only torch
    {
      method: "script.start",
      params: {
        uri: "torch.js",
        params: {
          venv: "env"
        }
      }
    },

    // Drop downloads in the converted Transformers-native format (unsupported by boson_multimodal)
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: [
          "python -c \"import app; app.remove_stale_model_dirs()\""
        ]
      }
    },

    // Download Higgs Audio V2 models from Hugging Face, pinned to the last original-format
    // revisions (keep in sync with MODEL_REVISION / AUDIO_TOKENIZER_REVISION in app.py)
    {
      method: "hf.download",
      params: {
        "_": ["bosonai/higgs-audio-v2-generation-3B-base"],
        "revision": "10840182ca4ad5d9d9113b60b9bb3c1ef1ba3f84",
        "local-dir": "models/higgs-audio-v2-generation-3B-base"
      }
    },

    {
      method: "hf.download",
      params: {
        "_": ["bosonai/higgs-audio-v2-tokenizer"],
        "revision": "9d4988fbd4ad07b4cac3a5fa462741a41810dbec",
        "local-dir": "models/higgs-audio-v2-tokenizer"
      }
    },

    // Verify installation
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: [
          "uv pip check",
          "python -c \"import app; print('All imports working correctly')\""
        ]
      }
    },
    {
      method: "fs.write",
      params: { path: "env/.installed", text: "Installation verified" }
    }
  ]
}
