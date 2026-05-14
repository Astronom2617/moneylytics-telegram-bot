import { useState, useEffect, useCallback } from 'react'
import { Plus } from 'lucide-react'
import { BarChart, Bar, ResponsiveContainer, Tooltip } from 'recharts'
import { getStats, getExpenses } from '../api.js'
import AddExpenseModal from '../components/AddExpenseModal.jsx'
import { useTranslation, translateCategory, localeFor } from '../i18n.js'

const CATEGORY_COLORS = {
  Food: '#F59E0B',
  Transport: '#3B82F6',
  Shopping: '#EC4899',
  Entertainment: '#8B5CF6',
  Health: '#22C55E',
  Housing: '#F97316',
  Utilities: '#06B6D4',
  Education: '#6366F1',
  Travel: '#14B8A6',
  Gifts: '#EF4444',
  Other: '#94A3B8',
}

const CATEGORY_EMOJI = {
  Food: '🍕', Transport: '🚌', Shopping: '🛍',
  Entertainment: '🎬', Health: '💊', Housing: '🏠',
  Utilities: '💡', Education: '📚', Travel: '✈️',
  Gifts: '🎁', Other: '💰',
}

function capCat(cat) {
  return cat.charAt(0).toUpperCase() + cat.slice(1).toLowerCase()
}

function formatTotals(value, fallbackCur) {
  const entries = Object.entries(value || {})
  if (entries.length === 0) return `${fallbackCur} 0`
  return entries.map(([c, v]) => `${c} ${v.toFixed(0)}`).join(' · ')
}

function BudgetBar({ totals, budget, currency, t }) {
  if (!budget) return null
  const spent = (totals && totals[currency]) || 0
  const pct = Math.min((spent / budget) * 100, 100)
  const color = pct < 70 ? 'var(--success)' : pct < 95 ? 'var(--accent)' : 'var(--danger)'
  const remaining = budget - spent

  return (
    <div style={{ marginTop: 8 }}>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <p style={{ fontSize: 12, color: 'var(--tg-theme-hint-color)', marginTop: 6 }}>
        {remaining > 0
          ? <>{currency} {remaining.toFixed(2)} {t('dashboard.left')}</>
          : <span style={{ color: 'var(--danger)' }}>{t('dashboard.overBudgetBy')} {currency} {Math.abs(remaining).toFixed(2)}</span>
        }
      </p>
    </div>
  )
}

const SparkTooltip = ({ active, payload, currency }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--tg-theme-bg-color)',
      border: '1px solid var(--tg-theme-secondary-bg-color)',
      borderRadius: 8, padding: '6px 10px',
      fontSize: 12,
    }}>
      <p style={{ fontWeight: 500 }}>{payload[0].payload?.date}</p>
      <p style={{ color: 'var(--accent)', fontFamily: 'var(--font-mono)' }}>
        {currency} {Number(payload[0].value).toFixed(2)}
      </p>
    </div>
  )
}

