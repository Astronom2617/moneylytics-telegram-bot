import { useState, useEffect, useCallback } from 'react'
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts'
import { getStats } from '../api.js'
import { useTranslation, translateCategory, localeFor } from '../i18n.js'
import { currencySymbol } from '../currency.js'

const PERIOD_IDS = ['today', 'week', 'month']

// Picked to stay readable on both light and dark Telegram themes
const COLORS = [
  '#F59E0B', '#3B82F6', '#EC4899', '#22C55E',
  '#8B5CF6', '#F97316', '#06B6D4', '#EF4444',
  '#14B8A6', '#6366F1', '#94A3B8',
]

const CustomTooltip = ({ active, payload, currency, language, translateName }) => {
  if (!active || !payload?.length) return null
  const rawName = payload[0].payload?.label || payload[0].name || payload[0].payload?.date
  const name = translateName ? translateName(rawName) : rawName
  return (
    <div style={{
      background: 'var(--tg-theme-bg-color)',
      border: '1px solid var(--tg-theme-secondary-bg-color)',
      borderRadius: 8, padding: '8px 12px',
      fontSize: 13,
    }}>
      <p style={{ fontWeight: 500 }}>{name}</p>
      <p style={{ color: 'var(--accent)', fontFamily: 'var(--font-mono)' }}>
        {currency} {Number(payload[0].value).toFixed(2)}
      </p>
    </div>
  )
}

