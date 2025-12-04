/**
 * API client for FoodGPT Mini App
 */

const API_BASE = '/api'

/**
 * Get Telegram WebApp init data for authentication
 */
function getInitData() {
  return window.Telegram?.WebApp?.initData || ''
}

/**
 * Make an authenticated API request
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`
  const initData = getInitData()

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-Telegram-Init-Data': initData,
      ...options.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || 'Request failed')
  }

  return response.json()
}

/**
 * API methods
 */
export const api = {
  // Auth
  getMe: () => apiRequest('/auth/me'),

  // User
  getProfile: () => apiRequest('/user/profile'),
  updateProfile: (data) => apiRequest('/user/profile', {
    method: 'PUT',
    body: JSON.stringify(data)
  }),
  resetMacros: () => apiRequest('/user/profile/reset-macros', {
    method: 'POST'
  }),
  deleteAccount: () => apiRequest('/user/account', {
    method: 'DELETE'
  }),

  // Dashboard
  getTodayDashboard: () => apiRequest('/dashboard/today'),

  // Calendar
  getCalendar: (year, month) => {
    const params = new URLSearchParams()
    if (year) params.append('year', year)
    if (month) params.append('month', month)
    const query = params.toString() ? `?${params}` : ''
    return apiRequest(`/calendar${query}`)
  },

  getDayDetail: (date) => apiRequest(`/calendar/${date}`),
  deleteEntry: (id) => apiRequest(`/calendar/entry/${id}`, { method: 'DELETE' }),

  // Charts
  getCaloriesChart: (days = 7) => apiRequest(`/charts/calories?days=${days}`),
  getMacrosChart: (days = 7) => apiRequest(`/charts/macros?days=${days}`),
  getTrendChart: (days = 30) => apiRequest(`/charts/trend?days=${days}`),

  // Summary
  getSummary: (days = 7) => apiRequest(`/summary?days=${days}`),
}

export default api
