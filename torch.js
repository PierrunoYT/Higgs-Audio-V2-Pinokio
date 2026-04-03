module.exports = {
  run: [
    // windows nvidia
    {
      "when": "{{platform === 'win32' && gpu === 'nvidia'}}",
      "method": "shell.run",
      "params": {
        "venv": "{{args && args.venv ? args.venv : null}}",
        "path": "{{args && args.path ? args.path : '.'}}",
        "message": "uv pip install torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 {{args && args.xformers ? 'xformers' : ''}} --index-url https://download.pytorch.org/whl/cu128 --force-reinstall --no-deps"
      },
      "next": null
    },
    {
      "when": "{{platform === 'win32' && gpu === 'nvidia' && args && args.triton}}",
      "method": "shell.run",
      "params": {
        "venv": "{{args && args.venv ? args.venv : null}}",
        "path": "{{args && args.path ? args.path : '.'}}",
        "message": "uv pip install triton-windows==3.3.1.post19"
      },
      "next": null
    },
    {
      "when": "{{platform === 'win32' && gpu === 'nvidia' && args && args.sageattention}}",
      "method": "shell.run",
      "params": {
        "venv": "{{args && args.venv ? args.venv : null}}",
        "path": "{{args && args.path ? args.path : '.'}}",
        "message": "python -c \"import sys; import subprocess; mv='sageattention'; v=f'cp{sys.version_info[0]}{sys.version_info[1]}'; tag=f'sageattention-2.1.1+cu128torch2.7.0-{v}-{v}-win_amd64.whl'; url=f'https://github.com/woct0rdho/SageAttention/releases/download/v2.1.1-windows/{tag}'; subprocess.check_call(['uv', 'pip', 'install', url])\""
      },
      "next": null
    },
    // windows amd
    {
      "when": "{{platform === 'win32' && gpu === 'amd'}}",
      "method": "shell.run",
      "params": {
        "venv": "{{args && args.venv ? args.venv : null}}",
        "path": "{{args && args.path ? args.path : '.'}}",
        "message": "uv pip install torch-directml torchaudio torchvision numpy==1.26.4"
      },
      "next": null
    },
    // windows cpu
    {
      "when": "{{platform === 'win32' && (gpu !== 'nvidia' && gpu !== 'amd')}}",
      "method": "shell.run",
      "params": {
        "venv": "{{args && args.venv ? args.venv : null}}",
        "path": "{{args && args.path ? args.path : '.'}}",
        "message": "uv pip install torch torchvision torchaudio numpy==1.26.4"
      },
      "next": null
    },
    // mac
    {
      "when": "{{platform === 'darwin'}}",
      "method": "shell.run",
      "params": {
        "venv": "{{args && args.venv ? args.venv : null}}",
        "path": "{{args && args.path ? args.path : '.'}}",
        "message": "uv pip install torch torchvision torchaudio"
      },
      "next": null
    },
    // linux nvidia
    {
      "when": "{{platform === 'linux' && gpu === 'nvidia'}}",
      "method": "shell.run",
      "params": {
        "venv": "{{args && args.venv ? args.venv : null}}",
        "path": "{{args && args.path ? args.path : '.'}}",
        "message": "uv pip install torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 {{args && args.xformers ? 'xformers' : ''}} --index-url https://download.pytorch.org/whl/cu128 --force-reinstall --no-deps"
      },
      "next": null
    },
    {
      "when": "{{platform === 'linux' && gpu === 'nvidia' && args && args.sageattention}}",
      "method": "shell.run",
      "params": {
        "venv": "{{args && args.venv ? args.venv : null}}",
        "path": "{{args && args.path ? args.path : '.'}}",
        "message": "uv pip install git+https://github.com/thu-ml/SageAttention.git"
      },
      "next": null
    },
    // linux rocm (amd)
    {
      "when": "{{platform === 'linux' && gpu === 'amd'}}",
      "method": "shell.run",
      "params": {
        "venv": "{{args && args.venv ? args.venv : null}}",
        "path": "{{args && args.path ? args.path : '.'}}",
        "message": "uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.2.4 --force-reinstall --no-deps"
      },
      "next": null
    },
    // linux cpu
    {
      "when": "{{platform === 'linux' && (gpu !== 'amd' && gpu !=='nvidia')}}",
      "method": "shell.run",
      "params": {
        "venv": "{{args && args.venv ? args.venv : null}}",
        "path": "{{args && args.path ? args.path : '.'}}",
        "message": "uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"
      },
      "next": null
    }
  ]
}
