module.exports = {
  run: [
    {
      method: "shell.run",
      params: {
        message: "git pull"
      }
    },
    {
      method: "shell.run",
      when: "{{exists('temp_higgs')}}",
      params: {
        path: "temp_higgs",
        message: "git pull"
      }
    },
    {
      method: "shell.run",
      when: "{{exists('temp_higgs')}}",
      params: {
        venv: "env",
        message: [
          "uv pip install -r temp_higgs/requirements.txt"
        ]
      }
    },
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: [
          "uv pip install -r requirements.txt"
        ]
      }
    },
    {
      method: "shell.run",
      when: "{{exists('temp_higgs')}}",
      params: {
        venv: "env",
        message: [
          "uv pip install -e temp_higgs/"
        ]
      }
    },
    {
      method: "script.start",
      params: {
        uri: "torch.js",
        params: {
          venv: "env"
        }
      }
    }
  ]
}
