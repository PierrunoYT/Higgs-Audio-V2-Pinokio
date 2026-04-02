module.exports = {
  run: [
    // Clone the official Higgs Audio package from Boson AI
    {
      method: "shell.run",
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
          "uv pip install -r temp_higgs/requirements.txt"
        ]
      }
    },

    // Install main app dependencies
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: [
          "uv pip install -r requirements.txt"
        ]
      }
    },

    // Install Spaces helper used by app.py decorators
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: [
          "uv pip install spaces"
        ]
      }
    },

    // Install boson_multimodal package in development mode
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: [
          "uv pip install -e temp_higgs/"
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

    // Download Higgs Audio V2 models from Hugging Face
    {
      method: "hf.download",
      params: {
        "_": ["bosonai/higgs-audio-v2-generation-3B-base"],
        "local-dir": "models/higgs-audio-v2-generation-3B-base"
      }
    },

    {
      method: "hf.download",
      params: {
        "_": ["bosonai/higgs-audio-v2-tokenizer"],
        "local-dir": "models/higgs-audio-v2-tokenizer"
      }
    },

    // Verify installation
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: [
          "python -c \"from boson_multimodal.serve.serve_engine import HiggsAudioServeEngine; print('All imports working correctly')\""
        ]
      }
    }
  ]
}
