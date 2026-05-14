import { X, Pencil } from 'lucide-react'
import BottomSheet from './BottomSheet.jsx'
import { useTranslation, translateCategory, localeFor } from '../i18n.js'

const EMOJI = {
  Food: '🍕', Transport: '🚌', Shopping: '🛍',
  Entertainment: '🎬', Health: '💊', Housing: '🏠',
  Utilities: '💡', Education: '📚', Travel: '✈️',
  Gifts: '🎁', Other: '💰',
}

function getCategoryEmoji(cat) {
  const cap = cat.charAt(0).toUpperCase() + cat.slice(1).toLowerCase()
  return EMOJI[cap] ?? '💰'
}

function formatDateTime(isoStr, locale) {
  const d = new Date(isoStr)
  return d.toLocaleDateString(locale, {
    weekday: 'short', day: 'numeric', month: 'short', year: 'numeric',
  }) + ' · ' + d.toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' })
}

export default function ExpenseDetailModal({ expense, language, onClose, onDelete, onEdit, deleting }) {
  const t = useTranslation(language)
  const locale = localeFor(language)

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
              {getCategoryEmoji(expense.category)}
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

          {onEdit && (
            <button
              className="btn-primary"
              onClick={onEdit}
              style={{ marginTop: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}
            >
              <Pencil size={16} /> {t('history.edit')}
            </button>
          )}

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
