import { useState, useEffect, useCallback } from 'react'
import { Plus, Pencil, Trash2, Pause, Play } from 'lucide-react'
import {
  getSubscriptions, deleteSubscription, updateSubscription,
} from '../api.js'
import { useTranslation, translateCategory, localeFor } from '../i18n.js'
import { currencySymbol } from '../currency.js'
import { CATEGORY_EMOJI, capCat } from '../categories.js'
import SubscriptionModal from '../components/SubscriptionModal.jsx'
import { useFabCollapse } from '../useFabCollapse.js'

// Per-month equivalent so the totals card can roll weekly subs into the same
// "per month" number. 30/7 averages out fine for a single summary line.
const monthlyEquivalent = (sub) =>
  sub.period === 'weekly' ? sub.amount * (30 / 7) : sub.amount

const SECTION_LABEL = {
  fontSize: 13, fontWeight: 600,
  color: 'var(--tg-theme-hint-color)',
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
  marginBottom: 10,
  marginTop: 8,
}

function formatDue(iso, locale) {
  if (!iso) return ''
  try {
    return new Date(iso + 'T12:00:00').toLocaleDateString(locale, {
      day: 'numeric', month: 'short',
    })
  } catch { return iso }
}

export default function Subscriptions({ user }) {
  const [items,     setItems]     = useState([])
  const [loading,   setLoading]   = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editing,   setEditing]   = useState(null)
  const fabCollapsed = useFabCollapse()

  const lang = user?.language ?? 'en'
  const locale = localeFor(lang)
  const t = useTranslation(lang)

  const load = useCallback(() => {
    setLoading(true)
    getSubscriptions()
      .then(setItems)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  const handleSaved = () => { setEditing(null); setShowModal(false); load() }

  const handleDelete = async (sub) => {
    if (!window.confirm(t('subs.confirmDelete'))) return
    try {
      await deleteSubscription(sub.id)
      load()
    } catch (e) { console.error(e) }
  }

  const handleToggleActive = async (sub) => {
    try {
      await updateSubscription(sub.id, { active: !sub.active })
      load()
    } catch (e) { console.error(e) }
  }

  // Sum monthly-equivalents per currency for the totals card. Paused subs
  // are excluded — the "per month" line should match what'll actually fire.
  const monthlyTotals = items.reduce((acc, s) => {
    if (!s.active) return acc
    acc[s.currency] = (acc[s.currency] || 0) + monthlyEquivalent(s)
    return acc
  }, {})

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('page.subscriptions')}</h1>
      </div>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 40 }}>
          <div className="spinner" />
        </div>
      ) : items.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">🔁</div>
          <p>{t('subs.empty')}</p>
          <p style={{
            fontSize: 12, color: 'var(--tg-theme-hint-color)',
            marginTop: 6, maxWidth: 260, lineHeight: 1.4,
            textAlign: 'center', marginLeft: 'auto', marginRight: 'auto',
          }}>
            {t('subs.emptyHint')}
          </p>
          <button
            className="btn-accent"
            onClick={() => setShowModal(true)}
            style={{ marginTop: 16, width: 'auto', display: 'inline-flex', alignItems: 'center', gap: 6, padding: '10px 24px' }}
          >
            <Plus size={18} /> {t('subs.add')}
          </button>
        </div>
      ) : (
        <>
          {Object.keys(monthlyTotals).length > 0 && (
            <div className="card" style={{ padding: 14 }}>
              <p style={{
                fontSize: 11, fontWeight: 600,
                color: 'var(--tg-theme-hint-color)',
                textTransform: 'uppercase', letterSpacing: '0.4px',
              }}>
                {t('subs.totalMonthly')}
              </p>
              <div style={{ marginTop: 4 }}>
                {Object.entries(monthlyTotals).map(([c, v]) => (
                  <p key={c} className="amount" style={{ fontSize: 22, fontWeight: 600 }}>
                    {currencySymbol(c)}{v.toFixed(2)}
                    <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--tg-theme-hint-color)', marginLeft: 4 }}>
                      / {c}
                    </span>
                  </p>
                ))}
              </div>
            </div>
          )}

          <p style={SECTION_LABEL}>{t('page.subscriptions')}</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {items.map((s) => {
              const cap = capCat(s.category)
              const emoji = CATEGORY_EMOJI[cap] ?? '🔁'
              return (
                <div
                  key={s.id}
                  className="card"
                  style={{
                    padding: 14, display: 'flex', alignItems: 'center', gap: 12,
                    opacity: s.active ? 1 : 0.55,
                  }}
                >
                  <div style={{
                    width: 44, height: 44, borderRadius: 12,
                    background: 'var(--accent-light)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 22, flexShrink: 0,
                  }}>
                    {emoji}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ fontSize: 15, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {s.name}
                    </p>
                    <p style={{ fontSize: 12, color: 'var(--tg-theme-hint-color)', marginTop: 2 }}>
                      {translateCategory(s.category, lang)} ·{' '}
                      {s.period === 'weekly' ? t('subs.weekly') : t('subs.monthly')}
                    </p>
                    <p style={{ fontSize: 11, color: 'var(--tg-theme-hint-color)', marginTop: 2 }}>
                      {s.active
                        ? <>{t('subs.nextDue')}: {formatDue(s.next_due_date, locale)}</>
                        : t('subs.paused')}
                    </p>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
                    <p className="amount" style={{ fontSize: 15, fontWeight: 600, whiteSpace: 'nowrap' }}>
                      {currencySymbol(s.currency)}{s.amount.toFixed(2)}
                    </p>
                    <div style={{ display: 'flex', gap: 4 }}>
                      <button
                        type="button"
                        onClick={() => handleToggleActive(s)}
                        title={s.active ? t('subs.pause') : t('subs.resume')}
                        style={iconBtn}
                      >
                        {s.active ? <Pause size={15} /> : <Play size={15} />}
                      </button>
                      <button
                        type="button"
                        onClick={() => { setEditing(s); setShowModal(true) }}
                        title={t('subs.edit')}
                        style={iconBtn}
                      >
                        <Pencil size={15} />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(s)}
                        title={t('subs.delete')}
                        style={{ ...iconBtn, color: 'var(--danger)' }}
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}

      <button
        className={`fab-extended${fabCollapsed ? ' collapsed' : ''}`}
        onClick={() => { setEditing(null); setShowModal(true) }}
        aria-label={t('subs.add')}
      >
        <Plus size={20} />
        <span className="fab-label">{t('subs.add')}</span>
      </button>

      {showModal && (
        <SubscriptionModal
          user={user}
          sub={editing}
          onClose={() => { setShowModal(false); setEditing(null) }}
          onSaved={handleSaved}
        />
      )}
    </div>
  )
}

const iconBtn = {
  background: 'transparent', border: 'none',
  padding: 6, borderRadius: 6, cursor: 'pointer',
  color: 'var(--tg-theme-hint-color)',
  display: 'flex', alignItems: 'center', justifyContent: 'center',
}
