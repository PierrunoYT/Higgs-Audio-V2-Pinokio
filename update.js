module.exports = {
  run: [{
    method: "shell.run",
    params: {
      message: "[ -d .git ] && git pull || true"
    }
  }, {
    method: "shell.run",
    params: {
      path: "app",
      message: "[ -d .git ] && git pull || true"
    }
  }]
}
