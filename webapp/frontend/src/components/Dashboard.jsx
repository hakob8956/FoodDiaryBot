import React, { useState, useEffect } from 'react'
import api from '../api/client'

function CircularProgress({ eaten, target, remaining }) {
  const percentage = target > 0 ? Math.min((eaten / target) * 100, 100) : 0
  const radius = 70
  const strokeWidth = 8
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (percentage / 100) * circumference

  return (
    <div className="circular-progress">
      <svg width="180" height="180" viewBox="0 0 180 180">
        {/* Background circle */}
        <circle
          cx="90"
          cy="90"
          r={radius}
          fill="none"
          stroke="var(--bg-card)"
          strokeWidth={strokeWidth}
        />
        {/* Progress circle */}
        <circle
          cx="90"
          cy="90"
          r={radius}
          fill="none"
          stroke="var(--success)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          transform="rotate(-90 90 90)"
          style={{ transition: 'stroke-dashoffset 0.5s ease' }}
        />
      </svg>
      <div className="circular-progress-content">
        <span className="remaining-value">{remaining}</span>
        <span className="remaining-label">Remaining</span>
      </div>
    </div>
  )
}

function MacroProgressBar({ label, current, target, color }) {
  const percentage = target > 0 ? Math.min((current / target) * 100, 100) : 0

  return (
    <div className="macro-progress-item">
      <div className="macro-progress-header">
        <span className="macro-progress-label">{label}</span>
        <div className="macro-progress-dot" style={{ backgroundColor: color }}></div>
      </div>
      <div className="macro-progress-bar-container">
        <div
          className="macro-progress-bar-fill"
          style={{ width: `${percentage}%`, backgroundColor: color }}
        ></div>
      </div>
      <span className="macro-progress-values">
        {Math.round(current)} / {target} g
      </span>
    </div>
  )
}

function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [deletingId, setDeletingId] = useState(null)

  useEffect(() => {
    loadDashboard()
  }, [])

  async function loadDashboard() {
    try {
      setLoading(true)
      const result = await api.getTodayDashboard()
      setData(result)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(mealId) {
    if (!window.confirm('Delete this meal?')) return

    try {
      setDeletingId(mealId)
      await api.deleteEntry(mealId)
      await loadDashboard()
    } catch (err) {
      alert('Failed to delete: ' + err.message)
    } finally {
      setDeletingId(null)
    }
  }

  if (loading) {
    return (
      <div className="dashboard">
        <div className="dashboard-loading">Loading...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="dashboard">
        <div className="dashboard-error">
          <p>{error}</p>
          <button onClick={loadDashboard}>Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <div className="dashboard-card">
        {/* Calories section */}
        <div className="calories-section">
          <div className="calories-side">
            <span className="calories-value">{data.calories_eaten}</span>
            <span className="calories-label">Eaten</span>
          </div>

          <CircularProgress
            eaten={data.calories_eaten}
            target={data.calories_target}
            remaining={data.calories_remaining}
          />

          <div className="calories-side">
            <span className="calories-value">{data.calories_target}</span>
            <span className="calories-label">Target</span>
          </div>
        </div>

        {/* Macros section */}
        <div className="macros-section">
          <MacroProgressBar
            label="Carbs"
            current={data.carbs.current}
            target={data.carbs.target}
            color="var(--carbs)"
          />
          <MacroProgressBar
            label="Protein"
            current={data.protein.current}
            target={data.protein.target}
            color="var(--protein)"
          />
          <MacroProgressBar
            label="Fat"
            current={data.fat.current}
            target={data.fat.target}
            color="var(--fat)"
          />
        </div>
      </div>

      {/* Meals List */}
      {data.meals && data.meals.length > 0 && (
        <div className="meals-list">
          <h3>Today's Meals</h3>
          {data.meals.map(meal => (
            <div key={meal.id} className="meal-item">
              <div className="meal-header">
                <span className="meal-time">{meal.time}</span>
                <div className="meal-header-right">
                  <span className="meal-calories">{meal.calories} kcal</span>
                  <button
                    className="delete-btn"
                    onClick={() => handleDelete(meal.id)}
                    disabled={deletingId === meal.id}
                    title="Delete"
                  >
                    {deletingId === meal.id ? '...' : '×'}
                  </button>
                </div>
              </div>
              <div className="meal-foods">
                {meal.foods.join(', ')}
              </div>
              <div className="meal-macros">
                <span className="meal-macro protein">P: {meal.protein}g</span>
                <span className="meal-macro carbs">C: {meal.carbs}g</span>
                <span className="meal-macro fat">F: {meal.fat}g</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {data.meal_count === 0 && (
        <div className="dashboard-info">
          <span>No meals logged today</span>
        </div>
      )}
    </div>
  )
}

export default Dashboard
