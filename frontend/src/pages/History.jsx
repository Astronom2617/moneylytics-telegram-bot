import { useState, useEffect, useCallback } from 'react'
import { Trash2, Plus, X, Pencil } from 'lucide-react'
import { getExpenses, deleteExpense, updateExpense } from '../api.js'
import AddExpenseModal from '../components/AddExpenseModal.jsx'
import BottomSheet from '../components/BottomSheet.jsx'
import { useTranslation, translateCategory, localeFor } from '../i18n.js'

const PERIOD_IDS = ['today', 'week', 'month', 'all']

const CATEGORIES = [
  { id: 'Food',          emoji: '🍕' },
  { id: 'Transport',     emoji: '🚌' },
  { id: 'Shopping',      emoji: '🛍' },
  { id: 'Entertainment', emoji: '🎬' },
  { id: 'Health',        emoji: '💊' },
  { id: 'Housing',       emoji: '🏠' },
  { id: 'Utilities',     emoji: '💡' },
  { id: 'Education',     emoji: '📚' },
  { id: 'Travel',        emoji: '✈️' },
  { id: 'Gifts',         emoji: '🎁' },
  { id: 'Other',         emoji: '💰' },
]

function groupByDate(expenses) {
  const groups = {}
  for (const e of expenses) {
    const key = e.created_at.slice(0, 10)
    if (!groups[key]) groups[key] = []
    groups[key].push(e)
  }
  return Object.entries(groups).sort(([a], [b]) => b.localeCompare(a))
}

function formatDate(isoDate, t) {
  const d = new Date(isoDate + 'T00:00:00')
  const today = new Date()
  const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1)

  if (d.toDateString() === today.toDateString())     return t('history.today')
  if (d.toDateString() === yesterday.toDateString()) return t('history.yesterday')

  return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })
}

function formatTime(isoStr, locale) {
  return new Date(isoStr).toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' })
}

function formatDateTime(isoStr, locale) {
  const d = new Date(isoStr)
  return d.toLocaleDateString(locale, {
    weekday: 'short', day: 'numeric', month: 'short', year: 'numeric',
  }) + ' · ' + d.toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' })
}

function getCategoryEmoji(cat) {
  const map = {
    Food: '🍕', Transport: '🚌', Shopping: '🛍',
    Entertainment: '🎬', Health: '💊', Housing: '🏠',
    Utilities: '💡', Education: '📚', Travel: '✈️',
    Gifts: '🎁', Other: '💰',
  }
  const cap = cat.charAt(0).toUpperCase() + cat.slice(1).toLowerCase()
  return map[cap] ?? '💰'
}

function ExpenseDetailModal({ expense, language, onClose, onDelete, onEdit, deleting }) {
  const t = useTranslation(language)
  const locale = localeFor(language)
  const catKey = expense.category.charAt(0).toUpperCase() + expense.category.slice(1).toLowerCase()

  return (
    <BottomSheet onClose={onClose}>
      {(close) => (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h2 style={{ fontSize: 18, fontWeight: 600 }}>{t('history.details')}</h2>
            <button
              onClick={close}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--tg-theme-hint-color)' }}
            >
              <X size={22} />
            </button>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 24 }}>
            <div style={{
              width: 52, height: 52, borderRadius: 14,
              background: 'var(--accent-light)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 24, flexShrink: 0,
            }}>
              {getCategoryEmoji(catKey)}
            </div>
            <div>
              <p style={{ fontSize: 17, fontWeight: 600 }}>{translateCategory(expense.category, language)}</p>
              <p className="amount" style={{ fontSize: 26, fontWeight: 500, marginTop: 2 }}>
                {expense.currency} {expense.amount.toFixed(2)}
              </p>
            </div>
          </div>

          <div className="card" style={{ padding: '14px 16px', marginBottom: 12 }}>
            <div className="detail-row">
              <span className="detail-label">{t('history.dateTime')}</span>
              <span className="detail-value">{formatDateTime(expense.created_at, locale)}</span>
            </div>
            {expense.description && (
              <>
                <div style={{ height: 1, background: 'var(--tg-theme-bg-color)', margin: '10px 0' }} />
                <div className="detail-row">
                  <span className="detail-label">{t('history.note')}</span>
                  <span className="detail-value">{expense.description}</span>
                </div>
              </>
            )}
          </div>

          <button
            className="btn-primary"
            onClick={onEdit}
            style={{ marginTop: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}
          >
            <Pencil size={16} /> {t('history.edit')}
          </button>

          <button
            className="btn-danger"
            onClick={() => onDelete(expense.id)}
            disabled={deleting}
            style={{ marginTop: 10 }}
          >
            {deleting ? t('history.deleting') : t('history.delete')}
          </button>
        </>
      )}
    </BottomSheet>
  )
}

