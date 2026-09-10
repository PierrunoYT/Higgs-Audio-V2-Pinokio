module.exports = {
  run: [
    {
      method: "shell.run",
      params: { message: "git pull --ff-only" }
    },
    {
      method: "shell.run",
      when: "{{exists('temp_higgs/.git')}}",
      params: { path: "temp_higgs", message: "git pull --ff-only" }
    },
    {
      method: "script.start",
      params: { uri: "install.js" }
    }
  ]
}
