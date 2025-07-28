# How to Create a Pinokio Script

This guide explains how to create a Pinokio script based on the Hunyuan3D-2-LowVRAM example. Pinokio is a package manager for AI applications that uses JavaScript configuration files to define installation, startup, and management workflows.

## Core Files Structure

A typical Pinokio script consists of these JavaScript files:

```
your-project/
├── pinokio.js      # Main configuration and menu system
├── install.js      # Installation workflow
├── start.js        # Application startup
├── update.js       # Update workflow
├── reset.js        # Reset/cleanup workflow
├── torch.js        # PyTorch installation (optional)
└── icon.png        # Project icon
```

## 1. Main Configuration (`pinokio.js`)

The main configuration file defines your project metadata and dynamic menu system:

```javascript
const path = require('path')
module.exports = {
  version: "1.0.0",
  title: "Your Project Name",
  description: "Description of your AI project",
  icon: "icon.png",
  menu: async (kernel, info) => {
    let installed = info.exists("app/env")  // Check if installed
    let running = {
      install: info.running("install.js"),
      start: info.running("start.js"),
      update: info.running("update.js"),
      reset: info.running("reset.js")
    }
    
    // Show different menus based on state
    if (running.install) {
      return [{
        default: true,
        icon: "fa-solid fa-plug",
        text: "Installing",
        href: "install.js",
      }]
    } else if (installed) {
      if (running.start) {
        let local = info.local("start.js")
        if (local && local.url) {
          return [{
            default: true,
            icon: "fa-solid fa-rocket",
            text: "Open Web UI",
            href: local.url,
          }, {
            icon: 'fa-solid fa-terminal',
            text: "Terminal",
            href: "start.js",
          }]
        }
      } else {
        // Main menu when installed but not running
        return [{
          icon: "fa-solid fa-power-off",
          text: "Start Application",
          href: "start.js"
        }, {
          icon: "fa-solid fa-plug",
          text: "Update",
          href: "update.js",
        }, {
          icon: "fa-solid fa-plug",
          text: "Install",
          href: "install.js",
        }, {
          icon: "fa-regular fa-circle-xmark",
          text: "Reset",
          href: "reset.js",
        }]
      }
    } else {
      // Not installed - show install option
      return [{
        default: true,
        icon: "fa-solid fa-plug",
        text: "Install",
        href: "install.js",
      }]
    }
  }
}
```

### Advanced Menu Features

You can create nested menus and platform-specific options:

```javascript
// Platform-specific menus
if (kernel.platform === "darwin") {
  // macOS specific options
} else {
  // Windows/Linux options
}

// Nested menus
return [{
  icon: "fa-solid fa-power-off",
  text: "Start Options",
  menu: [{
    icon: "fa-solid fa-cube",
    text: "Basic Mode",
    href: "start.js",
    params: { mode: "basic" }
  }, {
    icon: "fa-solid fa-bolt-lightning",
    text: "Advanced Mode",
    href: "start.js",
    params: { mode: "advanced" }
  }]
}]
```

## 2. Installation Script (`install.js`)

Defines the installation workflow:

```javascript
module.exports = {
  run: [
    // Clone repository
    {
      method: "shell.run",
      params: {
        message: "git clone https://github.com/your-repo/project.git app"
      }
    },
    
    // Install PyTorch (optional)
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
    
    // Install dependencies
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: [
          "pip install -r requirements.txt",
          "pip install additional-package"
        ]
      }
    },
    
    // Platform-specific installations
    {
      when: "{{platform === 'win32'}}",
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: "pip install windows-specific-package"
      }
    }
  ]
}
```

### Installation Methods

- `shell.run`: Execute shell commands
- `script.start`: Run another script
- `fs.rm`: Remove files/directories
- `fs.link`: Create symbolic links

### Conditional Installation

Use `when` conditions for platform or GPU-specific installations:

```javascript
{
  when: "{{platform === 'linux' && gpu === 'nvidia'}}",
  method: "shell.run",
  params: {
    message: "pip install torch --index-url https://download.pytorch.org/whl/cu118"
  }
}
```

## 3. Startup Script (`start.js`)

Defines how to start your application:

