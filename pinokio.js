const path = require('path')

module.exports = {
  version: "1.0.0",
  title: "Higgs Audio V2 Enhanced",
  description: "Advanced text-to-speech with voice cloning, multi-speaker support, and background music generation using Higgs Audio V2",
  icon: "icon.png",
  menu: async (kernel, info) => {
    let installed = info.exists("app/env")
    let running = {
      install: info.running("install.js"),
      start: info.running("start.js"),
      update: info.running("update.js"),
      reset: info.running("reset.js")
    }
    
    // Show different menus based on state
    if (running.install) {
      return [{
        default: true,
        icon: "fa-solid fa-plug",
        text: "Installing Higgs Audio V2...",
        href: "install.js",
      }]
    } else if (installed) {
      if (running.start) {
        let local = info.local("start.js")
        if (local && local.url) {
          return [{
            default: true,
            icon: "fa-solid fa-microphone",
            text: "Open Higgs Audio Interface",
            href: local.url,
          }, {
            icon: 'fa-solid fa-terminal',
            text: "View Terminal",
            href: "start.js",
          }, {
            icon: "fa-solid fa-stop",
            text: "Stop Application",
            href: "start.js",
            params: { action: "stop" }
          }]
        } else {
          return [{
            default: true,
            icon: "fa-solid fa-spinner fa-spin",
            text: "Starting...",
            href: "start.js",
          }]
        }
      } else {
        // Main menu when installed but not running
        return [{
          default: true,
          icon: "fa-solid fa-play",
          text: "Start Higgs Audio V2",
          href: "start.js"
        }, {
          icon: "fa-solid fa-sync",
          text: "Update",
          href: "update.js",
        }, {
          icon: "fa-solid fa-download",
          text: "Reinstall",
          href: "install.js",
        }, {
          icon: "fa-solid fa-trash",
          text: "Reset",
          href: "reset.js",
        }]
      }
    } else {
      // Not installed - show install option
      return [{
        default: true,
        icon: "fa-solid fa-download",
        text: "Install Higgs Audio V2",
        href: "install.js",
      }]
    }
  }
}