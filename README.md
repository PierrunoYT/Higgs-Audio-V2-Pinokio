# Higgs Audio V2 Enhanced Gradio Interface

A comprehensive web-based interface for Higgs Audio V2, featuring advanced text-to-speech capabilities with voice cloning, multi-speaker support, and background music generation.

## Features

### Core Features
- **Expressive Speech Generation**: Convert text to natural, expressive speech
- **Voice Cloning**: Clone voices using reference audio samples
- **Multi-Speaker Dialogues**: Generate conversations with different speakers
- **Background Music Generation**: Add music to speech using special tags
- **Advanced Scene Control**: Customize audio environment and recording conditions
- **Template System**: Pre-configured templates for different TTS modes

### Advanced Controls
- **Extended Temperature Range**: 0.0-1.5 for fine-tuned creativity control
- **RAS (Repetition Avoidance Sampling)**: Prevents repetitive output
- **Custom Stop Strings**: Control generation termination
- **Advanced Sampling Parameters**: Top-p, top-k, and token settings
- **Real-time Audio Playback**: Listen to generated speech directly in the browser
- **Voice Preset Library**: Pre-loaded voice samples for quick cloning

### Interface Features
- **Template-based Examples**: Smart voice, voice cloning, multi-speaker, BGM, and more
- **Custom Reference Audio**: Upload your own audio for voice cloning
- **Voice Sample Preview**: Listen to voice presets before selection
- **Enhanced Theme**: Professional UI with custom styling
- **Easy-to-use Interface**: Clean, intuitive web interface built with Gradio

## About Higgs Audio V2

Higgs Audio V2 is a 3.6B parameter audio foundation model that:
- Trained on 10M+ hours of diverse audio data
- Achieves 75.7% win rate over GPT-4o-mini-TTS on emotional speech
- Supports multilingual multi-speaker dialogues
- Can generate speech with background music and prosody adaptation
- Requires no fine-tuning for high-quality results

## Installation

### Prerequisites

- Python 3.8 or higher
- CUDA-compatible GPU (recommended) or CPU
- At least 8GB RAM (16GB+ recommended for GPU)

### Setup

1. **Clone or download this repository:**
   ```bash
   git clone <your-repo-url>
   cd "Higgs Audio V2"
   ```

2. **Create and activate virtual environment:**
   ```bash
   # On Windows:
   python -m venv higgs_audio_env
   higgs_audio_env\Scripts\activate
   
   # On macOS/Linux:
   python3 -m venv higgs_audio_env
   source higgs_audio_env/bin/activate
   ```

3. **Install PyTorch with CUDA support (recommended):**
   ```bash
   # For CUDA 12.8 (latest):
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
   
   # For CUDA 12.6:
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
   
   # For CUDA 11.8:
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   
   # CPU-only (if no GPU):
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   ```

4. **Clone and install the Higgs Audio package:**
   ```bash
   # Clone the official repository
   git clone https://github.com/boson-ai/higgs-audio.git temp_higgs
   cd temp_higgs

   # Install dependencies and the package
   pip install -r requirements.txt
   pip install -e .
   cd ..
   ```

5. **Install interface dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

6. **Authenticate with HuggingFace (Required):**
   ```bash
   # Install huggingface-hub if not already installed
   pip install huggingface-hub
   
   # Login to HuggingFace to access the models
   hf auth login
   ```
   When prompted, enter your HuggingFace Access Token. You can create one at: https://huggingface.co/settings/tokens

7. **Clean up (optional):**
   ```bash
   # Remove the temporary clone directory
   rmdir /s temp_higgs  # Windows
   # rm -rf temp_higgs   # macOS/Linux
   ```

7. **Clean up (optional):**
   ```bash
   # Remove the temporary clone directory
   rmdir /s temp_higgs  # Windows
   # rm -rf temp_higgs   # macOS/Linux
   ```

## Usage

1. **Activate the virtual environment:**
   ```bash
   # On Windows:
   higgs_audio_env\Scripts\activate

   # On macOS/Linux:
   source higgs_audio_env/bin/activate
   ```

2. **Ensure HuggingFace authentication (if not done during installation):**
   ```bash
   hf auth login
   ```

3. **Start the Gradio interface:**
   ```bash
   python gradio_interface.py
   ```

4. **Open your browser** and navigate to `http://localhost:7860`

5. **Initialize the model** by clicking the "Initialize Model" button (first-time setup may take a few minutes to download models)

6. **Generate speech:**
   - Enter your text in the "Text to speak" field
   - Optionally customize the scene description
   - Adjust advanced settings if needed
   - Click "Generate Speech"
   - Listen to the generated audio in the output player

## Interface Components

