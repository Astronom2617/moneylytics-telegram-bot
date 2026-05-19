import { useState, useEffect } from 'react'
import { Check } from 'lucide-react'
import { updateUser, getAlltimeStats, setupMono, removeMono, getMonoStatus } from '../api.js'
import { useTranslation } from '../i18n.js'
import { CURRENCIES, currencySymbol } from '../currency.js'

const LANGUAGES = [
  { id: 'en', label: '🇬🇧 English' },
  { id: 'ru', label: '🇷🇺 Русский' },
  { id: 'uk', label: '🇺🇦 Українська' },
]

const MONO_TOKEN_URL = 'https://api.monobank.ua/'

// Turns the literal "api.monobank.ua" inside an instruction line into a
// tappable link, leaving the rest of the text untouched.
function linkifyMono(text) {
  const parts = text.split('api.monobank.ua')
  if (parts.length === 1) return text
  const out = []
  parts.forEach((part, i) => {
    if (i > 0) {
      out.push(
        <a
          key={`l${i}`}
          href={MONO_TOKEN_URL}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: 'var(--accent-dark)', textDecoration: 'underline' }}
        >
          api.monobank.ua
        </a>,
      )
    }
    if (part) out.push(<span key={`t${i}`}>{part}</span>)
  })
  return out
}

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

// Per-currency validation. Returns error codes (not messages) so the caller
// controls when each is shown. Codes: 'pos' = a set limit isn't a positive
// number; for daily-over-weekly the SAME conflict is reported on both fields
// in each field's own words — 'lte' under daily ("can't exceed weekly"),
// 'gte' under weekly ("must be ≥ daily") — so neither field is left
// unexplained. The comparison only runs once both are valid positives, so
// 'pos' wins over the cross-field codes.
function fieldErrors(limits) {
  const errs = { daily: null, weekly: null }
  const dRaw = limits?.daily
  const wRaw = limits?.weekly
  const dSet = dRaw !== '' && dRaw != null
  const wSet = wRaw !== '' && wRaw != null
  const d = dSet ? parseFloat(dRaw) : null
  const w = wSet ? parseFloat(wRaw) : null

  if (dSet && (Number.isNaN(d) || d <= 0)) errs.daily = 'pos'
  if (wSet && (Number.isNaN(w) || w <= 0)) errs.weekly = 'pos'
  if (!errs.daily && !errs.weekly && dSet && wSet && w < d) {
    errs.daily = 'lte'
    errs.weekly = 'gte'
  }
  return errs
}

