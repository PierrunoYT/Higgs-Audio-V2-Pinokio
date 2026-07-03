module.exports = {
  run: [{
    method: "fs.rm",
    params: {
      path: "env"
    }
  }, {
    method: "fs.rm",
    params: {
      path: "temp_higgs"
    }
  }, {
    method: "fs.rm",
    params: {
      path: "models"
    }
  }, {
    method: "fs.rm",
    params: {
      path: "voice_preset_cache"
    }
  }]
}