```javascript
module.exports = async (kernel) => {
  const port = await kernel.port()  // Get available port
  
  return {
    daemon: true,  // Keep running in background
    run: [
      {
        method: "shell.run",
        params: {
          venv: "env",
          path: "app",
          message: `python app.py --port ${port}`,
          on: [{
            // Wait for server to start
            event: "/http:\/\/[0-9.:]+/",
            done: true
          }]
        }
      },
      {
        // Set URL for "Open Web UI" button
        method: "local.set",
        params: {
          url: "{{input.event[0]}}"
        }
      }
    ]
  }
}
```

### Event Monitoring

Monitor shell output for specific patterns:

```javascript
on: [{
  event: "/Server running on port [0-9]+/",  // Regex pattern
  done: true  // Continue to next step when matched
}]
```

## 4. PyTorch Installation (`torch.js`)

Handle PyTorch installation across platforms with latest optimizations:

```javascript
module.exports = {
  run: [
    // Windows NVIDIA with advanced optimizations
    {
      when: "{{platform === 'win32' && gpu === 'nvidia'}}",
      method: "shell.run",
      params: {
        venv: "{{args && args.venv ? args.venv : null}}",
        path: "{{args && args.path ? args.path : '.'}}",
        message: [
          "uv pip install torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 {{args && args.xformers ? 'xformers' : ''}} --index-url https://download.pytorch.org/whl/cu128",
          "{{args && args.triton ? 'uv pip install -U triton-windows' : ''}}",
          "{{args && args.sageattention ? 'uv pip install https://github.com/woct0rdho/SageAttention/releases/download/v2.1.1-windows/sageattention-2.1.1+cu128torch2.7.0-cp310-cp310-win_amd64.whl' : ''}}"
        ]
      },
      next: null
    },
    
    // Windows AMD GPU support
    {
      when: "{{platform === 'win32' && gpu === 'amd'}}",
      method: "shell.run",
      params: {
        venv: "{{args && args.venv ? args.venv : null}}",
        path: "{{args && args.path ? args.path : '.'}}",
        message: "uv pip install torch-directml torchaudio torchvision numpy==1.26.4"
      },
      next: null
    },
    
    // Windows CPU fallback
    {
      when: "{{platform === 'win32' && (gpu !== 'nvidia' && gpu !== 'amd')}}",
      method: "shell.run",
      params: {
        venv: "{{args && args.venv ? args.venv : null}}",
        path: "{{args && args.path ? args.path : '.'}}",
        message: "uv pip install torch torchvision torchaudio numpy==1.26.4"
      },
      next: null
    },
    
    // macOS (Apple Silicon and Intel)
    {
      when: "{{platform === 'darwin'}}",
      method: "shell.run",
      params: {
        venv: "{{args && args.venv ? args.venv : null}}",
        path: "{{args && args.path ? args.path : '.'}}",
        message: "uv pip install torch torchvision torchaudio"
      },
      next: null
    },
    
    // Linux NVIDIA with optimizations
    {
      when: "{{platform === 'linux' && gpu === 'nvidia'}}",
      method: "shell.run",
      params: {
        venv: "{{args && args.venv ? args.venv : null}}",
        path: "{{args && args.path ? args.path : '.'}}",
        message: [
          "uv pip install torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 {{args && args.xformers ? 'xformers' : ''}} --index-url https://download.pytorch.org/whl/cu128",
          "{{args && args.sageattention ? 'uv pip install git+https://github.com/thu-ml/SageAttention.git' : ''}}"
        ]
      },
      next: null
    },
    
    // Linux AMD (ROCm support)
    {
      when: "{{platform === 'linux' && gpu === 'amd'}}",
      method: "shell.run",
      params: {
        venv: "{{args && args.venv ? args.venv : null}}",
        path: "{{args && args.path ? args.path : '.'}}",
        message: "uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.2.4"
      },
      next: null
    },
    
    // Linux CPU fallback
    {
      when: "{{platform === 'linux' && (gpu !== 'amd' && gpu !=='nvidia')}}",
      method: "shell.run",
      params: {
        venv: "{{args && args.venv ? args.venv : null}}",
        path: "{{args && args.path ? args.path : '.'}}",
        message: "uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"
      },
      next: null
    }
  ]
}
```

### Advanced PyTorch Features

The updated torch.js includes support for:

