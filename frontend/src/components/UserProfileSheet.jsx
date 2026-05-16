import { useEffect, useState } from 'react'
import { Download, X } from 'lucide-react'
import BottomSheet from './BottomSheet.jsx'
import Avatar from './Avatar.jsx'
import { getAlltimeStats, exportCSV } from '../api.js'
import { useTranslation } from '../i18n.js'

const MONTHS = {
  en: ['January','February','March','April','May','June','July','August','September','October','November','December'],
  ru: ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'],
  uk: ['січня','лютого','березня','квітня','травня','червня','липня','серпня','вересня','жовтня','листопада','грудня'],
}

function formatMemberSince(iso, lang) {
  if (!iso) return null
  const d = new Date(iso)
  if (isNaN(d.getTime())) return null
  const months = MONTHS[lang] ?? MONTHS.en
  return `${months[d.getMonth()]} ${d.getFullYear()}`
}

export default function UserProfileSheet({ user, photoUrl, onClose }) {
  const lang = user?.language ?? 'en'
  const t = useTranslation(lang)

  const [stats, setStats]         = useState(null)
  const [loading, setLoading]     = useState(true)
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    getAlltimeStats()
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const handleExport = async () => {
    setExporting(true)
    try { await exportCSV() }
    catch (e) { console.error(e) }
    finally { setExporting(false) }
  }

  const memberSinceISO = stats?.member_since ?? user?.created_at
  const memberSince = formatMemberSince(memberSinceISO, lang)

  const totalsLine = stats?.total_by_currency
    ? Object.entries(stats.total_by_currency)
        .map(([cur, amt]) => `${cur} ${amt.toFixed(2)}`)
        .join(' · ')
    : ''

  return (
    <BottomSheet onClose={onClose}>
      {(close) => (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h2 style={{ fontSize: 18, fontWeight: 600 }}>{t('profile.title')}</h2>
            <button
              onClick={close}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--tg-theme-hint-color)' }}
              aria-label="Close"
            >
              <X size={22} />
            </button>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 16 }}>
            <Avatar photoUrl={photoUrl} name={user?.first_name} size={64} />
            <div style={{ minWidth: 0 }}>
              <p style={{ fontSize: 18, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {user?.first_name ?? '—'}
              </p>
              {user?.username && (
                <p style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)' }}>@{user.username}</p>
              )}
              {memberSince && (
                <p style={{ fontSize: 12, color: 'var(--tg-theme-hint-color)', marginTop: 2 }}>
                  {t('profile.memberSince')} {memberSince}
                </p>
              )}
            </div>
          </div>

          <div className="card" style={{ marginBottom: 16 }}>
            <p style={{
              fontSize: 12, color: 'var(--tg-theme-hint-color)', fontWeight: 600,
              textTransform: 'uppercase', letterSpacing: '0.5px',
            }}>
              {t('profile.totalSpent')}
            </p>
            {loading ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: 12 }}>
                <div className="spinner" />
              </div>
            ) : stats && stats.total_count > 0 ? (
              <>
                <p className="amount" style={{ fontSize: 20, fontWeight: 600, marginTop: 6 }}>
                  {totalsLine || '—'}
                </p>
                <p style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)', marginTop: 4 }}>
                  {stats.total_count} {t('profile.transactions')}
                </p>
              </>
            ) : (
              <p style={{ fontSize: 14, color: 'var(--tg-theme-hint-color)', marginTop: 6 }}>—</p>
            )}
          </div>

          <div style={{
            height: 1,
            background: 'var(--tg-theme-secondary-bg-color)',
            margin: '4px 0 16px',
          }} />

          <button
            className="btn-accent"
            onClick={handleExport}
            disabled={exporting || (stats && stats.total_count === 0)}
            style={{
              background: 'var(--accent-gradient, linear-gradient(135deg, #8B5CF6 0%, #3B82F6 100%))',
              color: '#fff',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            }}
          >
            <Download size={18} />
            {exporting ? '…' : t('profile.export')}
          </button>
        </>
      )}
    </BottomSheet>
  )
}
