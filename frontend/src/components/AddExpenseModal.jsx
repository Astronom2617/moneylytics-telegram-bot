import { useState } from 'react'
import { X } from 'lucide-react'
import { createExpense } from '../api.js'
import { useTranslation } from '../i18n.js'

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

const overlay = {
  position: 'fixed', inset: 0,
  background: 'rgba(0,0,0,0.45)',
  display: 'flex', alignItems: 'flex-end',
  zIndex: 300,
}

const sheet = {
  width: '100%',
  background: 'var(--tg-theme-bg-color)',
  borderRadius: '20px 20px 0 0',
  padding: '20px 16px 32px',
  maxHeight: '90vh',
  overflowY: 'auto',
}

export default function AddExpenseModal({ user, onClose, onAdded }) {
  const [amount,      setAmount]      = useState('')
  const [category,    setCategory]    = useState('Food')
  const [description, setDescription] = useState('')
  const [loading,     setLoading]     = useState(false)
  const [error,       setError]       = useState(null)
  const t = useTranslation(user?.language)

  const handleSubmit = async () => {
    const amt = parseFloat(amount)
    if (!amt || amt <= 0) {
      setError('Enter a valid amount')
      return
    }

    setLoading(true)
    setError(null)
    try {
      const expense = await createExpense({
        amount: amt,
        category,
        description: description.trim() || undefined,
        currency: user?.currency ?? 'EUR',
        timezone_offset: new Date().getTimezoneOffset(),
      })
      onAdded(expense)
      onClose()
    } catch (e) {
      setError('Failed to save. Try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={overlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div style={sheet}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ fontSize: 18, fontWeight: 600 }}>{t('common.newExpense')}</h2>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--tg-theme-hint-color)' }}
          >
            <X size={22} />
          </button>
        </div>

        <label className="form-label">{t('common.amount')} ({user?.currency ?? 'EUR'})</label>
        <input
          className="input"
          type="number"
          inputMode="decimal"
          placeholder="0.00"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
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

        <button className="btn-accent" onClick={handleSubmit} disabled={loading}>
          {loading ? t('history.saving') : t('common.addExpense')}
        </button>
      </div>
    </div>
  )
}
