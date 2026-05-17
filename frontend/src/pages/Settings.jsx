import { useState, useEffect } from 'react'
import { Check } from 'lucide-react'
import { updateUser, getAlltimeStats } from '../api.js'
import { useTranslation } from '../i18n.js'
import { CURRENCIES, currencySymbol } from '../currency.js'

const LANGUAGES = [
  { id: 'en', label: '🇬🇧 English' },
  { id: 'ru', label: '🇷🇺 Русский' },
  { id: 'uk', label: '🇺🇦 Українська' },
]

// Builds the editable form from stored budgets: every cell is a string so
// empty means "no limit". Currencies absent from the user's budgets simply
// start blank.
function toForm(budgets) {
  const form = {}
  for (const [cur, limits] of Object.entries(budgets || {})) {
    form[cur] = {
      daily: limits?.daily != null ? String(limits.daily) : '',
      weekly: limits?.weekly != null ? String(limits.weekly) : '',
    }
  }
  return form
}

export default function Settings({ user, setUser }) {
  const [form,     setForm]     = useState(() => toForm(user?.budgets))
  const [currency, setCurrency] = useState(user?.currency ?? 'EUR')
  const [language, setLanguage] = useState(user?.language ?? 'en')
  const [used,     setUsed]     = useState([])
  const [saving,   setSaving]   = useState(false)
  const [saved,    setSaved]    = useState(false)

  const t = useTranslation(language)

  // Show a budget editor for every currency the user actually spends in,
  // plus their main currency — and nothing else, so the list stays short.
  useEffect(() => {
    getAlltimeStats()
      .then((s) => setUsed(Object.keys(s?.total_by_currency || {})))
      .catch(() => setUsed([]))
  }, [])

  const editable = CURRENCIES.filter(
    (c) => c === currency || used.includes(c) || form[c],
  ).sort((a, b) => {
    if (a === currency) return -1
    if (b === currency) return 1
    return CURRENCIES.indexOf(a) - CURRENCIES.indexOf(b)
  })

  const setLimit = (cur, period, value) => {
    setForm((prev) => ({
      ...prev,
      [cur]: { ...(prev[cur] || { daily: '', weekly: '' }), [period]: value },
    }))
  }

  const buildBudgets = () => {
    const out = {}
    for (const [cur, limits] of Object.entries(form)) {
      const entry = {}
      for (const period of ['daily', 'weekly']) {
        const raw = limits?.[period]
        if (raw === '' || raw == null) continue
        const num = parseFloat(raw)
        if (!Number.isNaN(num) && num > 0) entry[period] = num
      }
      if (Object.keys(entry).length) out[cur] = entry
    }
    return out
  }

  const handleSave = async () => {
    setSaving(true)
    const budgets = buildBudgets()
    try {
      const updated = await updateUser({ budgets, currency, language })
      setUser((prev) => ({ ...prev, ...updated }))
      setForm(toForm(updated.budgets))
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e) {
      console.error(e)
    } finally {
      setSaving(false)
    }
  }

  const sectionLabel = {
    fontSize: 13, fontWeight: 600,
    color: 'var(--tg-theme-hint-color)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    marginBottom: 10,
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('page.settings')}</h1>
      </div>

      <p style={sectionLabel}>{t('settings.budgets')}</p>
      <p style={{ fontSize: 12, color: 'var(--tg-theme-hint-color)', margin: '-4px 2px 12px' }}>
        {t('settings.budgetsHint')}
      </p>

      {editable.map((c) => (
        <div key={c} className="card" style={{ padding: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <span style={{
              fontSize: 13, fontWeight: 700,
              background: 'var(--accent-light)', color: 'var(--accent-dark)',
              borderRadius: 8, padding: '3px 10px',
            }}>
              {currencySymbol(c)} {c}
            </span>
            {c === currency && (
              <span style={{ fontSize: 11, color: 'var(--tg-theme-hint-color)' }}>
                {t('settings.mainCurrency')}
              </span>
            )}
          </div>

          <div style={{ display: 'flex', gap: 12 }}>
            <div style={{ flex: 1 }}>
              <label className="form-label">{t('settings.dailyLimit')}</label>
              <input
                className="input"
                type="number"
                inputMode="decimal"
                min="0"
                step="0.01"
                placeholder={t('settings.noLimit')}
                value={form[c]?.daily ?? ''}
                onChange={(e) => setLimit(c, 'daily', e.target.value)}
                onKeyDown={(e) => { if (['e', 'E', '+', '-'].includes(e.key)) e.preventDefault() }}
              />
            </div>
            <div style={{ flex: 1 }}>
              <label className="form-label">{t('settings.weeklyLimit')}</label>
              <input
                className="input"
                type="number"
                inputMode="decimal"
                min="0"
                step="0.01"
                placeholder={t('settings.noLimit')}
                value={form[c]?.weekly ?? ''}
                onChange={(e) => setLimit(c, 'weekly', e.target.value)}
                onKeyDown={(e) => { if (['e', 'E', '+', '-'].includes(e.key)) e.preventDefault() }}
              />
            </div>
          </div>
        </div>
      ))}

      <p style={{ ...sectionLabel, marginTop: 4 }}>{t('settings.mainCurrency')}</p>
      <div className="chips" style={{ marginBottom: 16 }}>
        {CURRENCIES.map((c) => (
          <button
            key={c}
            className={`chip ${currency === c ? 'active' : ''}`}
            onClick={() => setCurrency(c)}
          >
            {currencySymbol(c)} {c}
          </button>
        ))}
      </div>

      <p style={sectionLabel}>{t('settings.language')}</p>
      <div className="chips" style={{ marginBottom: 24 }}>
        {LANGUAGES.map((l) => (
          <button
            key={l.id}
            className={`chip ${language === l.id ? 'active' : ''}`}
            onClick={() => setLanguage(l.id)}
          >
            {l.label}
          </button>
        ))}
      </div>

      <button
        className="btn-accent"
        onClick={handleSave}
        disabled={saving}
        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}
      >
        {saved ? (
          <><Check size={17} /> {t('settings.saved')}</>
        ) : saving ? (
          t('settings.saving')
        ) : (
          t('settings.saveChanges')
        )}
      </button>

      {user && (
        <div style={{
          marginTop: 32,
          padding: '12px 0',
          borderTop: '1px solid var(--tg-theme-secondary-bg-color)',
          textAlign: 'center',
        }}>
          <p style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)' }}>
            {t('settings.loggedInAs')} <strong>{user.first_name}</strong>
          </p>
          <p style={{ fontSize: 12, color: 'var(--tg-theme-hint-color)', marginTop: 4 }}>
            {t('settings.id')}: {user.id}
          </p>
        </div>
      )}
    </div>
  )
}
