import { useState, useEffect, useCallback } from 'react'
import { Plus } from 'lucide-react'
import { getStats } from '../api.js'
import AddExpenseModal from '../components/AddExpenseModal.jsx'

// Форматируем категорию: food → Food
const formatCategory = (cat) => cat.charAt(0).toUpperCase() + cat.slice(1).toLowerCase()

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

// Полоса бюджета: зелёная → жёлтая → красная в зависимости от %
function BudgetBar({ spent, budget, currency }) {
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
          ? <>{currency} {remaining.toFixed(2)} left</>
          : <span style={{ color: 'var(--danger)' }}>Over budget by {currency} {Math.abs(remaining).toFixed(2)}</span>
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

  const loadStats = useCallback(() => {
    setLoading(true)
    getStats('week')
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { loadStats() }, [loadStats])

  // После добавления расхода перезагружаем статистику
  const handleExpenseAdded = () => loadStats()

  const greeting = () => {
    const h = new Date().getHours()
    if (h < 12) return 'Good morning'
    if (h < 18) return 'Good afternoon'
    return 'Good evening'
  }

  return (
    <div className="page">
      {/* Приветствие */}
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
                <p style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)', fontWeight: 500 }}>TODAY</p>
                <p className="amount" style={{ fontSize: 32, fontWeight: 500, marginTop: 2 }}>
                  {cur} {stats.today.toFixed(2)}
                </p>
              </div>
              {user?.daily_budget && (
                <p style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)' }}>
                  of {cur} {user.daily_budget}
                </p>
              )}
            </div>
            <BudgetBar spent={stats.today} budget={user?.daily_budget} currency={cur} />
          </div>

          {/* Неделя */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <p style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)', fontWeight: 500 }}>THIS WEEK</p>
                <p className="amount" style={{ fontSize: 32, fontWeight: 500, marginTop: 2 }}>
                  {cur} {stats.week.toFixed(2)}
                </p>
              </div>
              {user?.weekly_budget && (
                <p style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)' }}>
                  of {cur} {user.weekly_budget}
                </p>
              )}
            </div>
            <BudgetBar spent={stats.week} budget={user?.weekly_budget} currency={cur} />
          </div>

          {/* Топ категории */}
          {stats.by_category.length > 0 && (
            <>
              <p style={{
                fontSize: 13, fontWeight: 500,
                color: 'var(--tg-theme-hint-color)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: 10,
              }}>
                Top categories this week
              </p>
               <div className="card" style={{ padding: '8px 0' }}>
                 {stats.by_category.slice(0, 5).map((item, i) => {
                   const displayCategory = formatCategory(item.category)
                   const color = CATEGORY_COLORS[displayCategory] ?? '#94A3B8'
                   const maxTotal = stats.by_category[0].total
                   const pct = (item.total / maxTotal) * 100
                   return (
                     <div key={i} style={{ padding: '10px 16px' }}>
                       <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                         <span style={{ fontSize: 14 }}>{displayCategory}</span>
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
          )}
        </>
      )}

      {/* FAB — кнопка добавления */}
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
