import { useState } from 'react'
import { Check } from 'lucide-react'
import { updateUser } from '../api.js'
import { useTranslation } from '../i18n.js'

const CURRENCIES = ['EUR', 'USD', 'UAH', 'GBP']
const LANGUAGES  = [
  { id: 'en', label: '🇬🇧 English' },
  { id: 'ru', label: '🇷🇺 Русский' },
  { id: 'uk', label: '🇺🇦 Українська' },
]

export default function Settings({ user, setUser }) {
  const [dailyBudget,  setDailyBudget]  = useState(user?.daily_budget  ?? '')
  const [weeklyBudget, setWeeklyBudget] = useState(user?.weekly_budget ?? '')
  const [currency,     setCurrency]     = useState(user?.currency  ?? 'EUR')
  const [language,     setLanguage]     = useState(user?.language  ?? 'en')
  const [saving,       setSaving]       = useState(false)
  const [saved,        setSaved]        = useState(false)

  const t = useTranslation(language)

  const handleSave = async () => {
    setSaving(true)
    try {
      await updateUser({
        daily_budget:  dailyBudget  === '' ? null : parseFloat(dailyBudget),
        weekly_budget: weeklyBudget === '' ? null : parseFloat(weeklyBudget),
        currency,
        language,
      })
      setUser((prev) => ({
        ...prev,
        daily_budget:  dailyBudget  === '' ? null : parseFloat(dailyBudget),
        weekly_budget: weeklyBudget === '' ? null : parseFloat(weeklyBudget),
        currency,
        language,
      }))
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

      <p style={sectionLabel}>{t('settings.budgets')} ({currency})</p>
      <div className="card" style={{ padding: '16px' }}>
        <label className="form-label">{t('settings.dailyLimit')}</label>
        <input
          className="input"
          type="number"
          inputMode="decimal"
          min="0"
          step="0.01"
          placeholder={t('settings.noLimit')}
          value={dailyBudget}
          onChange={(e) => setDailyBudget(e.target.value)}
          onKeyDown={(e) => { if (['e', 'E', '+', '-'].includes(e.key)) e.preventDefault() }}
          style={{ marginBottom: 14 }}
        />
        <label className="form-label">{t('settings.weeklyLimit')}</label>
        <input
          className="input"
          type="number"
          inputMode="decimal"
          min="0"
          step="0.01"
          placeholder={t('settings.noLimit')}
          value={weeklyBudget}
          onChange={(e) => setWeeklyBudget(e.target.value)}
          onKeyDown={(e) => { if (['e', 'E', '+', '-'].includes(e.key)) e.preventDefault() }}
        />
      </div>

      <p style={{ ...sectionLabel, marginTop: 4 }}>{t('settings.currency')}</p>
      <div className="chips" style={{ marginBottom: 16 }}>
        {CURRENCIES.map((c) => (
          <button
            key={c}
            className={`chip ${currency === c ? 'active' : ''}`}
            onClick={() => setCurrency(c)}
          >
            {c}
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
