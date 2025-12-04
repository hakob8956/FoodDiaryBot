import React, { useState, useEffect } from 'react'
import api from './api/client'
import Navigation from './components/Navigation'
import Dashboard from './components/Dashboard'
import Calendar from './components/Calendar'
import Charts from './components/Charts'
import DaySummary from './components/DaySummary'
import Settings from './components/Settings'

const GOAL_LABELS = {
  'lose': 'Lose Weight',
  'maintain': 'Maintain Weight',
  'gain': 'Gain Weight',
  'gain_muscles': 'Build Muscle',
}

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [profile, setProfile] = useState(null)
  const [selectedDay, setSelectedDay] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [calendarKey, setCalendarKey] = useState(0)
  const [showSettings, setShowSettings] = useState(false)
  const [dashboardKey, setDashboardKey] = useState(0)

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

  function handleSettingsSaved() {
    // Reload profile and dashboard after settings change
    loadProfile()
    setDashboardKey(k => k + 1)
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
        {activeTab === 'dashboard' && <Dashboard key={dashboardKey} />}
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
            <div className="profile-header">
              <h2>Profile</h2>
              <button className="edit-btn" onClick={() => setShowSettings(true)}>
                Edit
              </button>
            </div>
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
                <strong>{GOAL_LABELS[profile?.goal] || profile?.goal || 'Not set'}</strong>
              </div>
              <div className="profile-row">
                <span>Daily Target</span>
                <strong>{profile?.daily_calorie_target ? `${profile.daily_calorie_target} kcal` : 'Not set'}</strong>
              </div>
            </div>

            <h3 className="profile-section-title">Macro Targets</h3>
            <div className="profile-card">
              <div className="profile-row">
                <span>Protein</span>
                <strong>{profile?.protein_target ? `${profile.protein_target}g` : 'Auto'}</strong>
              </div>
              <div className="profile-row">
                <span>Carbs</span>
                <strong>{profile?.carbs_target ? `${profile.carbs_target}g` : 'Auto'}</strong>
              </div>
              <div className="profile-row">
                <span>Fat</span>
                <strong>{profile?.fat_target ? `${profile.fat_target}g` : 'Auto'}</strong>
              </div>
              {profile?.macro_override && (
                <div className="profile-row custom-indicator">
                  <span></span>
                  <strong className="custom-badge">Custom</strong>
                </div>
              )}
            </div>

            <h3 className="profile-section-title">Notifications</h3>
            <div className="profile-card">
              <div className="profile-row">
                <span>Enabled</span>
                <strong>{profile?.notifications_enabled ? 'On' : 'Off'}</strong>
              </div>
              <div className="profile-row">
                <span>Reminder Time</span>
                <strong>{profile?.reminder_hour}:00</strong>
              </div>
            </div>

            <h3 className="profile-section-title danger-section">Danger Zone</h3>
            <div className="profile-card danger-card">
              <p className="danger-text">
                Deleting your account will permanently remove all your data including food logs and settings.
              </p>
              <button
                className="delete-account-btn"
                onClick={async () => {
                  if (window.confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
                    if (window.confirm('This will delete ALL your data. Are you absolutely sure?')) {
                      try {
                        await api.deleteAccount()
                        alert('Account deleted successfully')
                        window.Telegram?.WebApp?.close()
                      } catch (err) {
                        alert('Failed to delete account: ' + err.message)
                      }
                    }
                  }
                }}
              >
                Delete Account
              </button>
            </div>
          </div>
        )}
      </main>

      {selectedDay && (
        <DaySummary
          date={selectedDay}
          onClose={closeDaySummary}
          onDataChanged={handleDataChanged}
        />
      )}

      {showSettings && (
        <Settings
          profile={profile}
          onClose={() => setShowSettings(false)}
          onSave={handleSettingsSaved}
        />
      )}

      <Navigation activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  )
}

export default App
