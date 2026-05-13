import { useState, useEffect, useCallback } from 'react'
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts'
import { getStats } from '../api.js'

const PERIODS = [
  { id: 'today', label: 'Today' },
  { id: 'week',  label: 'Week' },
  { id: 'month', label: 'Month' },
]

// Цвета для категорий — достаточно контрастны на светлом и тёмном фоне
const COLORS = [
  '#F59E0B', '#3B82F6', '#EC4899', '#22C55E',
  '#8B5CF6', '#F97316', '#06B6D4', '#EF4444',
  '#14B8A6', '#6366F1', '#94A3B8',
]

// Кастомный tooltip для Recharts — стилизован под TMA
const CustomTooltip = ({ active, payload, currency }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--tg-theme-bg-color)',
      border: '1px solid var(--tg-theme-secondary-bg-color)',
      borderRadius: 8, padding: '8px 12px',
      fontSize: 13,
    }}>
      <p style={{ fontWeight: 500 }}>{payload[0].name || payload[0].payload?.date}</p>
      <p style={{ color: 'var(--accent)', fontFamily: 'var(--font-mono)' }}>
        {currency} {Number(payload[0].value).toFixed(2)}
      </p>
    </div>
  )
}

export default function Analytics({ user }) {
  const [period,  setPeriod]  = useState('week')
  const [stats,   setStats]   = useState(null)
  const [loading, setLoading] = useState(true)

  const cur = user?.currency ?? 'EUR'

  const load = useCallback(() => {
    setLoading(true)
    getStats(period)
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [period])

  useEffect(() => { load() }, [load])

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Analytics</h1>
      </div>

      <div className="period-tabs">
        {PERIODS.map((p) => (
          <button
            key={p.id}
            className={`period-tab ${period === p.id ? 'active' : ''}`}
            onClick={() => setPeriod(p.id)}
          >
            {p.label}
          </button>
        ))}
      </div>

      {loading || !stats ? (
        <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 40 }}>
          <div className="spinner" />
        </div>
      ) : stats.by_category.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">📊</div>
          <p>No data for this period</p>
        </div>
      ) : (
        <>
          {/* Суммарная карточка */}
          <div className="card" style={{ display: 'flex', gap: 12 }}>
            {[
              { label: 'Today',  value: stats.today },
              { label: 'Week',   value: stats.week },
              { label: 'Month',  value: stats.month },
            ].map(({ label, value }) => (
              <div key={label} style={{ flex: 1, textAlign: 'center' }}>
                <p style={{ fontSize: 11, color: 'var(--tg-theme-hint-color)', textTransform: 'uppercase', letterSpacing: '0.4px' }}>
                  {label}
                </p>
                <p className="amount" style={{ fontSize: 16, fontWeight: 500, marginTop: 2 }}>
                  {cur} {value.toFixed(0)}
                </p>
              </div>
            ))}
          </div>

          {/* Pie chart — по категориям */}
          <p style={{
            fontSize: 13, fontWeight: 600,
            color: 'var(--tg-theme-hint-color)',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            marginBottom: 12,
          }}>
            By category
          </p>
          <div className="card">
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={stats.by_category}
                  dataKey="total"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={3}
                >
                  {stats.by_category.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip currency={cur} />} />
              </PieChart>
            </ResponsiveContainer>

            {/* Легенда */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 8 }}>
              {stats.by_category.map((item, i) => {
                const total = stats.by_category.reduce((s, x) => s + x.total, 0)
                const pct = ((item.total / total) * 100).toFixed(0)
                return (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ width: 10, height: 10, borderRadius: 3, background: COLORS[i % COLORS.length], flexShrink: 0 }} />
                    <span style={{ flex: 1, fontSize: 14 }}>{item.category}</span>
                    <span className="amount" style={{ fontSize: 14, color: 'var(--tg-theme-hint-color)' }}>{pct}%</span>
                    <span className="amount" style={{ fontSize: 14, fontWeight: 500 }}>{cur} {item.total.toFixed(2)}</span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Bar chart — последние 7 дней */}
          <p style={{
            fontSize: 13, fontWeight: 600,
            color: 'var(--tg-theme-hint-color)',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            marginBottom: 12,
            marginTop: 4,
          }}>
            Last 7 days
          </p>
          <div className="card">
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={stats.daily_last_7} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--tg-theme-bg-color)" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11, fill: 'var(--tg-theme-hint-color)', fontFamily: 'var(--font-body)' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: 'var(--tg-theme-hint-color)', fontFamily: 'var(--font-mono)' }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip content={<CustomTooltip currency={cur} />} cursor={{ fill: 'var(--accent-light)' }} />
                <Bar dataKey="total" name="Spent" fill="var(--accent)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  )
}
