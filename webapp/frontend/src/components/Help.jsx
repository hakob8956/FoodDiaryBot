import React, { useState } from 'react'

const COMMANDS = [
  { command: '/start', description: 'Set up your profile' },
  { command: '/profile', description: 'View your stats and calorie target' },
  { command: '/setcalories', description: 'Override daily calorie target' },
  { command: '/setweight', description: 'Update your weight in kg' },
  { command: '/summarize', description: 'Get nutrition summary' },
  { command: '/delete', description: 'Delete a food entry' },
  { command: '/notifications', description: 'Configure daily reminders' },
  { command: '/rawlog', description: 'Export all logs as JSON' },
  { command: '/help', description: 'Show all commands' },
]

function Help() {
  const [copiedCommand, setCopiedCommand] = useState(null)

  async function handleCommandClick(command) {
    const tg = window.Telegram?.WebApp

    try {
      // Copy command to clipboard
      await navigator.clipboard.writeText(command)
      setCopiedCommand(command)

      // Show feedback
      if (tg) {
        tg.showAlert(`Copied ${command}\n\nClose the app and paste it in the chat!`)
      }

      // Reset copied state after 2 seconds
      setTimeout(() => setCopiedCommand(null), 2000)
    } catch (err) {
      // Fallback if clipboard fails
      if (tg) {
        tg.showAlert(`Type ${command} in the chat`)
      }
    }
  }

  return (
    <div className="help-view">
      <h2>Bot Commands</h2>
      <p className="help-intro">
        Tap a command to copy it:
      </p>
      <div className="command-list">
        {COMMANDS.map((cmd) => (
          <div
            key={cmd.command}
            className={`command-item clickable ${copiedCommand === cmd.command ? 'copied' : ''}`}
            onClick={() => handleCommandClick(cmd.command)}
          >
            <code className="command-name">{cmd.command}</code>
            <span className="command-desc">
              {copiedCommand === cmd.command ? 'Copied!' : cmd.description}
            </span>
          </div>
        ))}
      </div>
      <div className="help-tips">
        <h3>Quick Tips</h3>
        <ul>
          <li>Send a photo of your meal to log it</li>
          <li>Or just type what you ate (e.g., "2 eggs and toast")</li>
          <li>Photo + caption gives the most accurate results</li>
        </ul>
      </div>
    </div>
  )
}

export default Help
