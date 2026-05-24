import { useState } from 'react'
import { X } from 'lucide-react'
import { createSubscription, updateSubscription } from '../api.js'
import { useTranslation } from '../i18n.js'
import { CURRENCIES, currencySymbol, normalizeCurrency } from '../currency.js'
import { CATEGORIES } from '../categories.js'
import { notify } from '../haptic.js'
import BottomSheet from './BottomSheet.jsx'
import DatePicker from './DatePicker.jsx'

const pad = (n) => String(n).padStart(2, '0')
const todayYMD = () => {
  const d = new Date()
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

// One modal handles both Create (sub === null) and Edit (sub === object). The
// caller controls the lifecycle and feeds back the saved row via onSaved.
export default function SubscriptionModal({ user, sub, onClose, onSaved }) {
  const editing = !!sub
  const [name,        setName]        = useState(sub?.name ?? '')
  const [amount,      setAmount]      = useState(sub ? String(sub.amount) : '')
  const [currency,    setCurrency]    = useState(normalizeCurrency(sub?.currency ?? user?.currency ?? 'EUR'))
  const [category,    setCategory]    = useState(
    sub?.category
      ? sub.category.charAt(0).toUpperCase() + sub.category.slice(1).toLowerCase()
      : 'Entertainment'
  )
  const [period,      setPeriod]      = useState(sub?.period ?? 'monthly')
  const [nextDue,     setNextDue]     = useState(sub?.next_due_date ?? todayYMD())
  const [loading,     setLoading]     = useState(false)
  const [error,       setError]       = useState(null)
  const t = useTranslation(user?.language)

  const handleSubmit = async (close) => {
    const amt = parseFloat(String(amount).replace(',', '.'))
    const trimmed = name.trim()
    if (!trimmed) { setError(t('subs.name')); return }
    if (!amt || amt <= 0) { setError(t('common.amount')); return }
    if (!nextDue) { setError(t('subs.nextDue')); return }

    setLoading(true)
    setError(null)
    try {
      const payload = {
        name: trimmed,
        amount: amt,
        currency,
        category: category.toLowerCase(),
        period,
        next_due_date: nextDue,
      }
      const saved = editing
        ? await updateSubscription(sub.id, payload)
        : await createSubscription(payload)
      notify('success')
      onSaved(saved)
      close()
    } catch (e) {
      notify('error')
      setError('Failed to save')
    } finally {
      setLoading(false)
    }
  }

  return (
    <BottomSheet onClose={onClose}>
      {(close) => (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h2 style={{ fontSize: 18, fontWeight: 600 }}>
              {editing ? t('subs.edit') : t('subs.add')}
            </h2>
            <button onClick={close} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--tg-theme-hint-color)' }}>
              <X size={22} />
            </button>
          </div>

          <label className="form-label">{t('subs.name')}</label>
          <input
            className="input"
            type="text"
            placeholder={t('subs.namePlaceholder')}
            value={name}
            onChange={(e) => setName(e.target.value)}
            style={{ marginBottom: 16 }}
            autoFocus={!editing}
          />

          <label className="form-label">{t('subs.amount')}</label>
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
              style={{ fontSize: 22, fontFamily: 'var(--font-mono)', flex: 1, minWidth: 0 }}
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

          <label className="form-label">{t('subs.period')}</label>
          <div className="chips" style={{ marginBottom: 16 }}>
            <button
              type="button"
              className={`chip ${period === 'monthly' ? 'active' : ''}`}
              onClick={() => setPeriod('monthly')}
            >
              {t('subs.monthly')}
            </button>
            <button
              type="button"
              className={`chip ${period === 'weekly' ? 'active' : ''}`}
              onClick={() => setPeriod('weekly')}
            >
              {t('subs.weekly')}
            </button>
          </div>

          <label className="form-label">{t('subs.nextDue')}</label>
          <div style={{ marginBottom: 16 }}>
            <DatePicker
              value={nextDue}
              onChange={setNextDue}
              language={user?.language}
            />
          </div>

          <label className="form-label">{t('common.category')}</label>
          <div className="chips" style={{ marginBottom: 20 }}>
            {CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                type="button"
                className={`chip ${category === cat.id ? 'active' : ''}`}
                onClick={() => setCategory(cat.id)}
              >
                {cat.emoji} {t(`cat.${cat.id}`)}
              </button>
            ))}
          </div>

          {error && (
            <p style={{ color: 'var(--danger)', fontSize: 13, marginBottom: 12 }}>{error}</p>
          )}

          <button className="btn-accent" onClick={() => handleSubmit(close)} disabled={loading}>
            {loading ? t('history.saving') : (editing ? t('subs.save') : t('subs.create'))}
          </button>
        </>
      )}
    </BottomSheet>
  )
}
