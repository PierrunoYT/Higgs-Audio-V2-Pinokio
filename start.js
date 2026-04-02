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
            GRADIO_SERVER_NAME: "127.0.0.1",
            GRADIO_SERVER_PORT: port.toString()
          },
          message: [
            "python app.py"
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
          url: `http://localhost:${port}`
        }
      }
    ]
  }
}
