import React, { useState, useEffect } from 'react'
import api from '../api/client'

const GOALS = [
  { value: 'lose', label: 'Lose Weight' },
  { value: 'maintain', label: 'Maintain Weight' },
  { value: 'gain', label: 'Gain Weight' },
  { value: 'gain_muscles', label: 'Build Muscle' },
]

const CALORIES_PER_GRAM = {
  protein: 4,
  carbs: 4,
  fat: 9,
}

function Settings({ profile, onClose, onSave }) {
  // Profile info
  const [name, setName] = useState(profile?.first_name || '')
  const [weight, setWeight] = useState(profile?.weight || '')
  const [height, setHeight] = useState(profile?.height || '')
  const [age, setAge] = useState(profile?.age || '')
  // Goal and calories
  const [goal, setGoal] = useState(profile?.goal || 'maintain')
  const [calories, setCalories] = useState(profile?.daily_calorie_target || 2000)
  const [macroMode, setMacroMode] = useState('grams') // 'grams' or 'percent'
  const [protein, setProtein] = useState(0)
  const [carbs, setCarbs] = useState(0)
  const [fat, setFat] = useState(0)
  const [notificationsEnabled, setNotificationsEnabled] = useState(profile?.notifications_enabled ?? true)
  const [reminderHour, setReminderHour] = useState(profile?.reminder_hour ?? 20)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  // Initialize macros from profile or calculate defaults
  useEffect(() => {
    if (profile?.protein_target && profile?.carbs_target && profile?.fat_target) {
      setProtein(profile.protein_target)
      setCarbs(profile.carbs_target)
      setFat(profile.fat_target)
    } else {
      // Calculate defaults based on goal
      calculateDefaultMacros(goal, calories)
    }
  }, [profile])

  function calculateDefaultMacros(goalValue, calorieTarget) {
    let proteinPct, carbsPct, fatPct

    switch (goalValue) {
      case 'lose':
        proteinPct = 0.30
        carbsPct = 0.40
        fatPct = 0.30
        break
      case 'gain':
        proteinPct = 0.25
        carbsPct = 0.50
        fatPct = 0.25
        break
      case 'gain_muscles':
        proteinPct = 0.35
        carbsPct = 0.40
        fatPct = 0.25
        break
      default: // maintain
        proteinPct = 0.25
        carbsPct = 0.45
        fatPct = 0.30
    }

    setProtein(Math.round((calorieTarget * proteinPct) / CALORIES_PER_GRAM.protein))
    setCarbs(Math.round((calorieTarget * carbsPct) / CALORIES_PER_GRAM.carbs))
    setFat(Math.round((calorieTarget * fatPct) / CALORIES_PER_GRAM.fat))
  }

  function handleGoalChange(newGoal) {
    setGoal(newGoal)
    // Optionally recalculate macros when goal changes
    calculateDefaultMacros(newGoal, calories)
  }

  function handleCaloriesChange(newCalories) {
    const cal = parseInt(newCalories) || 0
    setCalories(cal)
    if (macroMode === 'percent') {
      // Recalculate grams from percentages
      const totalCurrent = protein * CALORIES_PER_GRAM.protein +
                          carbs * CALORIES_PER_GRAM.carbs +
                          fat * CALORIES_PER_GRAM.fat
      if (totalCurrent > 0) {
        const proteinPct = (protein * CALORIES_PER_GRAM.protein) / totalCurrent
        const carbsPct = (carbs * CALORIES_PER_GRAM.carbs) / totalCurrent
        const fatPct = (fat * CALORIES_PER_GRAM.fat) / totalCurrent
        setProtein(Math.round((cal * proteinPct) / CALORIES_PER_GRAM.protein))
        setCarbs(Math.round((cal * carbsPct) / CALORIES_PER_GRAM.carbs))
        setFat(Math.round((cal * fatPct) / CALORIES_PER_GRAM.fat))
      }
    }
  }

  function getPercentage(macroGrams, caloriesPerGram) {
    if (calories <= 0) return 0
    return Math.round((macroGrams * caloriesPerGram / calories) * 100)
  }

  function handlePercentChange(macro, percent) {
    const pct = Math.min(100, Math.max(0, parseInt(percent) || 0)) / 100
    const grams = Math.round((calories * pct) / CALORIES_PER_GRAM[macro])

    if (macro === 'protein') setProtein(grams)
    else if (macro === 'carbs') setCarbs(grams)
    else if (macro === 'fat') setFat(grams)
  }

  async function handleSave() {
    setSaving(true)
    setError(null)

    try {
      const updateData = {
        goal,
        daily_calorie_target: calories,
        protein_target: protein,
        carbs_target: carbs,
        fat_target: fat,
        notifications_enabled: notificationsEnabled,
        reminder_hour: reminderHour,
      }

      // Add profile fields if they have values
      if (name) updateData.first_name = name
      if (weight) updateData.weight = weight
      if (height) updateData.height = height
      if (age) updateData.age = age

      await api.updateProfile(updateData)
      onSave()
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleReset() {
    setSaving(true)
    setError(null)

    try {
      const result = await api.resetMacros()
      setProtein(result.protein_target)
      setCarbs(result.carbs_target)
      setFat(result.fat_target)
      onSave()
      onClose() // Close modal so profile refreshes and Custom badge hides
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const totalPercent = getPercentage(protein, CALORIES_PER_GRAM.protein) +
                       getPercentage(carbs, CALORIES_PER_GRAM.carbs) +
                       getPercentage(fat, CALORIES_PER_GRAM.fat)

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content settings-modal" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>
        <h2 className="modal-title">Profile Settings</h2>

        {error && <div className="settings-error">{error}</div>}

        {/* Profile Info */}
        <div className="settings-section">
          <h3>Profile</h3>
          <div className="profile-inputs">
            <div className="profile-input-row">
              <label>Name</label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="Your name"
              />
            </div>
            <div className="profile-input-row">
              <label>Weight</label>
              <div className="input-with-unit">
                <input
                  type="number"
                  value={weight}
                  onChange={e => setWeight(e.target.value ? parseFloat(e.target.value) : '')}
                  placeholder="80"
                  min="20"
                  max="300"
                />
                <span className="unit">kg</span>
              </div>
            </div>
            <div className="profile-input-row">
              <label>Height</label>
              <div className="input-with-unit">
                <input
                  type="number"
                  value={height}
                  onChange={e => setHeight(e.target.value ? parseFloat(e.target.value) : '')}
                  placeholder="175"
                  min="50"
                  max="250"
                />
                <span className="unit">cm</span>
              </div>
            </div>
            <div className="profile-input-row">
              <label>Age</label>
              <div className="input-with-unit">
                <input
                  type="number"
                  value={age}
                  onChange={e => setAge(e.target.value ? parseInt(e.target.value) : '')}
                  placeholder="30"
                  min="1"
                  max="150"
                />
                <span className="unit">years</span>
              </div>
            </div>
          </div>
        </div>

        {/* Goal Selection */}
        <div className="settings-section">
          <h3>Goal</h3>
          <div className="goal-options">
            {GOALS.map(g => (
              <label key={g.value} className={`goal-option ${goal === g.value ? 'selected' : ''}`}>
                <input
                  type="radio"
                  name="goal"
                  value={g.value}
                  checked={goal === g.value}
                  onChange={() => handleGoalChange(g.value)}
                />
                <span>{g.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Calories */}
        <div className="settings-section">
          <h3>Daily Calories</h3>
          <div className="input-with-unit">
            <input
              type="number"
              value={calories}
              onChange={e => handleCaloriesChange(e.target.value)}
              min="1000"
              max="10000"
            />
            <span className="unit">kcal</span>
          </div>
        </div>

        {/* Macros */}
        <div className="settings-section">
          <div className="macros-header">
            <h3>Macros</h3>
            <button
              className="reset-auto-link"
              onClick={handleReset}
              disabled={saving}
            >
              Reset to Auto
            </button>
            <div className="macro-mode-toggle">
              <button
                className={macroMode === 'grams' ? 'active' : ''}
                onClick={() => setMacroMode('grams')}
              >
                Grams
              </button>
              <button
                className={macroMode === 'percent' ? 'active' : ''}
                onClick={() => setMacroMode('percent')}
              >
                Percent
              </button>
            </div>
          </div>

          <div className="macro-inputs">
            <div className="macro-input-row">
              <label>Protein</label>
              {macroMode === 'grams' ? (
                <div className="input-with-unit">
                  <input
                    type="number"
                    value={protein}
                    onChange={e => setProtein(parseInt(e.target.value) || 0)}
                    min="0"
                  />
                  <span className="unit">g</span>
                </div>
              ) : (
                <div className="input-with-unit">
                  <input
                    type="number"
                    value={getPercentage(protein, CALORIES_PER_GRAM.protein)}
                    onChange={e => handlePercentChange('protein', e.target.value)}
                    min="0"
                    max="100"
                  />
                  <span className="unit">%</span>
                </div>
              )}
              <span className="macro-secondary">
                {macroMode === 'grams'
                  ? `(${getPercentage(protein, CALORIES_PER_GRAM.protein)}%)`
                  : `(${protein}g)`
                }
              </span>
            </div>

            <div className="macro-input-row">
              <label>Carbs</label>
              {macroMode === 'grams' ? (
                <div className="input-with-unit">
                  <input
                    type="number"
                    value={carbs}
                    onChange={e => setCarbs(parseInt(e.target.value) || 0)}
                    min="0"
                  />
                  <span className="unit">g</span>
                </div>
              ) : (
                <div className="input-with-unit">
                  <input
                    type="number"
                    value={getPercentage(carbs, CALORIES_PER_GRAM.carbs)}
                    onChange={e => handlePercentChange('carbs', e.target.value)}
                    min="0"
                    max="100"
                  />
                  <span className="unit">%</span>
                </div>
              )}
              <span className="macro-secondary">
                {macroMode === 'grams'
                  ? `(${getPercentage(carbs, CALORIES_PER_GRAM.carbs)}%)`
                  : `(${carbs}g)`
                }
              </span>
            </div>

            <div className="macro-input-row">
              <label>Fat</label>
              {macroMode === 'grams' ? (
                <div className="input-with-unit">
                  <input
                    type="number"
                    value={fat}
                    onChange={e => setFat(parseInt(e.target.value) || 0)}
                    min="0"
                  />
                  <span className="unit">g</span>
                </div>
              ) : (
                <div className="input-with-unit">
                  <input
                    type="number"
                    value={getPercentage(fat, CALORIES_PER_GRAM.fat)}
                    onChange={e => handlePercentChange('fat', e.target.value)}
                    min="0"
                    max="100"
                  />
                  <span className="unit">%</span>
                </div>
              )}
              <span className="macro-secondary">
                {macroMode === 'grams'
                  ? `(${getPercentage(fat, CALORIES_PER_GRAM.fat)}%)`
                  : `(${fat}g)`
                }
              </span>
            </div>

            {totalPercent !== 100 && (
              <div className="macro-warning">
                Total: {totalPercent}% (should be 100%)
              </div>
            )}
          </div>
        </div>

        {/* Notifications */}
        <div className="settings-section">
          <h3>Notifications</h3>
          <div className="notification-settings">
            <div className="toggle-row">
              <span>Daily Reminder</span>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={notificationsEnabled}
                  onChange={e => setNotificationsEnabled(e.target.checked)}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            {notificationsEnabled && (
              <div className="reminder-time-row">
                <span>Reminder Time</span>
                <select
                  value={reminderHour}
                  onChange={e => setReminderHour(parseInt(e.target.value))}
                  className="time-select"
                >
                  {Array.from({ length: 24 }, (_, i) => (
                    <option key={i} value={i}>
                      {i.toString().padStart(2, '0')}:00
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="settings-actions">
          <button
            className="btn-primary"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default Settings
