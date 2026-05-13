import { useState, useEffect, useCallback } from 'react'
import { Trash2, Plus } from 'lucide-react'
import { getExpenses, deleteExpense } from '../api.js'
import AddExpenseModal from '../components/AddExpenseModal.jsx'

const PERIODS = [
  { id: 'today', label: 'Today' },
  { id: 'week',  label: 'Week' },
  { id: 'month', label: 'Month' },
  { id: 'all',   label: 'All' },
]

// Группируем расходы по дате (YYYY-MM-DD)
function groupByDate(expenses) {
  const groups = {}
  for (const e of expenses) {
    const key = e.created_at.slice(0, 10) // "2024-11-05"
    if (!groups[key]) groups[key] = []
    groups[key].push(e)
  }
  return Object.entries(groups).sort(([a], [b]) => b.localeCompare(a))
}

function formatDate(isoDate) {
  const d = new Date(isoDate + 'T00:00:00')
  const today = new Date()
  const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1)

  if (d.toDateString() === today.toDateString())     return 'Today'
  if (d.toDateString() === yesterday.toDateString()) return 'Yesterday'

  return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })
}

function formatTime(isoStr) {
  return new Date(isoStr).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}

export default function History({ user }) {
  const [period,    setPeriod]    = useState('week')
  const [expenses,  setExpenses]  = useState([])
  const [loading,   setLoading]   = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [deletingId, setDeletingId] = useState(null)

  const cur = user?.currency ?? 'EUR'

  const load = useCallback(() => {
    setLoading(true)
    getExpenses(period)
      .then(setExpenses)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [period])

  useEffect(() => { load() }, [load])

  const handleDelete = async (id) => {
    setDeletingId(id)
    try {
      await deleteExpense(id)
      setExpenses((prev) => prev.filter((e) => e.id !== id))
    } catch (e) {
      console.error(e)
    } finally {
      setDeletingId(null)
    }
  }

  const total = expenses.reduce((sum, e) => sum + e.amount, 0)

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">History</h1>
        {!loading && expenses.length > 0 && (
          <p className="page-subtitle">
            {expenses.length} transactions · {cur} {total.toFixed(2)}
          </p>
        )}
      </div>

      {/* Фильтры периода */}
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

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 40 }}>
          <div className="spinner" />
        </div>
      ) : expenses.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">📭</div>
          <p>No expenses {period !== 'all' ? `this ${period}` : 'yet'}</p>
        </div>
      ) : (
        groupByDate(expenses).map(([date, items]) => (
          <div key={date} style={{ marginBottom: 20 }}>
            {/* Дата-разделитель */}
            <p style={{
              fontSize: 13, fontWeight: 600,
              color: 'var(--tg-theme-hint-color)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              marginBottom: 8,
            }}>
              {formatDate(date)}
            </p>

            <div className="card" style={{ padding: '4px 0' }}>
              {items.map((e, i) => (
                <div key={e.id}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '12px 16px',
                    gap: 12,
                  }}>
                    {/* Иконка категории */}
                    <div style={{
                      width: 40, height: 40, borderRadius: 10,
                      background: 'var(--accent-light)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 18, flexShrink: 0,
                    }}>
                      {getCategoryEmoji(e.category)}
                    </div>

                    {/* Инфо */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ fontSize: 15, fontWeight: 500 }}>{e.category}</p>
                      {e.description && (
                        <p style={{
                          fontSize: 13,
                          color: 'var(--tg-theme-hint-color)',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}>
                          {e.description}
                        </p>
                      )}
                      <p style={{ fontSize: 12, color: 'var(--tg-theme-hint-color)', marginTop: 1 }}>
                        {formatTime(e.created_at)}
                      </p>
                    </div>

                    {/* Сумма + удаление */}
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <p className="amount" style={{ fontSize: 16, fontWeight: 500 }}>
                        {e.currency} {e.amount.toFixed(2)}
                      </p>
                      <button
                        onClick={() => handleDelete(e.id)}
                        disabled={deletingId === e.id}
                        style={{
                          background: 'none', border: 'none', cursor: 'pointer',
                          color: 'var(--danger)', opacity: deletingId === e.id ? 0.4 : 0.6,
                          marginTop: 4, padding: 2,
                        }}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>

                  {i < items.length - 1 && (
                    <div style={{ height: 1, background: 'var(--tg-theme-bg-color)', marginLeft: 68 }} />
                  )}
                </div>
              ))}
            </div>
          </div>
        ))
      )}

      <button className="fab" onClick={() => setShowModal(true)}>
        <Plus size={24} />
      </button>

      {showModal && (
        <AddExpenseModal
          user={user}
          onClose={() => setShowModal(false)}
          onAdded={(expense) => {
            setExpenses((prev) => [expense, ...prev])
          }}
        />
      )}
    </div>
  )
}

function getCategoryEmoji(cat) {
  const map = {
    Food: '🍕', Transport: '🚌', Shopping: '🛍',
    Entertainment: '🎬', Health: '💊', Housing: '🏠',
    Utilities: '💡', Education: '📚', Travel: '✈️',
    Gifts: '🎁', Other: '💰',
  }
  return map[cat] ?? '💰'
}
