import React, { useState, useEffect } from 'react'
import api from '../api/client'

function DaySummary({ date, onClose, onDataChanged }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [deletingId, setDeletingId] = useState(null)

  useEffect(() => {
    loadDayData()
  }, [date])

  async function loadDayData() {
    try {
      setLoading(true)
      const dayData = await api.getDayDetail(date)
      setData(dayData)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(mealId) {
    if (!window.confirm('Delete this meal entry?')) {
      return
    }

    try {
      setDeletingId(mealId)
      await api.deleteEntry(mealId)
      // Refresh the day data
      await loadDayData()
      // Notify parent to refresh calendar
      if (onDataChanged) {
        onDataChanged()
      }
      // Close modal if no meals left
      if (data && data.meals.length <= 1) {
        onClose()
      }
    } catch (err) {
      alert('Failed to delete: ' + err.message)
    } finally {
      setDeletingId(null)
    }
  }

  function formatTime(isoString) {
    const date = new Date(isoString)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  function formatDate(dateStr) {
    const date = new Date(dateStr)
    return date.toLocaleDateString([], {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  function getProgressWidth() {
    if (!data || !data.daily_target) return 0
    return Math.min((data.total_calories / data.daily_target) * 100, 100)
  }

  function getProgressClass() {
    if (!data || !data.daily_target) return ''
    const ratio = data.total_calories / data.daily_target
    if (ratio <= 0.9) return 'under'
    if (ratio <= 1.1) return 'near'
    return 'over'
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>&times;</button>

        {loading ? (
          <div className="modal-loading">Loading...</div>
        ) : error ? (
          <div className="modal-error">{error}</div>
        ) : data ? (
          <>
            <h2 className="modal-title">{formatDate(date)}</h2>

            <div className="day-totals">
              <div className="total-calories">
                <span className="total-value">{data.total_calories}</span>
                <span className="total-label">kcal</span>
              </div>

              {data.daily_target && (
                <div className="progress-bar">
                  <div
                    className={`progress-fill ${getProgressClass()}`}
                    style={{ width: `${getProgressWidth()}%` }}
                  ></div>
                  <span className="progress-label">
                    {Math.round((data.total_calories / data.daily_target) * 100)}% of target
                  </span>
                </div>
              )}

              <div className="macro-totals">
                <div className="macro">
                  <span className="macro-value">{data.total_protein.toFixed(1)}g</span>
                  <span className="macro-label">Protein</span>
                </div>
                <div className="macro">
                  <span className="macro-value">{data.total_carbs.toFixed(1)}g</span>
                  <span className="macro-label">Carbs</span>
                </div>
                <div className="macro">
                  <span className="macro-value">{data.total_fat.toFixed(1)}g</span>
                  <span className="macro-label">Fat</span>
                </div>
              </div>
            </div>

            <div className="meals-list">
              <h3>Meals ({data.meals.length})</h3>
              {data.meals.length === 0 ? (
                <p className="no-meals">No meals logged this day</p>
              ) : (
                data.meals.map((meal) => (
                  <div key={meal.id} className="meal-item">
                    <div className="meal-header">
                      <span className="meal-time">{formatTime(meal.logged_at)}</span>
                      <div className="meal-header-right">
                        <span className="meal-calories">{meal.total_calories} kcal</span>
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
                      {meal.items.map(item => item.name).join(', ')}
                    </div>
                    <div className="meal-macros">
                      <span className="meal-macro protein">P: {meal.total_protein.toFixed(1)}g</span>
                      <span className="meal-macro carbs">C: {meal.total_carbs.toFixed(1)}g</span>
                      <span className="meal-macro fat">F: {meal.total_fat.toFixed(1)}g</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}

export default DaySummary
