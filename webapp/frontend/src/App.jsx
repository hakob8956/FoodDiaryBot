import React, { useState, useEffect } from 'react'
import api from './api/client'
import Navigation from './components/Navigation'
import Calendar from './components/Calendar'
import Charts from './components/Charts'
import DaySummary from './components/DaySummary'
import Help from './components/Help'

function App() {
  const [activeTab, setActiveTab] = useState('calendar')
  const [profile, setProfile] = useState(null)
  const [selectedDay, setSelectedDay] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [calendarKey, setCalendarKey] = useState(0)

  useEffect(() => {
    loadProfile()
  }, [])

  async function loadProfile() {
    try {
      setLoading(true)
      const data = await api.getProfile()
      setProfile(data)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function handleDaySelect(date) {
    setSelectedDay(date)
  }

  function closeDaySummary() {
    setSelectedDay(null)
  }

  function handleDataChanged() {
    // Increment key to force Calendar to re-fetch data
    setCalendarKey(k => k + 1)
  }

  if (loading) {
    return (
      <div className="app loading">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="app error">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={loadProfile}>Retry</button>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="header">
        <h1>FoodGPT</h1>
        {profile && (
          <div className="user-info">
            <span className="target">
              Target: {profile.daily_calorie_target || '---'} kcal
            </span>
          </div>
        )}
      </header>

      <main className="main">
        {activeTab === 'calendar' && (
          <Calendar
            key={calendarKey}
            onDaySelect={handleDaySelect}
            dailyTarget={profile?.daily_calorie_target}
          />
        )}
        {activeTab === 'charts' && (
          <Charts dailyTarget={profile?.daily_calorie_target} />
        )}
        {activeTab === 'profile' && (
          <div className="profile-view">
            <h2>Profile</h2>
            <div className="profile-card">
              <div className="profile-row">
                <span>Name</span>
                <strong>{profile?.first_name || 'Not set'}</strong>
              </div>
              <div className="profile-row">
                <span>Weight</span>
                <strong>{profile?.weight ? `${profile.weight} kg` : 'Not set'}</strong>
              </div>
              <div className="profile-row">
                <span>Height</span>
                <strong>{profile?.height ? `${profile.height} cm` : 'Not set'}</strong>
              </div>
              <div className="profile-row">
                <span>Age</span>
                <strong>{profile?.age || 'Not set'}</strong>
              </div>
              <div className="profile-row">
                <span>Goal</span>
                <strong>{profile?.goal || 'Not set'}</strong>
              </div>
              <div className="profile-row">
                <span>Daily Target</span>
                <strong>{profile?.daily_calorie_target ? `${profile.daily_calorie_target} kcal` : 'Not set'}</strong>
              </div>
              <div className="profile-row">
                <span>Notifications</span>
                <strong>{profile?.notifications_enabled ? 'On' : 'Off'}</strong>
              </div>
              <div className="profile-row">
                <span>Reminder Time</span>
                <strong>{profile?.reminder_hour}:00</strong>
              </div>
            </div>
            <p className="profile-hint">
              Use the bot commands to update your profile
            </p>
          </div>
        )}
        {activeTab === 'help' && <Help />}
      </main>

      {selectedDay && (
        <DaySummary
          date={selectedDay}
          onClose={closeDaySummary}
          onDataChanged={handleDataChanged}
        />
      )}

      <Navigation activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  )
}

export default App
