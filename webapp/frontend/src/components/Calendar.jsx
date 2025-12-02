import React, { useState, useEffect } from 'react'
import api from '../api/client'

const DAYS_OF_WEEK = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
]

function Calendar({ onDaySelect, dailyTarget }) {
  const today = new Date()
  const [year, setYear] = useState(today.getFullYear())
  const [month, setMonth] = useState(today.getMonth() + 1)
  const [calendarData, setCalendarData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadCalendarData()
  }, [year, month])

  async function loadCalendarData() {
    try {
      setLoading(true)
      const data = await api.getCalendar(year, month)
      setCalendarData(data)
    } catch (err) {
      console.error('Failed to load calendar:', err)
    } finally {
      setLoading(false)
    }
  }

  function goToPrevMonth() {
    if (month === 1) {
      setYear(year - 1)
      setMonth(12)
    } else {
      setMonth(month - 1)
    }
  }

  function goToNextMonth() {
    if (month === 12) {
      setYear(year + 1)
      setMonth(1)
    } else {
      setMonth(month + 1)
    }
  }

  function getDaysInMonth(y, m) {
    return new Date(y, m, 0).getDate()
  }

  function getFirstDayOfMonth(y, m) {
    return new Date(y, m - 1, 1).getDay()
  }

  function getDayData(day) {
    if (!calendarData) return null
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    return calendarData.days.find(d => d.date === dateStr)
  }

  function getStatusClass(dayData) {
    if (!dayData) return ''
    return `status-${dayData.status}`
  }

  function renderCalendarGrid() {
    const daysInMonth = getDaysInMonth(year, month)
    const firstDay = getFirstDayOfMonth(year, month)
    const cells = []

    // Empty cells for days before the first of the month
    for (let i = 0; i < firstDay; i++) {
      cells.push(<div key={`empty-${i}`} className="calendar-cell empty"></div>)
    }

    // Day cells
    for (let day = 1; day <= daysInMonth; day++) {
      const dayData = getDayData(day)
      const isToday =
        year === today.getFullYear() &&
        month === today.getMonth() + 1 &&
        day === today.getDate()

      const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`

      cells.push(
        <div
          key={day}
          className={`calendar-cell ${isToday ? 'today' : ''} ${dayData ? 'has-data' : ''} ${getStatusClass(dayData)}`}
          onClick={() => dayData && onDaySelect(dateStr)}
        >
          <span className="day-number">{day}</span>
          {dayData && (
            <div className="day-indicator">
              <span className="calories">{dayData.total_calories}</span>
            </div>
          )}
        </div>
      )
    }

    return cells
  }

  return (
    <div className="calendar">
      <div className="calendar-header">
        <button className="nav-btn" onClick={goToPrevMonth}>&lt;</button>
        <h2>{MONTHS[month - 1]} {year}</h2>
        <button className="nav-btn" onClick={goToNextMonth}>&gt;</button>
      </div>

      <div className="calendar-weekdays">
        {DAYS_OF_WEEK.map(day => (
          <div key={day} className="weekday">{day}</div>
        ))}
      </div>

      <div className="calendar-grid">
        {loading ? (
          <div className="calendar-loading">Loading...</div>
        ) : (
          renderCalendarGrid()
        )}
      </div>

      <div className="calendar-legend">
        <div className="legend-item">
          <span className="legend-dot status-under"></span>
          <span>Under target</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot status-near"></span>
          <span>Near target</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot status-over"></span>
          <span>Over target</span>
        </div>
      </div>
    </div>
  )
}

export default Calendar
