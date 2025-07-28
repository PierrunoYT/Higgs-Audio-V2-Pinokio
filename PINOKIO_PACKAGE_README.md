# Higgs Audio V2 Enhanced - Pinokio Package

This directory contains a complete Pinokio installer package for Higgs Audio V2 Enhanced, a comprehensive web-based interface for advanced text-to-speech with voice cloning capabilities.

## Package Contents

### Core Pinokio Files
- **`pinokio.js`** - Main configuration and dynamic menu system
- **`install.js`** - Complete installation workflow
- **`start.js`** - Application startup script with port management
- **`torch.js`** - Cross-platform PyTorch installation
- **`update.js`** - Update workflow for package and dependencies
- **`reset.js`** - Clean removal and reset functionality
- **`icon.png`** - Project icon (512x512px microphone design)

### Additional Files
- **`icon.svg`** - Vector version of the project icon
- **`ICON_INSTRUCTIONS.md`** - Instructions for customizing the icon
- **`PINOKIO_PACKAGE_README.md`** - This documentation file

## Installation Process

The Pinokio installer will:

1. **Create App Directory**: Sets up isolated `app/` directory
2. **Copy Project Files**: Copies all necessary files from current directory
3. **Install PyTorch**: Platform and GPU-specific PyTorch installation
4. **Clone Higgs Audio**: Downloads official Higgs Audio repository
5. **Install Dependencies**: Installs all required Python packages
6. **Setup Environment**: Creates virtual environment with all dependencies
7. **Cleanup**: Removes temporary files and directories

## Features

### Smart Menu System
- **Dynamic State Detection**: Shows appropriate options based on installation status
- **Running Process Awareness**: Detects if installation/startup is in progress
- **Direct Web Access**: "Open Web UI" button when application is running
- **Terminal Access**: View logs and output during operation

### Cross-Platform Support
- **Windows**: Full support with PowerShell commands
- **macOS**: Native support for Intel and Apple Silicon
- **Linux**: Ubuntu/Debian and other distributions

### GPU Optimization
- **NVIDIA CUDA**: Automatic detection and installation of appropriate CUDA version
- **CPU Fallback**: Graceful fallback to CPU-only mode
- **Multiple CUDA Versions**: Support for CUDA 12.8, 12.6, and 11.8

### Robust Installation
- **Error Handling**: Graceful handling of installation failures
- **Dependency Management**: Proper virtual environment isolation
- **Update Support**: Easy updates without full reinstallation
- **Clean Reset**: Complete removal for fresh starts

## Usage Instructions

### For End Users
1. Copy this entire directory to your Pinokio packages folder
2. Launch Pinokio and find "Higgs Audio V2 Enhanced" in your packages
3. Click "Install" to begin the installation process
4. After installation, click "Start" to launch the application
5. Click "Open Web UI" to access the Gradio interface

### For Developers
1. Ensure all source files are in the same directory as the Pinokio scripts
2. Test the installation process in a clean environment
3. Verify cross-platform compatibility
4. Update version numbers in `pinokio.js` as needed

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, macOS 10.15+, or Linux
- **RAM**: 8GB (16GB+ recommended)
- **Storage**: 15GB free space
- **Python**: 3.8+ (installed automatically in virtual environment)

### Recommended for Optimal Performance
- **GPU**: NVIDIA RTX 3070 or better with 8GB+ VRAM
- **RAM**: 16GB or more
- **Storage**: SSD with 25GB+ free space
- **Internet**: Stable connection for model downloads (~6GB)

## Authentication Requirements

The application requires HuggingFace authentication:
- Users need a HuggingFace account and access token
- Authentication is handled via `hf auth login` command
- The startup script checks authentication status
- Clear instructions provided for authentication setup

## Troubleshooting

### Common Issues
1. **Installation Fails**: Check internet connection and disk space
2. **PyTorch Issues**: Verify CUDA compatibility or use CPU mode
3. **Authentication Errors**: Ensure valid HuggingFace token
4. **Memory Issues**: Reduce model parameters or use CPU mode
5. **Port Conflicts**: Pinokio automatically finds available ports

### Debug Information
- Installation logs are available in Pinokio terminal
- Application logs shown during startup
- Error messages include helpful troubleshooting hints
- Reset option available for clean reinstallation

## Technical Details

### Virtual Environment
- Isolated Python environment in `app/env/`
- All dependencies installed within virtual environment
- No conflicts with system Python installation

### Model Management
- Models downloaded automatically on first run
- Cached locally for subsequent uses
- Approximately 6GB download on first initialization

### Port Management
- Automatic port detection and assignment
- Default port 7860 with fallback options
- Accessible via localhost and network interfaces

## Version History

- **v1.0.0**: Initial Pinokio package release
  - Complete installation workflow
  - Cross-platform PyTorch support
  - Dynamic menu system
  - HuggingFace authentication integration

## Support

For issues related to:
- **Pinokio Package**: Check this documentation and Pinokio logs
- **Higgs Audio Model**: Visit [official repository](https://github.com/boson-ai/higgs-audio)
- **Installation Problems**: Use the Reset option and try reinstalling
- **Performance Issues**: Check system requirements and GPU compatibility

## License

This Pinokio package is provided as-is. The underlying Higgs Audio V2 model has its own licensing terms - please refer to the official repository for details.