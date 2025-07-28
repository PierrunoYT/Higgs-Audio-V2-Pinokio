module.exports = {
  run: [
    // Update the main project repository
    {
      method: "shell.run",
      params: {
        path: "app",
        message: "git pull origin main"
      }
    },
    
    // Update Higgs Audio package
    {
      method: "shell.run",
      params: {
        path: "app",
        message: "git clone https://github.com/boson-ai/higgs-audio.git temp_higgs_update"
      }
    },
    
    // Install updated Higgs Audio package (using UV for speed)
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app/temp_higgs_update",
        message: [
          "uv pip install -r requirements.txt",
          "uv pip install -e . --upgrade"
        ]
      }
    },
    
    // Update interface dependencies (using UV for speed)
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: "uv pip install -r requirements.txt --upgrade"
      }
    },
    
    // Clean up temporary update directory (Windows)
    {
      when: "{{platform === 'win32'}}",
      method: "shell.run",
      params: {
        path: "app",
        message: "rmdir /s /q temp_higgs_update"
      }
    },
    
    // Clean up temporary update directory (Unix-like)
    {
      when: "{{platform !== 'win32'}}",
      method: "shell.run",
      params: {
        path: "app",
        message: "rm -rf temp_higgs_update"
      }
    },
    
    // Update completion marker
    {
      method: "fs.write",
      params: {
        path: "app/UPDATE_COMPLETE.txt",
        text: "Higgs Audio V2 Enhanced update completed successfully.\n\nUpdated components:\n- Higgs Audio package\n- Interface dependencies\n- Project files\n\nYou can now start the application using the Start button."
      }
    },
    
    // Log completion message
    {
      method: "log",
      params: {
        text: "✅ Higgs Audio V2 Enhanced has been updated successfully!"
      }
    }
  ]
}