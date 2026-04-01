module.exports = {
  run: [{
    method: "shell.run",
    params: {
      message: "git pull"
    }
  }, {
    method: "shell.run",
    params: {
      path: "temp_higgs",
      message: "git pull"
    }
  }, {
    method: "shell.run",
    params: {
      venv: "env",
      message: "pip install -e temp_higgs/"
    }
  }]
}
