import { useState } from 'react'
import { X } from 'lucide-react'
import { createExpense } from '../api.js'
import { useTranslation } from '../i18n.js'
import { CURRENCIES, currencySymbol, normalizeCurrency } from '../currency.js'
import BottomSheet from './BottomSheet.jsx'
import DatePicker from './DatePicker.jsx'

const CATEGORIES = [
  { id: 'Food',          emoji: '🍕' },
  { id: 'Transport',     emoji: '🚌' },
  { id: 'Shopping',      emoji: '🛍' },
  { id: 'Entertainment', emoji: '🎬' },
  { id: 'Health',        emoji: '💊' },
  { id: 'Beauty',        emoji: '💅' },
  { id: 'Housing',       emoji: '🏠' },
  { id: 'Utilities',     emoji: '💡' },
  { id: 'Education',     emoji: '📚' },
  { id: 'Travel',        emoji: '✈️' },
  { id: 'Gifts',         emoji: '🎁' },
  { id: 'Transfer',      emoji: '💸' },
  { id: 'Other',         emoji: '💰' },
]

export default function AddExpenseModal({ user, onClose, onAdded }) {
  const pad = (n) => String(n).padStart(2, '0')
  const today = (() => {
    const d = new Date()
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
  })()

  const [amount,      setAmount]      = useState('')
  const [category,    setCategory]    = useState('Food')
  const [description, setDescription] = useState('')
  const [currency,    setCurrency]    = useState(normalizeCurrency(user?.currency ?? 'EUR'))
  const [date,        setDate]        = useState(today)
  const [loading,     setLoading]     = useState(false)
  const [error,       setError]       = useState(null)
  const t = useTranslation(user?.language)

  const handleSubmit = async (close) => {
    const amt = parseFloat(String(amount).replace(',', '.'))
    if (!amt || amt <= 0) {
      setError('Enter a valid amount')
      return
    }

    setLoading(true)
    setError(null)
    try {
      const now = new Date()
      const client_now = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`

      const expense = await createExpense({
        amount: amt,
        category,
        description: description.trim() || undefined,
        currency,
        client_now,
        expense_date: date,
        timezone_offset: now.getTimezoneOffset(),
      })
      onAdded(expense)
      close()
    } catch (e) {
      setError('Failed to save. Try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <BottomSheet onClose={onClose}>
      {(close) => (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h2 style={{ fontSize: 18, fontWeight: 600 }}>{t('common.newExpense')}</h2>
            <button
              onClick={close}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--tg-theme-hint-color)' }}
            >
              <X size={22} />
            </button>
          </div>

          <label className="form-label">{t('common.amount')}</label>
          <div className="amount-row">
            <span className="amount-symbol" key={currency}>{currencySymbol(currency)}</span>
            <input
              className="input"
              type="text"
              inputMode="decimal"
              placeholder="0.00"
              value={amount}
              onChange={(e) => {
                const v = e.target.value
                if (v === '' || /^[0-9]*[.,]?[0-9]*$/.test(v)) setAmount(v)
              }}
              onKeyDown={(e) => {
                if (e.key.length === 1 && !/[0-9.,]/.test(e.key) && !e.ctrlKey && !e.metaKey) {
                  e.preventDefault()
                }
              }}
              style={{ fontSize: 24, fontFamily: 'var(--font-mono)', flex: 1, minWidth: 0 }}
              autoFocus
            />
          </div>

          <label className="form-label">{t('expense.date')}</label>
          <div style={{ marginBottom: 16 }}>
            <DatePicker
              value={date}
              onChange={setDate}
              language={user?.language}
              maxDate={today}
            />
          </div>

          <label className="form-label">{t('settings.currency')}</label>
          <div className="chips" style={{ marginBottom: 16 }}>
            {CURRENCIES.map((c) => (
              <button
                key={c}
                type="button"
                className={`chip ${currency === c ? 'active' : ''}`}
                onClick={() => setCurrency(c)}
              >
                {currencySymbol(c)} {c}
              </button>
            ))}
          </div>

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

          <button className="btn-accent" onClick={() => handleSubmit(close)} disabled={loading}>
            {loading ? t('history.saving') : t('common.addExpense')}
          </button>
        </>
      )}
    </BottomSheet>
  )
}