export default function Settings({ user, setUser }) {
  const [form,     setForm]     = useState(() => toForm(user?.budgets))
  const [currency, setCurrency] = useState(user?.currency ?? 'EUR')
  const [language, setLanguage] = useState(user?.language ?? 'en')
  const [used,     setUsed]     = useState([])
  const [saving,   setSaving]   = useState(false)
  const [saved,    setSaved]    = useState(false)
  const [touched,  setTouched]  = useState({})

  const [monoConnected, setMonoConnected] = useState(null)
  const [monoToken,     setMonoToken]     = useState('')
  const [monoBusy,      setMonoBusy]      = useState(false)
  const [monoError,     setMonoError]     = useState(null)

  const t = useTranslation(language)

  useEffect(() => {
    getMonoStatus()
      .then((s) => setMonoConnected(!!s?.connected))
      .catch(() => setMonoConnected(false))
  }, [])

  const handleMonoConnect = async () => {
    const token = monoToken.trim()
    if (!token) return
    setMonoBusy(true)
    setMonoError(null)
    try {
      const res = await setupMono(token)
      if (res?.ok) {
        setMonoConnected(true)
        setMonoToken('')
      } else {
        setMonoError(res?.error || t('settings.monoConnect'))
      }
    } catch (e) {
      setMonoError(t('settings.monoConnect'))
    } finally {
      setMonoBusy(false)
    }
  }

  const handleMonoDisconnect = async () => {
    if (!window.confirm(t('settings.monoDisconnectConfirm'))) return
    setMonoBusy(true)
    setMonoError(null)
    try {
      await removeMono()
      setMonoConnected(false)
    } catch (e) {
      setMonoError(t('settings.monoDisconnect'))
    } finally {
      setMonoBusy(false)
    }
  }

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
    setTouched((prev) => ({ ...prev, [`${cur}.${period}`]: true }))
  }

  const errorMsg = (code) => {
    if (code === 'gte') return t('settings.errorWeekly')
    if (code === 'lte') return t('settings.errorDailyMax')
    return t('settings.errorDaily')
  }

  const hasErrors = editable.some((c) => {
    const e = fieldErrors(form[c])
    return e.daily || e.weekly
  })

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

      {editable.map((c) => {
        const errs = fieldErrors(form[c])
        const dTouched = touched[`${c}.daily`]
        const wTouched = touched[`${c}.weekly`]
        // The daily-over-weekly conflict shows on both fields. Either edit
        // can introduce it, so each side's message surfaces as soon as
        // either field has been touched — never an unexplained error.
        const showDaily = errs.daily &&
          (dTouched || (errs.daily === 'lte' && wTouched))
        const showWeekly = errs.weekly &&
          (wTouched || (errs.weekly === 'gte' && dTouched))
        const errStyle = {
          color: 'var(--danger)', fontSize: 12, marginTop: 6,
        }
        return (
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
              {showDaily && (
                <p style={errStyle}>{errorMsg(errs.daily)}</p>
              )}
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
              {showWeekly && (
                <p style={errStyle}>{errorMsg(errs.weekly)}</p>
              )}
            </div>
          </div>
        </div>
        )
      })}

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

      <p style={{ ...sectionLabel, marginTop: 4 }}>{t('settings.mono')}</p>
      <div className="card" style={{ padding: 16, marginBottom: 24 }}>
        {monoConnected ? (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{
                width: 9, height: 9, borderRadius: '50%',
                background: '#28a745', flexShrink: 0,
              }} />
              <span style={{ fontSize: 14, fontWeight: 500 }}>
                {t('settings.monoConnected')}
              </span>
            </div>
            <button
              className="btn-danger"
              onClick={handleMonoDisconnect}
              disabled={monoBusy}
              style={{ marginTop: 14 }}
            >
              {t('settings.monoDisconnect')}
            </button>
          </>
        ) : (
          <>
            <p style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)', marginBottom: 12 }}>
              {t('settings.monoHint')}
            </p>
            <input
              className="input"
              type="password"
              placeholder={t('settings.monoTokenPlaceholder')}
              value={monoToken}
              onChange={(e) => setMonoToken(e.target.value)}
              autoComplete="off"
              style={{ marginBottom: 8 }}
            />
            <a
              href={MONO_TOKEN_URL}
              target="_blank"
              rel="noopener noreferrer"
              style={{ fontSize: 12, color: 'var(--accent-dark)', textDecoration: 'none' }}
            >
              {t('settings.monoApiLink')}
            </a>
            <div style={{
              marginTop: 12,
              fontSize: 12,
              color: 'var(--tg-theme-hint-color)',
              lineHeight: 1.6,
            }}>
              <p style={{ marginBottom: 4 }}>{t('settings.monoInstructions')}</p>
              <ol style={{ margin: 0, paddingLeft: 18 }}>
                <li>{linkifyMono(t('settings.monoStep1'))}</li>
                <li>{linkifyMono(t('settings.monoStep2'))}</li>
                <li>{linkifyMono(t('settings.monoStep3'))}</li>
                <li>{linkifyMono(t('settings.monoStep4'))}</li>
              </ol>
            </div>
            {monoError && (
              <p style={{ color: 'var(--danger)', fontSize: 12, marginTop: 10 }}>{monoError}</p>
            )}
            <button
              className="btn-accent"
              onClick={handleMonoConnect}
              disabled={monoBusy || !monoToken.trim()}
              style={{ marginTop: 14 }}
            >
              {t('settings.monoConnect')}
            </button>
          </>
        )}
      </div>

      <button
        className="btn-accent"
        onClick={handleSave}
        disabled={saving || hasErrors}
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
