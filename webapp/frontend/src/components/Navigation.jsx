import React from 'react'

function Navigation({ activeTab, onTabChange }) {
  const tabs = [
    { id: 'calendar', label: 'Calendar', icon: '📅' },
    { id: 'charts', label: 'Charts', icon: '📊' },
    { id: 'profile', label: 'Profile', icon: '👤' },
  ]

  return (
    <nav className="navigation">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => onTabChange(tab.id)}
        >
          <span className="nav-icon">{tab.icon}</span>
          <span className="nav-label">{tab.label}</span>
        </button>
      ))}
    </nav>
  )
}

export default Navigation
