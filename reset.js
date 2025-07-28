module.exports = {
  run: [
    // Remove the entire app directory (Windows)
    {
      when: "{{platform === 'win32'}}",
      method: "shell.run",
      params: {
        message: "if exist app rmdir /s /q app"
      }
    },
    
    // Remove the entire app directory (Unix-like)
    {
      when: "{{platform !== 'win32'}}",
      method: "shell.run",
      params: {
        message: "if [ -d app ]; then rm -rf app; fi"
      }
    },
    
    // Log completion message
    {
      method: "log",
      params: {
        text: "🗑️ Higgs Audio V2 Enhanced has been completely removed. You can reinstall it using the Install button."
      }
    }
  ]
}