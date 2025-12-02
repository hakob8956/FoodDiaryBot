import React, { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
  PieChart,
  Pie,
  Cell
} from 'recharts'
import api from '../api/client'

const COLORS = {
  calories: '#ff6b6b',
  target: '#4ecdc4',
  protein: '#45b7d1',
  carbs: '#96ceb4',
  fat: '#ffeaa7',
  movingAvg: '#a29bfe'
}

function Charts({ dailyTarget }) {
  const [activeChart, setActiveChart] = useState('calories')
  const [days, setDays] = useState(7)
  const [caloriesData, setCaloriesData] = useState(null)
  const [macrosData, setMacrosData] = useState(null)
  const [trendData, setTrendData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadChartData()
  }, [days])

  async function loadChartData() {
    try {
      setLoading(true)
      const [calories, macros, trend] = await Promise.all([
        api.getCaloriesChart(days),
        api.getMacrosChart(days),
        api.getTrendChart(Math.max(days, 14))
      ])
      setCaloriesData(calories)
      setMacrosData(macros)
      setTrendData(trend)
    } catch (err) {
      console.error('Failed to load charts:', err)
    } finally {
      setLoading(false)
    }
  }

  function formatDate(dateStr) {
    const date = new Date(dateStr)
    return `${date.getMonth() + 1}/${date.getDate()}`
  }

  function renderCaloriesChart() {
    if (!caloriesData) return null

    const data = caloriesData.data.map(d => ({
      ...d,
      date: formatDate(d.date)
    }))

    return (
      <div className="chart-container">
        <div className="chart-stats">
          <div className="stat">
            <span className="stat-label">Average</span>
            <span className="stat-value">{caloriesData.average} kcal</span>
          </div>
          <div className="stat">
            <span className="stat-label">Total</span>
            <span className="stat-value">{caloriesData.total} kcal</span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="date" stroke="#888" fontSize={12} />
            <YAxis stroke="#888" fontSize={12} />
            <Tooltip
              contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }}
              labelStyle={{ color: '#fff' }}
            />
            <Bar dataKey="calories" fill={COLORS.calories} radius={[4, 4, 0, 0]} />
            {dailyTarget && (
              <ReferenceLine y={dailyTarget} stroke={COLORS.target} strokeDasharray="5 5" />
            )}
          </BarChart>
        </ResponsiveContainer>
      </div>
    )
  }

  function renderMacrosChart() {
    if (!macrosData) return null

    // Calculate total for pie chart
    const totals = macrosData.totals
    const pieData = [
      { name: 'Protein', value: totals.protein, color: COLORS.protein },
      { name: 'Carbs', value: totals.carbs, color: COLORS.carbs },
      { name: 'Fat', value: totals.fat, color: COLORS.fat }
    ]

    const data = macrosData.data.map(d => ({
      ...d,
      date: formatDate(d.date)
    }))

    return (
      <div className="chart-container">
        <div className="chart-stats">
          <div className="stat">
            <span className="stat-label">Avg Protein</span>
            <span className="stat-value">{macrosData.averages.protein}g</span>
          </div>
          <div className="stat">
            <span className="stat-label">Avg Carbs</span>
            <span className="stat-value">{macrosData.averages.carbs}g</span>
          </div>
          <div className="stat">
            <span className="stat-label">Avg Fat</span>
            <span className="stat-value">{macrosData.averages.fat}g</span>
          </div>
        </div>

        <div className="macro-charts">
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={70}
                paddingAngle={5}
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>

          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="date" stroke="#888" fontSize={10} />
              <YAxis stroke="#888" fontSize={10} />
              <Tooltip
                contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }}
              />
              <Bar dataKey="protein" stackId="a" fill={COLORS.protein} />
              <Bar dataKey="carbs" stackId="a" fill={COLORS.carbs} />
              <Bar dataKey="fat" stackId="a" fill={COLORS.fat} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    )
  }

  function renderTrendChart() {
    if (!trendData) return null

    const data = trendData.data.map(d => ({
      ...d,
      date: formatDate(d.date)
    }))

    return (
      <div className="chart-container">
        <p className="chart-description">
          7-day moving average shows your calorie trend over time
        </p>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="date" stroke="#888" fontSize={10} />
            <YAxis stroke="#888" fontSize={12} />
            <Tooltip
              contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="calories"
              stroke={COLORS.calories}
              strokeWidth={2}
              dot={{ r: 3 }}
              name="Daily"
            />
            <Line
              type="monotone"
              dataKey="moving_avg"
              stroke={COLORS.movingAvg}
              strokeWidth={2}
              dot={false}
              name="7-day Avg"
            />
            {dailyTarget && (
              <ReferenceLine y={dailyTarget} stroke={COLORS.target} strokeDasharray="5 5" />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    )
  }

  return (
    <div className="charts">
      <div className="chart-tabs">
        <button
          className={activeChart === 'calories' ? 'active' : ''}
          onClick={() => setActiveChart('calories')}
        >
          Calories
        </button>
        <button
          className={activeChart === 'macros' ? 'active' : ''}
          onClick={() => setActiveChart('macros')}
        >
          Macros
        </button>
        <button
          className={activeChart === 'trend' ? 'active' : ''}
          onClick={() => setActiveChart('trend')}
        >
          Trend
        </button>
      </div>

      <div className="period-selector">
        <button className={days === 7 ? 'active' : ''} onClick={() => setDays(7)}>
          7 days
        </button>
        <button className={days === 14 ? 'active' : ''} onClick={() => setDays(14)}>
          14 days
        </button>
        <button className={days === 30 ? 'active' : ''} onClick={() => setDays(30)}>
          30 days
        </button>
      </div>

      {loading ? (
        <div className="chart-loading">Loading charts...</div>
      ) : (
        <>
          {activeChart === 'calories' && renderCaloriesChart()}
          {activeChart === 'macros' && renderMacrosChart()}
          {activeChart === 'trend' && renderTrendChart()}
        </>
      )}
    </div>
  )
}

export default Charts
