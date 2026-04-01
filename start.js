module.exports = {
  daemon: true,
  run: [
    {
      method: "shell.run",
      params: {
        venv: "env",
        env: {
          GRADIO_SERVER_NAME: "127.0.0.1"
        },
        message: [
          "python gradio_interface.py"
        ],
        on: [{
          event: "/(http:\\/\\/\\S+)/",
          done: true
        }]
      }
    },
    {
      method: "local.set",
      params: {
        url: "{{input.event[1]}}"
      }
    }
  ]
}