### Main Controls
- **Text Input**: Enter the text you want to convert to speech
- **Scene Description**: Describe the recording environment (e.g., "quiet room", "outdoor park")
- **Generate Speech Button**: Process the text and create audio

### Advanced Settings
- **Temperature (0.1-1.0)**: Controls creativity/randomness in generation
- **Top-p (0.1-1.0)**: Nucleus sampling parameter for token selection
- **Top-k (1-100)**: Limits token selection to top k choices
- **Max Tokens (256-2048)**: Maximum length of generated audio sequence

### Example Prompts
Pre-loaded examples include:
- Factual narration
- Presentation speech
- Storytelling
- Casual conversation

## System Requirements

### Minimum Requirements
- **CPU**: Multi-core processor (Intel i5/AMD Ryzen 5 or better)
- **RAM**: 8GB
- **Storage**: 10GB free space
- **OS**: Windows 10/11, macOS 10.15+, or Linux

### Recommended for Best Performance
- **GPU**: NVIDIA RTX 3070 or better with 8GB+ VRAM
- **RAM**: 16GB or more
- **Storage**: SSD with 20GB+ free space

## Troubleshooting

### Common Issues

**"Error loading model: argument of type 'HiggsAudioConfig' is not iterable":**
- This occurs when using an incomplete installation of boson_multimodal
- **Solution:** Follow the updated installation steps above to clone and install from the official repository
- Make sure to activate the virtual environment before running the interface

**Model fails to load:**
- Ensure you have sufficient RAM/VRAM (minimum 8GB RAM, 16GB+ recommended)
- Check that CUDA is properly installed if using GPU
- Verify internet connection for model download (first run downloads ~6GB)
- **Verify HuggingFace authentication:** Run `hf auth login` and enter your access token
- Make sure you're running in the activated virtual environment

**"ModuleNotFoundError: No module named 'boson_multimodal.serve'":**
- This indicates the package wasn't installed correctly or virtual environment isn't activated
- **Solution:**
  1. Make sure virtual environment is activated: `higgs_audio_env\Scripts\activate` (Windows) or `source higgs_audio_env/bin/activate` (macOS/Linux)
  2. Reinstall using the proper method described in step 4 above

**Audio generation is slow:**
- Reduce max_tokens setting (try 512 instead of 1024)
- Use CPU if GPU memory is insufficient
- Close other applications to free up resources
- First generation is always slower due to model loading

**Poor audio quality:**
- Adjust temperature (lower values like 0.1-0.3 for more consistent output)
- Modify scene description for better context
- Try different top-p/top-k values
- Ensure your input text ends with proper punctuation

### Performance Tips

- **First run**: Model download and initialization may take 5-10 minutes (downloads ~6GB of model files)
- **GPU usage**: Monitor VRAM usage; the model requires ~8GB VRAM for optimal performance
- **CPU fallback**: The interface automatically falls back to CPU if CUDA is unavailable (much slower)
- **Virtual environment**: Always run the interface within the activated virtual environment
- **Memory management**: Close other applications if experiencing memory issues
- **Generation speed**: First generation is slower due to model loading; subsequent generations are faster

## Project Structure

After installation, your project directory should look like this:

```
Higgs Audio V2/
├── gradio_interface.py          # Main Gradio web interface
├── requirements.txt             # Interface dependencies
├── README.md                   # This file
├── .gitignore                  # Git ignore rules
└── higgs_audio_env/            # Virtual environment (created during setup)
    ├── Scripts/                # Windows activation scripts
    ├── bin/                    # macOS/Linux activation scripts
    └── Lib/                    # Installed packages
```

## Configuration

The interface can be customized by modifying `gradio_interface.py`:

```python
# Change default model paths
MODEL_PATH = "bosonai/higgs-audio-v2-generation-3B-base"
AUDIO_TOKENIZER_PATH = "bosonai/higgs-audio-v2-tokenizer"

# Modify server settings
demo.launch(
    share=True,           # Enable public sharing
    server_name="0.0.0.0", # Allow external connections
    server_port=7860      # Change port number
)
```

## License

This project uses the Higgs Audio V2 model. Please refer to the [original repository](https://github.com/boson-ai/higgs-audio) for licensing information.

## Credits

- **Higgs Audio V2**: Developed by Boson AI
- **Original Repository**: https://github.com/boson-ai/higgs-audio
- **Model Page**: https://huggingface.co/bosonai/higgs-audio-v2-generation-3B-base

## Support

For issues related to:
- **Higgs Audio model**: Visit the [official repository](https://github.com/boson-ai/higgs-audio)
- **This Gradio interface**: Open an issue in this repository
- **General Gradio questions**: Check the [Gradio documentation](https://gradio.app/docs/)