- **PyTorch 2.7.0**: Latest version with performance improvements
- **CUDA 12.8**: Latest CUDA support for NVIDIA GPUs
- **UV Package Manager**: Lightning-fast installation speeds
- **XFormers**: Memory-efficient attention mechanisms (optional)
- **Triton**: GPU kernel optimization for Windows (optional)
- **SageAttention**: Advanced attention optimization (optional)
- **AMD GPU Support**: DirectML for Windows, ROCm for Linux
- **Proper Fallbacks**: CPU-only installation when GPU unavailable

### Optional Parameters

You can pass additional parameters to enable optimizations:

```javascript
{
  method: "script.start",
  params: {
    uri: "torch.js",
    params: {
      venv: "env",
      path: "app",
      xformers: true,      // Enable XFormers
      triton: true,        // Enable Triton (Windows)
      sageattention: true  // Enable SageAttention
    }
  }
}
```

## 5. Update Script (`update.js`)

Handle project updates:

```javascript
module.exports = {
  run: [
    {
      method: "shell.run",
      params: {
        message: "git pull"  // Update main repo
      }
    },
    {
      method: "shell.run",
      params: {
        path: "app",
        message: "git pull"  // Update app repo
      }
    },
    {
      method: "fs.rm",
      params: {
        path: "app/env"  // Remove old environment
      }
    }
  ]
}
```

## 6. Reset Script (`reset.js`)

Clean reset functionality:

```javascript
module.exports = {
  run: [{
    method: "fs.rm",
    params: {
      path: "app"  // Remove entire app directory
    }
  }]
}
```

## Template Variables

Pinokio supports template variables in double braces:

- `{{platform}}` - Operating system (win32, darwin, linux)
- `{{gpu}}` - GPU type (nvidia, amd, cpu)
- `{{args.paramName}}` - Parameters passed from menu
- `{{which('command')}}` - Find command path

## Environment Variables

Set environment variables for shell commands:

```javascript
{
  method: "shell.run",
  params: {
    env: {
      CUDA_VISIBLE_DEVICES: "0",
      PYTHONPATH: "/custom/path"
    },
    message: "python script.py"
  }
}
```

## Best Practices

1. **Use UV Package Manager**: Replace `pip install` with `uv pip install` for lightning-fast installations
2. **Check Dependencies**: Use `when` conditions to install only what's needed
3. **Virtual Environments**: Always use `venv` parameter for Python packages
4. **Error Handling**: Use `next: null` to stop on errors
5. **Platform Support**: Test on all target platforms (Windows, macOS, Linux)
6. **GPU Optimization**: Support NVIDIA CUDA, AMD DirectML/ROCm, and CPU fallbacks
7. **Resource Management**: Use appropriate memory/VRAM profiles
8. **User Experience**: Provide clear menu options and status indicators
9. **Latest PyTorch**: Use PyTorch 2.7.0+ with CUDA 12.8 for best performance
10. **Optional Optimizations**: Include xformers, triton, and sageattention for advanced users

### UV Package Manager Benefits

- **Speed**: 10-100x faster than traditional pip
- **Compatibility**: Drop-in replacement for pip commands
- **Reliability**: Better dependency resolution
- **Usage**: Simply prefix pip commands with `uv`: `uv pip install package`

### GPU Support Matrix

| Platform | NVIDIA | AMD | CPU |
|----------|--------|-----|-----|
| Windows | CUDA 12.8 + XFormers + Triton | DirectML | CPU-only |
| Linux | CUDA 12.8 + XFormers + SageAttention | ROCm 6.2.4 | CPU-only |
| macOS | N/A | N/A | CPU + Metal |

## Testing Your Script

1. Create the JavaScript files in your project directory
2. Add an `icon.png` file (recommended 512x512px)
3. Test installation, startup, and reset workflows
4. Verify cross-platform compatibility
5. Test with different hardware configurations

## Example Project Structure

```
my-ai-project/
├── pinokio.js          # Main config
├── install.js          # Installation
├── start.js            # Startup
├── update.js           # Updates
├── reset.js            # Reset
├── torch.js            # PyTorch setup
├── icon.png            # Project icon
└── README.md           # Documentation
```

This structure provides a complete Pinokio package that users can install and manage through the Pinokio interface.