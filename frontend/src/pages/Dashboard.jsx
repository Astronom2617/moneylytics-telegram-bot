import { useState, useEffect, useCallback } from 'react'
import { Plus } from 'lucide-react'
import { getStats } from '../api.js'
import AddExpenseModal from '../components/AddExpenseModal.jsx'
import { useTranslation, translateCategory } from '../i18n.js'

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

function BudgetBar({ spent, budget, currency, t }) {
  if (!budget) return null

  const pct = Math.min((spent / budget) * 100, 100)
  const color = pct < 70 ? 'var(--success)' : pct < 95 ? 'var(--accent)' : 'var(--danger)'
  const remaining = budget - spent

  return (
    <div style={{ marginTop: 6 }}>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <p style={{ fontSize: 12, color: 'var(--tg-theme-hint-color)', marginTop: 4 }}>
        {remaining > 0
          ? <>{currency} {remaining.toFixed(2)} {t('dashboard.left')}</>
          : <span style={{ color: 'var(--danger)' }}>{t('dashboard.overBudgetBy')} {currency} {Math.abs(remaining).toFixed(2)}</span>
        }
      </p>
    </div>
  )
}

export default function Dashboard({ user }) {
  const [stats,       setStats]       = useState(null)
  const [loading,     setLoading]     = useState(true)
  const [showModal,   setShowModal]   = useState(false)

  const cur = user?.currency ?? 'EUR'
  const lang = user?.language ?? 'en'
  const t = useTranslation(lang)

  const loadStats = useCallback(() => {
    setLoading(true)
    getStats('week')
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { loadStats() }, [loadStats])

  const handleExpenseAdded = () => loadStats()

  const greeting = () => {
    const h = new Date().getHours()
    if (h < 12) return t('greeting.morning')
    if (h < 18) return t('greeting.afternoon')
    return t('greeting.evening')
  }

  const weekCount = stats?.count_week ?? 0
  const txWord = weekCount === 1 ? t('dashboard.transaction') : t('dashboard.transactions')

  return (
    <div className="page">
      <div className="page-header">
        <p style={{ fontSize: 14, color: 'var(--tg-theme-hint-color)' }}>{greeting()}</p>
        <h1 style={{ fontSize: 26, fontWeight: 600 }}>{user?.first_name ?? 'there'} 👋</h1>
      </div>

      {loading || !stats ? (
        <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 40 }}>
          <div className="spinner" />
        </div>
      ) : (
        <>
          {/* Сегодня */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <p style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)', fontWeight: 500 }}>{t('dashboard.today')}</p>
                <p className="amount" style={{ fontSize: 32, fontWeight: 500, marginTop: 2 }}>
                  {cur} {stats.today.toFixed(2)}
                </p>
                {stats.today === 0 && (
                  <p style={{ fontSize: 12, color: 'var(--success)', marginTop: 6 }}>
                    {t('dashboard.motivateNoToday')}
                  </p>
                )}
              </div>
              {user?.daily_budget && (
                <p style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)' }}>
                  {t('dashboard.of')} {cur} {user.daily_budget}
                </p>
              )}
            </div>
            <BudgetBar spent={stats.today} budget={user?.daily_budget} currency={cur} t={t} />
          </div>

          {/* Неделя */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <p style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)', fontWeight: 500 }}>{t('dashboard.thisWeek')}</p>
                <p className="amount" style={{ fontSize: 32, fontWeight: 500, marginTop: 2 }}>
                  {cur} {stats.week.toFixed(2)}
                </p>
                <p style={{ fontSize: 12, color: 'var(--tg-theme-hint-color)', marginTop: 6 }}>
                  {weekCount} {txWord}
                </p>
              </div>
              {user?.weekly_budget && (
                <p style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)' }}>
                  {t('dashboard.of')} {cur} {user.weekly_budget}
                </p>
              )}
            </div>
            <BudgetBar spent={stats.week} budget={user?.weekly_budget} currency={cur} t={t} />
          </div>

          {/* Месяц */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <p style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)', fontWeight: 500 }}>{t('dashboard.thisMonth')}</p>
                <p className="amount" style={{ fontSize: 28, fontWeight: 500, marginTop: 2 }}>
                  {cur} {stats.month.toFixed(2)}
                </p>
              </div>
              <p style={{ fontSize: 12, color: 'var(--tg-theme-hint-color)' }}>
                {stats.count_month ?? 0} {stats.count_month === 1 ? t('dashboard.transaction') : t('dashboard.transactions')}
              </p>
            </div>
          </div>

          <p style={{
            fontSize: 11,
            color: 'var(--tg-theme-hint-color)',
            fontStyle: 'italic',
            margin: '-4px 4px 12px',
          }}>
            ℹ️ {t('analytics.totalsNote')}
          </p>

          {/* Топ категории */}
          {stats.by_category.length > 0 ? (
            <>
              <p style={{
                fontSize: 13, fontWeight: 500,
                color: 'var(--tg-theme-hint-color)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: 10,
              }}>
                {t('dashboard.topCategories')}
              </p>
               <div className="card" style={{ padding: '8px 0' }}>
                 {stats.by_category.slice(0, 5).map((item, i) => {
                   const cap = item.category.charAt(0).toUpperCase() + item.category.slice(1).toLowerCase()
                   const color = CATEGORY_COLORS[cap] ?? '#94A3B8'
                   const maxTotal = stats.by_category[0].total
                   const pct = (item.total / maxTotal) * 100
                   return (
                     <div key={i} style={{ padding: '10px 16px' }}>
                       <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                         <span style={{ fontSize: 14 }}>{translateCategory(item.category, lang)}</span>
                         <span className="amount" style={{ fontSize: 14, color }}>
                           {cur} {item.total.toFixed(2)}
                         </span>
                       </div>
                       <div style={{ height: 3, borderRadius: 2, background: 'var(--tg-theme-bg-color)' }}>
                         <div style={{ width: `${pct}%`, height: '100%', borderRadius: 2, background: color }} />
                       </div>
                     </div>
                   )
                 })}
               </div>
            </>
          ) : stats.today === 0 && stats.week === 0 && (
            <div className="empty">
              <div className="empty-icon">📭</div>
              <p>{t('history.noExpenses')} {t('history.yet')}</p>
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

      <button className="fab" onClick={() => setShowModal(true)}>
        <Plus size={24} />
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
