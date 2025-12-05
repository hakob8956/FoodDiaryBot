import React, { useState, useEffect } from 'react'
import api from '../api/client'
import './Pet.css'

function Pet() {
  const [pet, setPet] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [isRenaming, setIsRenaming] = useState(false)
  const [newName, setNewName] = useState('')
  const [showInfo, setShowInfo] = useState(false)

  useEffect(() => {
    loadPet()
  }, [])

  async function loadPet() {
    try {
      setLoading(true)
      const data = await api.getPet()
      setPet(data)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleRename() {
    if (!newName.trim() || newName.length > 20) return

    try {
      const result = await api.renamePet(newName.trim())
      if (result.success) {
        setPet(prev => ({ ...prev, name: result.name }))
        setIsRenaming(false)
        setNewName('')
      }
    } catch (err) {
      alert('Failed to rename pet: ' + err.message)
    }
  }

  if (loading) {
    return (
      <div className="pet-container loading">
        <div className="spinner"></div>
        <p>Loading your pet...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="pet-container error">
        <p>Error: {error}</p>
        <button onClick={loadPet}>Retry</button>
      </div>
    )
  }

  if (!pet) return null

  const moodEmoji = {
    stuffed: '🫃',
    ecstatic: '🌟',
    happy: '😊',
    hungry: '😕',
    starving: '😢'
  }

  // Calculate progress bar width (cap at 100% for display, but show real percentage)
  const progressPercent = Math.min(pet.calories_percent, 100)
  const isOvereating = pet.calories_percent > 120

  return (
    <div className="pet-container">
      {/* Info Modal */}
      {showInfo && (
        <div className="info-modal-overlay" onClick={() => setShowInfo(false)}>
          <div className="info-modal" onClick={e => e.stopPropagation()}>
            <button className="close-btn" onClick={() => setShowInfo(false)}>×</button>
            <h3>How Your Pet Works</h3>

            <div className="info-section">
              <h4>🎭 Moods</h4>
              <p>Your pet's mood is based on your daily calorie progress:</p>
              <ul>
                <li>😢 <strong>Starving</strong> — 0% (nothing logged)</li>
                <li>😕 <strong>Hungry</strong> — 1-49%</li>
                <li>😊 <strong>Happy</strong> — 50-99%</li>
                <li>🌟 <strong>Ecstatic</strong> — 100-120%</li>
                <li>🫃 <strong>Stuffed</strong> — 121%+ (overeating)</li>
              </ul>
            </div>

            <div className="info-section">
              <h4>📈 Evolution</h4>
              <p>Your pet evolves as you log more meals:</p>
              <ul>
                <li>🥚 <strong>Egg</strong> — 0-1 meals</li>
                <li>🐣 <strong>Baby</strong> — 2-50 meals</li>
                <li>🐥 <strong>Teen</strong> — 51-150 meals</li>
                <li>🐔 <strong>Adult</strong> — 151-500 meals</li>
                <li>👑 <strong>Elder</strong> — 501+ meals</li>
              </ul>
            </div>

            <div className="info-section">
              <h4>🔥 Streaks</h4>
              <p>Log at least one meal every day to keep your streak going!</p>
            </div>
          </div>
        </div>
      )}

      {/* Pet Display */}
      <div className="pet-display">
        <button className="info-btn" onClick={() => setShowInfo(true)}>ℹ️</button>
        <div className="pet-image">
          <img
            src={pet.image_url}
            alt={`${pet.name} the ${pet.level_name} pet`}
            onError={(e) => {
              // Fallback to showing ASCII art if image fails
              e.target.style.display = 'none'
              e.target.nextSibling.style.display = 'block'
            }}
          />
          <pre className="pet-ascii-fallback" style={{ display: 'none' }}>{pet.ascii_art}</pre>
        </div>

        <div className="pet-name-row">
          {isRenaming ? (
            <div className="rename-form">
              <input
                type="text"
                value={newName}
                onChange={e => setNewName(e.target.value)}
                placeholder="New name..."
                maxLength={20}
                autoFocus
              />
              <button onClick={handleRename}>Save</button>
              <button onClick={() => setIsRenaming(false)}>Cancel</button>
            </div>
          ) : (
            <h2 onClick={() => { setNewName(pet.name); setIsRenaming(true); }}>
              {pet.name} <span className="edit-hint">tap to rename</span>
            </h2>
          )}
        </div>

        <div className="pet-status">
          <span className="mood">
            {moodEmoji[pet.mood] || '😊'} {pet.mood_name}
          </span>
          <span className="level">
            Level: {pet.level_name}
          </span>
        </div>

        {/* Calorie Progress Bar */}
        <div className="calorie-progress">
          <div className="progress-header">
            <span>Daily Progress</span>
            <span className={isOvereating ? 'overeating' : ''}>
              {pet.calories_today} / {pet.calories_target} kcal ({pet.calories_percent}%)
              {isOvereating && ' ⚠️'}
            </span>
          </div>
          <div className="progress-bar">
            <div
              className={`progress-fill ${isOvereating ? 'overeating' : ''}`}
              style={{ width: `${progressPercent}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="pet-stats">
        <div className="stat">
          <span className="stat-value">{pet.total_meals}</span>
          <span className="stat-label">Meals Logged</span>
        </div>
        <div className="stat">
          <span className="stat-value">{pet.current_streak}🔥</span>
          <span className="stat-label">Current Streak</span>
        </div>
        <div className="stat">
          <span className="stat-value">{pet.best_streak}</span>
          <span className="stat-label">Best Streak</span>
        </div>
      </div>

      {/* Achievements */}
      <div className="achievements-section">
        <h3>Achievements ({pet.unlocked_count}/{pet.total_achievements})</h3>
        <div className="achievements-grid">
          {pet.achievements.map(achievement => (
            <div
              key={achievement.id}
              className={`achievement ${achievement.unlocked ? 'unlocked' : 'locked'}`}
              title={achievement.description}
            >
              <span className="achievement-emoji">
                {achievement.unlocked ? achievement.emoji : '🔒'}
              </span>
              <span className="achievement-name">{achievement.name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Pet
