import { useState } from 'react'
import { Check } from 'lucide-react'
import { updateUser } from '../api.js'

const CURRENCIES = ['EUR', 'USD', 'GBP', 'RUB', 'PLN', 'CZK']
const LANGUAGES  = [
  { id: 'en', label: '🇬🇧 English' },
  { id: 'ru', label: '🇷🇺 Русский' },
]

export default function Settings({ user, setUser }) {
  const [dailyBudget,  setDailyBudget]  = useState(user?.daily_budget  ?? '')
  const [weeklyBudget, setWeeklyBudget] = useState(user?.weekly_budget ?? '')
  const [currency,     setCurrency]     = useState(user?.currency  ?? 'EUR')
  const [language,     setLanguage]     = useState(user?.language  ?? 'en')
  const [saving,       setSaving]       = useState(false)
  const [saved,        setSaved]        = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      await updateUser({
        daily_budget:  dailyBudget  === '' ? null : parseFloat(dailyBudget),
        weekly_budget: weeklyBudget === '' ? null : parseFloat(weeklyBudget),
        currency,
        language,
      })
      // Обновляем юзера в App — чтобы BudgetBar перезагрузился
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

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
      </div>

      {/* Бюджеты */}
      <p style={{
        fontSize: 13, fontWeight: 600,
        color: 'var(--tg-theme-hint-color)',
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
        marginBottom: 10,
      }}>
        Budgets ({currency})
      </p>
      <div className="card" style={{ padding: '16px' }}>
        <label className="form-label">Daily limit</label>
        <input
          className="input"
          type="number"
          inputMode="decimal"
          placeholder="No limit"
          value={dailyBudget}
          onChange={(e) => setDailyBudget(e.target.value)}
          style={{ marginBottom: 14 }}
        />
        <label className="form-label">Weekly limit</label>
        <input
          className="input"
          type="number"
          inputMode="decimal"
          placeholder="No limit"
          value={weeklyBudget}
          onChange={(e) => setWeeklyBudget(e.target.value)}
        />
      </div>

      {/* Валюта */}
      <p style={{
        fontSize: 13, fontWeight: 600,
        color: 'var(--tg-theme-hint-color)',
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
        marginBottom: 10,
        marginTop: 4,
      }}>
        Currency
      </p>
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

      {/* Язык */}
      <p style={{
        fontSize: 13, fontWeight: 600,
        color: 'var(--tg-theme-hint-color)',
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
        marginBottom: 10,
      }}>
        Language
      </p>
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
          <><Check size={17} /> Saved!</>
        ) : saving ? (
          'Saving…'
        ) : (
          'Save changes'
        )}
      </button>

      {/* Инфо о пользователе */}
      {user && (
        <div style={{
          marginTop: 32,
          padding: '12px 0',
          borderTop: '1px solid var(--tg-theme-secondary-bg-color)',
          textAlign: 'center',
        }}>
          <p style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)' }}>
            Logged in as <strong>{user.first_name}</strong>
          </p>
          <p style={{ fontSize: 12, color: 'var(--tg-theme-hint-color)', marginTop: 4 }}>
            ID: {user.id}
          </p>
        </div>
      )}
    </div>
  )
}
