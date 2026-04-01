module.exports = {
  run: [
    // Clone the official Higgs Audio package from Boson AI
    {
      method: "shell.run",
      params: {
        message: "git clone https://github.com/boson-ai/higgs-audio.git temp_higgs"
      }
    },
    
    // Install Higgs Audio package requirements
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: "uv pip install -r temp_higgs/requirements.txt"
      }
    },

    // Install main app dependencies
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: "uv pip install -r requirements.txt"
      }
    },

    // Install boson_multimodal package in development mode
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: "pip install -e temp_higgs/"
      }
    },

    // Install PyTorch with appropriate CUDA support
    {
      method: "script.start",
      params: {
        uri: "torch.js",
        params: {
          venv: "env"
        }
      }
    },
    
    // Install HuggingFace Hub CLI
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: "uv pip install huggingface-hub"
      }
    },
    
    // Download Higgs Audio V2 models from Hugging Face
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: "huggingface-cli download bosonai/higgs-audio-v2-generation-3B-base --local-dir models/higgs-audio-v2-generation-3B-base --repo-type model"
      }
    },
    
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: "huggingface-cli download bosonai/higgs-audio-v2-tokenizer --local-dir models/higgs-audio-v2-tokenizer --repo-type model"
      }
    },
    
    // Verify installation
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: "python -c \"from boson_multimodal.serve.serve_engine import HiggsAudioServeEngine; print('All imports working correctly')\""
      }
    }
  ]
}
