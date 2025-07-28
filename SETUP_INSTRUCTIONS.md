# Pinokio Package Setup Instructions

## Repository Configuration

The installation script is already configured to clone from:
```
https://github.com/PierrunoYT/HiggsAudio-V2-Local.git
```

### 1. Repository Setup ✅ Complete
The [`install.js`](install.js:4) file is configured with the correct repository URL:
```javascript
message: "git clone https://github.com/PierrunoYT/HiggsAudio-V2-Local.git app"
```

### 2. Required Files in Your Repository

Make sure your GitHub repository contains these files:
- `gradio_interface.py` - Main application
- `requirements.txt` - Dependencies  
- `README.md` - Documentation
- `LICENSE` - License file
- `voice_examples/` - Voice samples directory (optional)

### 3. Distribution Files

For the Pinokio package, you only need to distribute these 7 files:
- `pinokio.js` - Main configuration
- `install.js` - Installation script (with your repo URL)
- `start.js` - Startup script
- `torch.js` - PyTorch installation
- `update.js` - Update script
- `reset.js` - Reset script
- `icon.png` - Project icon

### 4. How It Works

1. User installs the Pinokio package (7 files above)
2. When they click "Install", it clones your GitHub repository into `app/` directory
3. Installs all dependencies and sets up the environment
4. User can then start the application through Pinokio interface

This approach ensures users always get the latest version from your repository and you don't need to include the source code in the Pinokio package itself.