export default function Dashboard({ user }) {
  const [stats,       setStats]       = useState(null)
  const [lastTx,      setLastTx]      = useState(null)
  const [loading,     setLoading]     = useState(true)
  const [showModal,   setShowModal]   = useState(false)

  const cur  = user?.currency ?? 'EUR'
  const lang = user?.language ?? 'en'
  const locale = localeFor(lang)
  const t = useTranslation(lang)

  const loadAll = useCallback(() => {
    setLoading(true)
    Promise.all([getStats('week'), getExpenses('month')])
      .then(([s, list]) => {
        setStats(s)
        setLastTx(list[0] || null)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { loadAll() }, [loadAll])

  const handleExpenseAdded = () => loadAll()

  const greeting = () => {
    const h = new Date().getHours()
    if (h < 12) return t('greeting.morning')
    if (h < 18) return t('greeting.afternoon')
    return t('greeting.evening')
  }

  const todayDate = new Date().toLocaleDateString(locale, {
    weekday: 'long', day: 'numeric', month: 'long',
  })

  const weekCount = stats?.count_week ?? 0
  const monthCount = stats?.count_month ?? 0
  const txWord = (n) => n === 1 ? t('dashboard.transaction') : t('dashboard.transactions')

  const lastTxCat = lastTx ? capCat(lastTx.category) : null

  return (
    <div className="page">
      <div className="page-header">
        <p style={{ fontSize: 14, color: 'var(--tg-theme-hint-color)' }}>{greeting()}</p>
        <h1 style={{ fontSize: 26, fontWeight: 700 }}>{user?.first_name ?? 'there'} 👋</h1>
        <p style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)', marginTop: 4, textTransform: 'capitalize' }}>
          {todayDate}
        </p>
      </div>

      {loading || !stats ? (
        <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 40 }}>
          <div className="spinner" />
        </div>
      ) : (
        <>
          {/* Три компактные карточки в строку */}
          <div className="stat-row">
            <div className="stat-card">
              <p className="stat-label">{t('dashboard.today')}</p>
              <p className="stat-value">{formatTotals(stats.today, cur)}</p>
              {stats.count_today > 0 && (
                <p className="stat-extra">{stats.count_today} {txWord(stats.count_today)}</p>
              )}
            </div>
            <div className="stat-card">
              <p className="stat-label">{t('dashboard.thisWeek')}</p>
              <p className="stat-value">{formatTotals(stats.week, cur)}</p>
              {weekCount > 0 && (
                <p className="stat-extra">{weekCount} {txWord(weekCount)}</p>
              )}
            </div>
            <div className="stat-card">
              <p className="stat-label">{t('dashboard.thisMonth')}</p>
              <p className="stat-value">{formatTotals(stats.month, cur)}</p>
              {monthCount > 0 && (
                <p className="stat-extra">{monthCount} {txWord(monthCount)}</p>
              )}
            </div>
          </div>

          {/* Прогресс-бары бюджетов */}
          {(user?.daily_budget || user?.weekly_budget) && (
            <div className="card">
              {user?.daily_budget && (
                <div style={{ marginBottom: user?.weekly_budget ? 14 : 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)', fontWeight: 500 }}>{t('dashboard.today')}</span>
                    <span className="amount" style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)' }}>
                      {t('dashboard.of')} {cur} {user.daily_budget}
                    </span>
                  </div>
                  <BudgetBar totals={stats.today} budget={user.daily_budget} currency={cur} t={t} />
                </div>
              )}
              {user?.weekly_budget && (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)', fontWeight: 500 }}>{t('dashboard.thisWeek')}</span>
                    <span className="amount" style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)' }}>
                      {t('dashboard.of')} {cur} {user.weekly_budget}
                    </span>
                  </div>
                  <BudgetBar totals={stats.week} budget={user.weekly_budget} currency={cur} t={t} />
                </div>
              )}
            </div>
          )}

          {/* Мотивационная подсказка если сегодня 0 */}
          {Object.keys(stats.today || {}).length === 0 && (
            <p style={{ fontSize: 13, color: 'var(--success)', textAlign: 'center', margin: '4px 0 12px' }}>
              {t('dashboard.motivateNoToday')}
            </p>
          )}

          {/* Sparkline — последние 7 дней */}
          {stats.daily_last_7 && stats.daily_last_7.some((d) => d.total > 0) && (
            <div className="card" style={{ padding: '10px 8px 4px' }}>
              <ResponsiveContainer width="100%" height={80}>
                <BarChart data={stats.daily_last_7} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
                  <Tooltip content={<SparkTooltip currency={cur} />} cursor={{ fill: 'var(--accent-light)' }} />
                  <Bar dataKey="total" fill="var(--accent)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Disclaimer о валюте */}
          <p style={{
            fontSize: 11,
            color: 'var(--tg-theme-hint-color)',
            fontStyle: 'italic',
            margin: '4px 4px 12px',
          }}>
            ℹ️ {t('analytics.totalsNote')}
          </p>

          {/* Последняя транзакция */}
          {lastTx && (
            <>
              <p style={{
                fontSize: 13, fontWeight: 600,
                color: 'var(--tg-theme-hint-color)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: 10,
              }}>
                {t('dashboard.lastTx')}
              </p>
              <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 14 }}>
                <div style={{
                  width: 44, height: 44, borderRadius: 12,
                  background: 'var(--accent-light)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 20, flexShrink: 0,
                }}>
                  {CATEGORY_EMOJI[lastTxCat] ?? '💰'}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ fontSize: 15, fontWeight: 500 }}>{translateCategory(lastTx.category, lang)}</p>
                  {lastTx.description && (
                    <p style={{ fontSize: 12, color: 'var(--tg-theme-hint-color)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {lastTx.description}
                    </p>
                  )}
                  <p style={{ fontSize: 11, color: 'var(--tg-theme-hint-color)', marginTop: 2 }}>
                    {new Date(lastTx.created_at).toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
                <p className="amount" style={{ fontSize: 16, fontWeight: 600 }}>
                  {lastTx.currency} {lastTx.amount.toFixed(2)}
                </p>
              </div>
            </>
          )}

          {/* Топ категории */}
          {stats.by_category.length > 0 ? (
            <>
              <p style={{
                fontSize: 13, fontWeight: 600,
                color: 'var(--tg-theme-hint-color)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: 10,
                marginTop: 8,
              }}>
                {t('dashboard.topCategories')}
              </p>
              <div className="card" style={{ padding: '8px 0' }}>
                {stats.by_category.slice(0, 5).map((item, i) => {
                  const cap = capCat(item.category)
                  const color = CATEGORY_COLORS[cap] ?? '#94A3B8'
                  const emoji = CATEGORY_EMOJI[cap] ?? '💰'
                  const maxTotal = stats.by_category[0].total
                  const pct = (item.total / maxTotal) * 100
                  return (
                    <div key={i} style={{ padding: '10px 16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, alignItems: 'center' }}>
                        <span style={{ fontSize: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontSize: 16 }}>{emoji}</span>
                          {translateCategory(item.category, lang)}
                        </span>
                        <span className="amount" style={{ fontSize: 14, color, fontWeight: 600 }}>
                          {cur} {item.total.toFixed(2)}
                        </span>
                      </div>
                      <div style={{ height: 4, borderRadius: 2, background: 'var(--tg-theme-bg-color)' }}>
                        <div style={{ width: `${pct}%`, height: '100%', borderRadius: 2, background: color, transition: 'width 0.5s ease' }} />
                      </div>
                    </div>
                  )
                })}
              </div>
            </>
          ) : !lastTx && (
            <div className="empty">
              <div className="empty-icon">📭</div>
              <p>{t('dashboard.noTx')}</p>
              <button
                className="btn-accent"
                onClick={() => setShowModal(true)}
                style={{ marginTop: 16, width: 'auto', display: 'inline-flex', alignItems: 'center', gap: 6, padding: '10px 24px' }}
              >
                <Plus size={18} /> {t('common.addExpense')}
              </button>
            </div>
          )}
        </>
      )}

      <button className="fab-extended" onClick={() => setShowModal(true)}>
        <Plus size={20} /> {t('dashboard.add')}
      </button>

      {showModal && (
        <AddExpenseModal
          user={user}
          onClose={() => setShowModal(false)}
          onAdded={handleExpenseAdded}
        />
      )}
    </div>
  )
}
