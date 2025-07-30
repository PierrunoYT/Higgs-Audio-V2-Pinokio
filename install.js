module.exports = {
  run: [
    // Clone the Higgs Audio V2 Enhanced repository
    {
      method: "shell.run",
      params: {
        message: "git clone https://github.com/PierrunoYT/HiggsAudio-V2-Local.git app"
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

    // Install boson_multimodal package in development mode - use main environment
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: "pip install -e temp_higgs/"
      }
    },

    // Install PyTorch with appropriate CUDA support (AFTER all other packages to prevent version conflicts)
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
        text: "Higgs Audio V2 Enhanced installation completed successfully.\n\nNext steps:\n1. Start the application using the Start button\n2. Open the web interface at the provided URL\n3. Begin generating audio with text-to-speech and voice cloning features\n\nFor support, check the README.md file.\n\nNote: All models are public and no HuggingFace authentication required."
      }
    }
  ]
}