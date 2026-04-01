module.exports = async (kernel) => {
  const port = await kernel.port()

  return {
    daemon: true,
    run: [
      {
        method: "shell.run",
        params: {
          venv: "env",
          env: {
            GRADIO_SERVER_PORT: port.toString(),
            GRADIO_SERVER_NAME: "0.0.0.0"
          },
          message: `python gradio_interface.py`,
          on: [{
            event: "/Running on local URL:.*http:\\/\\/[0-9.:]+:[0-9]+/",
            done: true
          }, {
            event: "/Running on public URL:.*https:\\/\\/[a-zA-Z0-9.-]+\\.gradio\\.live/",
            done: true
          }, {
            event: "/Gradio app running/",
            done: true
          }, {
            event: `/http:\\/\\/localhost:${port}/`,
            done: true
          }]
        }
      },
      {
        method: "local.set",
        params: {
          url: `http://localhost:${port}`
        }
      }
    ]
  }
}