export default function Analytics({ user }) {
  const [period,   setPeriod]   = useState('week')
  const [currency, setCurrency] = useState(null)
  const [stats,    setStats]    = useState(null)
  const [loading,  setLoading]  = useState(true)

  const cur = user?.currency ?? 'EUR'
  const lang = user?.language ?? 'en'
  const locale = localeFor(lang)
  const t = useTranslation(lang)

  const available = stats?.currencies ?? []
  const hasSwitcher = available.length > 1
  // When several currencies exist each one gets its own independent analytics;
  // with a single currency nothing changes and no switcher is shown.
  const activeCur = hasSwitcher ? (currency ?? (available.includes(cur) ? cur : available[0])) : cur

  const formatDay = (isoDate) => {
    try {
      return new Date(isoDate + 'T00:00:00').toLocaleDateString(locale, { weekday: 'short' })
    } catch { return isoDate }
  }

  const dailyData = (stats?.daily_last_7 || []).map((d) => ({ ...d, label: formatDay(d.date) }))
  const categoryTotal = (stats?.by_category || []).reduce((s, x) => s + x.total, 0)

  const load = useCallback(() => {
    setLoading(true)
    getStats(period, currency || undefined)
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [period, currency])

  useEffect(() => { load() }, [load])

  // Each period (Today / Week / Month) has its own set of currencies. Clear
  // the active selection whenever the period tab changes so the next fetch
  // is unfiltered and the switcher re-derives from THAT period's expenses —
  // otherwise a currency picked under one period leaks into another, hiding
  // the chips (or filtering to a currency with no data) for Today and Week.
  useEffect(() => { setCurrency(null) }, [period])

  // Once we know which currencies exist, lock onto a sensible default (the
  // user's own currency if present) and re-fetch filtered. Also recovers if
  // the chosen currency has no data in a newly selected period.
  useEffect(() => {
    if (!stats) return
    const list = stats.currencies ?? []
    if (list.length <= 1) {
      if (currency !== null) setCurrency(null)
      return
    }
    if (currency === null || !list.includes(currency)) {
      setCurrency(list.includes(cur) ? cur : list[0])
    }
  }, [stats, currency, cur])

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('page.analytics')}</h1>
      </div>

      <div className="period-tabs">
        {PERIOD_IDS.map((id) => (
          <button
            key={id}
            className={`period-tab ${period === id ? 'active' : ''}`}
            onClick={() => setPeriod(id)}
          >
            {t(`period.${id}`)}
          </button>
        ))}
      </div>

      {hasSwitcher && (
        <div className="chips currency-switch">
          {available.map((c) => (
            <button
              key={c}
              type="button"
              className={`chip ${activeCur === c ? 'active' : ''}`}
              onClick={() => setCurrency(c)}
            >
              {currencySymbol(c)} {c}
            </button>
          ))}
        </div>
      )}

      {loading || !stats ? (
        <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 40 }}>
          <div className="spinner" />
        </div>
      ) : stats.by_category.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">📊</div>
          <p>{t('analytics.noData')}</p>
        </div>
      ) : (
        <>
          <div className="card" style={{ display: 'flex', gap: 12 }}>
            {[
              { label: t('period.today'),  value: stats.today },
              { label: t('period.week'),   value: stats.week },
              { label: t('period.month'),  value: stats.month },
            ].map(({ label, value }) => {
              const entries = hasSwitcher
                ? [[activeCur, (value || {})[activeCur] || 0]]
                : Object.entries(value || {})
              return (
                <div key={label} style={{ flex: 1, textAlign: 'center', minWidth: 0 }}>
                  <p style={{ fontSize: 11, color: 'var(--tg-theme-hint-color)', textTransform: 'uppercase', letterSpacing: '0.4px' }}>
                    {label}
                  </p>
                  {entries.length === 0 ? (
                    <p className="amount" style={{ fontSize: 16, fontWeight: 500, marginTop: 2 }}>
                      {activeCur} 0
                    </p>
                  ) : entries.map(([c, v]) => (
                    <p key={c} className="amount" style={{ fontSize: 14, fontWeight: 500, marginTop: 2, lineHeight: 1.25 }}>
                      {c} {v.toFixed(0)}
                    </p>
                  ))}
                </div>
              )
            })}
          </div>

          <p style={{
            fontSize: 11,
            color: 'var(--tg-theme-hint-color)',
            fontStyle: 'italic',
            margin: '-4px 4px 12px',
          }}>
            ℹ️ {hasSwitcher ? `${activeCur} · ${t('analytics.currencyNote')}` : t('analytics.totalsNote')}
          </p>

          <p style={{
            fontSize: 13, fontWeight: 600,
            color: 'var(--tg-theme-hint-color)',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            marginBottom: 12,
          }}>
            {t('analytics.byCategory')}
          </p>
          <div className="card">
            <div style={{ position: 'relative' }}>
              <ResponsiveContainer width="100%" height={230}>
                <PieChart>
                  <Pie
                    data={stats.by_category}
                    dataKey="total"
                    nameKey="category"
                    cx="50%"
                    cy="50%"
                    innerRadius={64}
                    outerRadius={92}
                    paddingAngle={2}
                    cornerRadius={6}
                    stroke="var(--tg-theme-secondary-bg-color)"
                    strokeWidth={3}
                    animationDuration={600}
                  >
                    {stats.by_category.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip currency={activeCur} translateName={(n) => translateCategory(n, lang)} />} />
                </PieChart>
              </ResponsiveContainer>
              <div style={{
                position: 'absolute', inset: 0,
                display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center',
                pointerEvents: 'none',
              }}>
                <span style={{
                  fontSize: 11, color: 'var(--tg-theme-hint-color)',
                  textTransform: 'uppercase', letterSpacing: '0.5px',
                }}>
                  {t('profile.totalSpent')}
                </span>
                <span className="amount" style={{ fontSize: 19, fontWeight: 600, marginTop: 3 }}>
                  {activeCur} {categoryTotal.toFixed(0)}
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 8 }}>
              {stats.by_category.map((item, i) => {
                const pct = ((item.total / categoryTotal) * 100).toFixed(0)
                return (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ width: 10, height: 10, borderRadius: 3, background: COLORS[i % COLORS.length], flexShrink: 0 }} />
                    <span style={{ flex: 1, fontSize: 14 }}>{translateCategory(item.category, lang)}</span>
                    <span className="amount" style={{ fontSize: 14, color: 'var(--tg-theme-hint-color)' }}>{pct}%</span>
                    <span className="amount" style={{ fontSize: 14, fontWeight: 500 }}>{activeCur} {item.total.toFixed(2)}</span>
                  </div>
                )
              })}
            </div>
          </div>

          <p style={{
            fontSize: 13, fontWeight: 600,
            color: 'var(--tg-theme-hint-color)',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            marginBottom: 12,
            marginTop: 4,
          }}>
            {t('analytics.last7Days')}
          </p>
          <div className="card">
            <ResponsiveContainer width="100%" height={190}>
              <BarChart data={dailyData} margin={{ top: 4, right: 0, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6C63FF" />
                    <stop offset="100%" stopColor="#3B8BFF" />
                  </linearGradient>
                </defs>
                <CartesianGrid
                  vertical={false}
                  strokeDasharray="4 4"
                  stroke="var(--tg-theme-hint-color)"
                  strokeOpacity={0.18}
                />
                <XAxis
                  dataKey="label"
                  tick={{ fontSize: 11, fill: 'var(--tg-theme-hint-color)', fontFamily: 'var(--font-body)' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: 'var(--tg-theme-hint-color)', fontFamily: 'var(--font-mono)' }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip content={<CustomTooltip currency={activeCur} />} cursor={{ fill: 'var(--accent-light)' }} />
                <Bar
                  dataKey="total"
                  name={t('dashboard.spent')}
                  fill="url(#barGrad)"
                  radius={[6, 6, 0, 0]}
                  maxBarSize={30}
                  animationDuration={600}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  )
}
