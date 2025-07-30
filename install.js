module.exports = {
  run: [
    // Clone the Higgs Audio V2 Enhanced repository
    {
      method: "shell.run",
      params: {
        message: "git clone https://github.com/PierrunoYT/HiggsAudio-V2-Local.git app"
      }
    },
    
    // Install PyTorch with appropriate CUDA support
    {
      method: "script.start",
      params: {
        uri: "torch.js",
        params: {
          venv: "env",
          path: "app"
        }
      }
    },
    
    // Clone and install Higgs Audio package
    {
      method: "shell.run",
      params: {
        path: "app",
        message: "git clone https://github.com/boson-ai/higgs-audio.git temp_higgs"
      }
    },
    
    // Install main app dependencies first (using UV for speed)
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: "uv pip install -r requirements.txt"
      }
    },

    // Install Higgs Audio dependencies (using UV for deps) - use main environment
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: "uv pip install -r temp_higgs/requirements.txt"
      }
    },
    
    // Install boson_multimodal package in development mode - use main environment
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: "pip install -e temp_higgs/"
      }
    },
    
    // Verify boson_multimodal installation
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: "python -c \"import boson_multimodal; print('boson_multimodal successfully installed')\""
      }
    },
    
    
    // Install HuggingFace Hub for authentication (using UV for speed)
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: "uv pip install huggingface-hub"
      }
    },
    
    // Download Higgs Audio V2 models from Hugging Face (public models, no auth required)
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: "hf download PierrunoYT/higgs-audio-v2-generation-3B-base --local-dir models/higgs-audio-v2-generation-3B-base --repo-type model"
      }
    },
    
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: "hf download PierrunoYT/higgs-audio-v2-tokenizer --local-dir models/higgs-audio-v2-tokenizer --repo-type model"
      }
    },
    
    // Final verification of all components
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: "python -c \"from boson_multimodal.serve.serve_engine import HiggsAudioServeEngine; print('All imports working correctly')\""
      }
    },
    
    // Create a setup completion marker
    {
      method: "fs.write",
      params: {
        path: "app/INSTALLATION_COMPLETE.txt",
        text: "Higgs Audio V2 Enhanced installation completed successfully.\n\nNext steps:\n1. Authenticate with HuggingFace using 'hf auth login' (required for model access)\n2. Start the application using the Start button\n3. Open the web interface at the provided URL\n\nFor support, check the README.md file.\n\nIf you get authentication errors, run: hf auth login"
      }
    }
  ]
}