function ExpenseEditModal({ expense, language, onClose, onSaved }) {
  const t = useTranslation(language)
  const catKey = expense.category.charAt(0).toUpperCase() + expense.category.slice(1).toLowerCase()
  const [amount,      setAmount]      = useState(String(expense.amount))
  const [category,    setCategory]    = useState(catKey)
  const [description, setDescription] = useState(expense.description || '')
  const [saving,      setSaving]      = useState(false)
  const [error,       setError]       = useState(null)

  const handleSave = async (close) => {
    const amt = parseFloat(amount)
    if (!amt || amt <= 0) {
      setError('Invalid amount')
      return
    }
    setSaving(true)
    setError(null)
    try {
      const updated = await updateExpense(expense.id, {
        amount: amt,
        category,
        description: description.trim() || null,
      })
      onSaved(updated)
      close()
    } catch (e) {
      setError('Failed to save')
    } finally {
      setSaving(false)
    }
  }

  return (
    <BottomSheet onClose={onClose}>
      {(close) => (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h2 style={{ fontSize: 18, fontWeight: 600 }}>{t('history.edit')}</h2>
            <button
              onClick={close}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--tg-theme-hint-color)' }}
            >
              <X size={22} />
            </button>
          </div>

          <label className="form-label">{t('common.amount')} ({expense.currency})</label>
          <input
            className="input"
            type="number"
            inputMode="decimal"
            min="0"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            onKeyDown={(e) => { if (['e', 'E', '+', '-'].includes(e.key)) e.preventDefault() }}
            style={{ fontSize: 24, fontFamily: 'var(--font-mono)', marginBottom: 16 }}
            autoFocus
          />

          <label className="form-label">{t('common.category')}</label>
          <div className="chips" style={{ marginBottom: 16 }}>
            {CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                className={`chip ${category === cat.id ? 'active' : ''}`}
                onClick={() => setCategory(cat.id)}
              >
                {cat.emoji} {t(`cat.${cat.id}`)}
              </button>
            ))}
          </div>

          <label className="form-label">{t('common.noteOptional')}</label>
          <input
            className="input"
            type="text"
            placeholder={t('common.notePlaceholder')}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            style={{ marginBottom: 20 }}
          />

          {error && (
            <p style={{ color: 'var(--danger)', fontSize: 13, marginBottom: 12 }}>{error}</p>
          )}

          <button className="btn-accent" onClick={() => handleSave(close)} disabled={saving}>
            {saving ? t('history.saving') : t('history.save')}
          </button>
        </>
      )}
    </BottomSheet>
  )
}

export default function History({ user }) {
  const [period,      setPeriod]      = useState('week')
  const [expenses,    setExpenses]    = useState([])
  const [loading,     setLoading]     = useState(true)
  const [showModal,   setShowModal]   = useState(false)
  const [deletingId,  setDeletingId]  = useState(null)
  const [selected,    setSelected]    = useState(null)
  const [editing,     setEditing]     = useState(null)

  const lang = user?.language ?? 'en'
  const locale = localeFor(lang)
  const t = useTranslation(lang)

  const load = useCallback(() => {
    setLoading(true)
    getExpenses(period)
      .then(setExpenses)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [period])

  useEffect(() => { load() }, [load])

  const handleDelete = async (id) => {
    if (!window.confirm(t('history.confirmDelete'))) return
    setDeletingId(id)
    try {
      await deleteExpense(id)
      setExpenses((prev) => prev.filter((e) => e.id !== id))
      setSelected(null)
    } catch (e) {
      console.error(e)
    } finally {
      setDeletingId(null)
    }
  }

  const handleSaved = (updated) => {
    setExpenses((prev) => prev.map((e) => (e.id === updated.id ? updated : e)))
    setEditing(null)
    setSelected(null)
  }

  const totalsByCurrency = expenses.reduce((acc, e) => {
    const c = e.currency || 'EUR'
    acc[c] = (acc[c] || 0) + e.amount
    return acc
  }, {})
  const totalsStr = Object.entries(totalsByCurrency)
    .map(([c, v]) => `${c} ${v.toFixed(2)}`)
    .join(' · ')

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('page.history')}</h1>
        {!loading && expenses.length > 0 && (
          <p className="page-subtitle">
            {expenses.length} {t('history.transactions')} · {totalsStr}
          </p>
        )}
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

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 40 }}>
          <div className="spinner" />
        </div>
      ) : expenses.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">📭</div>
          <p>{t('history.noExpenses')} {period !== 'all' ? `${t('history.this')} ${t(`period.${period}`).toLowerCase()}` : t('history.yet')}</p>
          <button
            className="btn-accent"
            onClick={() => setShowModal(true)}
            style={{ marginTop: 16, width: 'auto', display: 'inline-flex', alignItems: 'center', gap: 6, padding: '10px 24px' }}
          >
            <Plus size={18} /> {t('common.addExpense')}
          </button>
        </div>
      ) : (
        groupByDate(expenses).map(([date, items]) => (
          <div key={date} style={{ marginBottom: 20 }}>
            <p style={{
              fontSize: 13, fontWeight: 600,
              color: 'var(--tg-theme-hint-color)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              marginBottom: 8,
            }}>
              {formatDate(date, t)}
            </p>

            <div className="card" style={{ padding: '4px 0' }}>
              {items.map((e, i) => (
                <div key={e.id}>
                  <div
                    onClick={() => setSelected(e)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '12px 16px',
                      gap: 12,
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{
                      width: 40, height: 40, borderRadius: 10,
                      background: 'var(--accent-light)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 18, flexShrink: 0,
                    }}>
                      {getCategoryEmoji(e.category)}
                    </div>

                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ fontSize: 15, fontWeight: 500 }}>{translateCategory(e.category, lang)}</p>
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
                        {formatTime(e.created_at, locale)}
                      </p>
                    </div>

                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <p className="amount" style={{ fontSize: 16, fontWeight: 500 }}>
                        {e.currency} {e.amount.toFixed(2)}
                      </p>
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

      {selected && !editing && (
        <ExpenseDetailModal
          expense={selected}
          language={lang}
          onClose={() => setSelected(null)}
          onDelete={handleDelete}
          onEdit={() => setEditing(selected)}
          deleting={deletingId === selected.id}
        />
      )}

      {editing && (
        <ExpenseEditModal
          expense={editing}
          language={lang}
          onClose={() => setEditing(null)}
          onSaved={handleSaved}
        />
      )}
    </div>
  )
}
