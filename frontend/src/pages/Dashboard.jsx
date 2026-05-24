import { useState, useEffect, useCallback } from 'react'
import { Plus } from 'lucide-react'
import { BarChart, Bar, ResponsiveContainer, Tooltip } from 'recharts'
import { getStats, getExpenses, deleteExpense } from '../api.js'
import { currencySymbol } from '../currency.js'
import AddExpenseModal from '../components/AddExpenseModal.jsx'
import ExpenseDetailModal from '../components/ExpenseDetailModal.jsx'
import Avatar from '../components/Avatar.jsx'
import UserProfileSheet from '../components/UserProfileSheet.jsx'
import { useTranslation, translateCategory, localeFor } from '../i18n.js'
import { useFabCollapse } from '../useFabCollapse.js'
import { CATEGORY_COLORS, CATEGORY_EMOJI, capCat as capCatShared } from '../categories.js'

const TG_PHOTO_URL = window.Telegram?.WebApp?.initDataUnsafe?.user?.photo_url ?? null

const SECTION_LABEL = {
  fontSize: 13, fontWeight: 600,
  color: 'var(--tg-theme-hint-color)',
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
  marginBottom: 10,
  marginTop: 8,
}

const capCat = capCatShared

function ymd(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

// Trims trailing zeros so limits read as "50" but "12.50" keeps its cents.
function money(n) {
  return Number.isInteger(n) ? String(n) : n.toFixed(2)
}

function dayLabel(isoDate, locale) {
  try {
    return new Date(isoDate + 'T00:00:00').toLocaleDateString(locale, { weekday: 'short' })
  } catch {
    return isoDate
  }
}

function computeStreak(expenses) {
  if (!expenses || !expenses.length) return 0
  const days = new Set(expenses.map((e) => e.created_at.slice(0, 10)))
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  let streak = 0
  while (days.has(ymd(d))) {
    streak++
    d.setDate(d.getDate() - 1)
  }
  return streak
}

// Primary currency (user's default) shown large; any other currencies are
// stacked compactly underneath as a single muted, wrapping line so three
// cards still fit a phone row no matter how many currencies are in play.
function StatValue({ totals, primary }) {
  const entries = Object.entries(totals || {})
  if (entries.length === 0) {
    return <p className="stat-value">{currencySymbol(primary)}0</p>
  }
  entries.sort((a, b) => {
    if (a[0] === primary) return -1
    if (b[0] === primary) return 1
    return b[1] - a[1]
  })
  const [mainCur, mainVal] = entries[0]
  const rest = entries.slice(1)
  return (
    <>
      <p className="stat-value">{currencySymbol(mainCur)}{mainVal.toFixed(0)}</p>
      {rest.length > 0 && (
        <p className="stat-value-sub">
          {rest.map(([c, v]) => `${currencySymbol(c)}${v.toFixed(0)}`).join(' · ')}
        </p>
      )}
    </>
  )
}

function BudgetRow({ label, spent, limit, symbol, t }) {
  const pct = Math.min((spent / limit) * 100, 100)
  const color = pct < 70 ? 'var(--success)' : pct < 95 ? 'var(--accent)' : 'var(--danger)'
  const remaining = limit - spent
  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <span style={{
          fontSize: 11, fontWeight: 600, letterSpacing: '0.4px',
          textTransform: 'uppercase', color: 'var(--tg-theme-hint-color)',
        }}>
          {label}
        </span>
        <span className="amount" style={{ fontSize: 13 }}>
          <span style={{ fontWeight: 600 }}>{symbol}{money(spent)}</span>
          <span style={{ color: 'var(--tg-theme-hint-color)' }}> / {symbol}{money(limit)}</span>
        </span>
      </div>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <p style={{ fontSize: 11, color: 'var(--tg-theme-hint-color)', marginTop: 5 }}>
        {remaining >= 0
          ? <>{symbol}{money(remaining)} {t('dashboard.left')}</>
          : <span style={{ color: 'var(--danger)' }}>{t('dashboard.overBudgetBy')} {symbol}{Math.abs(remaining).toFixed(2)}</span>}
      </p>
    </div>
  )
}

// Compact per-category progress row: emoji + name on the left, spent/limit
// on the right, thin bar below. One row per (category, period); rows with
// no configured limit are skipped before reaching this component.
function CategoryBudgetRow({ catId, period, spent, limit, symbol, t, lang }) {
  const pct = Math.min((spent / limit) * 100, 100)
  const color = pct < 70 ? 'var(--success)' : pct < 95 ? 'var(--accent)' : 'var(--danger)'
  const cap = capCat(catId)
  const emoji = CATEGORY_EMOJI[cap] ?? '💰'
  const periodLabel = period === 'daily' ? t('dashboard.today') : t('dashboard.thisWeek')
  return (
    <div style={{ marginTop: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 8 }}>
        <span style={{ fontSize: 12, display: 'inline-flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
          <span style={{ fontSize: 14 }}>{emoji}</span>
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {translateCategory(catId, lang)}
          </span>
          <span style={{ color: 'var(--tg-theme-hint-color)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.3px' }}>
            · {periodLabel}
          </span>
        </span>
        <span className="amount" style={{ fontSize: 12, flexShrink: 0 }}>
          <span style={{ fontWeight: 600 }}>{symbol}{money(spent)}</span>
          <span style={{ color: 'var(--tg-theme-hint-color)' }}> / {symbol}{money(limit)}</span>
        </span>
      </div>
      <div className="progress-bar" style={{ height: 4, marginTop: 4 }}>
        <div className="progress-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  )
}

// One card per currency that actually has a limit. Currencies without a
// budget are skipped entirely — no empty placeholders — and the whole
// section disappears when nothing is configured.
function Budgets({ budgets, stats, primary, t, lang }) {
  const hasAny = (b) => {
    if (!b) return false
    if (b.daily || b.weekly) return true
    const cats = b.categories || {}
    return Object.values(cats).some((cl) => cl?.daily || cl?.weekly)
  }
  const order = [primary, ...Object.keys(budgets).filter((c) => c !== primary)]
  const cards = order
    .filter((c) => hasAny(budgets[c]))
    .map((c) => {
      const b = budgets[c]
      const sym = currencySymbol(c)
      const catBudgets = b.categories || {}
      const todayCats = (stats.by_category_today || {})[c] || {}
      const weekCats = (stats.by_category_week || {})[c] || {}
      return (
        <div key={c} className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{
              fontSize: 12, fontWeight: 700,
              background: 'var(--accent-light)', color: 'var(--accent-dark)',
              borderRadius: 8, padding: '3px 9px',
            }}>
              {sym} {c}
            </span>
          </div>
          {b.daily ? (
            <BudgetRow
              label={t('dashboard.today')}
              spent={(stats.today || {})[c] || 0}
              limit={b.daily}
              symbol={sym}
              t={t}
            />
          ) : null}
          {b.weekly ? (
            <BudgetRow
              label={t('dashboard.thisWeek')}
              spent={(stats.week || {})[c] || 0}
              limit={b.weekly}
              symbol={sym}
              t={t}
            />
          ) : null}

          {Object.keys(catBudgets).length > 0 && (
            <div style={{
              marginTop: 12, paddingTop: 10,
              borderTop: '1px solid var(--tg-theme-secondary-bg-color)',
            }}>
              {Object.entries(catBudgets).flatMap(([catId, cl]) => {
                const rows = []
                if (cl?.daily) rows.push(
                  <CategoryBudgetRow
                    key={`${catId}-d`} catId={catId} period="daily"
                    spent={todayCats[catId] || 0} limit={cl.daily}
                    symbol={sym} t={t} lang={lang}
                  />
                )
                if (cl?.weekly) rows.push(
                  <CategoryBudgetRow
                    key={`${catId}-w`} catId={catId} period="weekly"
                    spent={weekCats[catId] || 0} limit={cl.weekly}
                    symbol={sym} t={t} lang={lang}
                  />
                )
                return rows
              })}
            </div>
          )}
        </div>
      )
    })

  if (!cards.length) return null
  return (
    <>
      <p style={SECTION_LABEL}>{t('dashboard.budgets')}</p>
      {cards}
    </>
  )
}

const SparkTooltip = ({ active, payload, symbol }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--tg-theme-bg-color)',
      border: '1px solid var(--tg-theme-secondary-bg-color)',
      borderRadius: 8, padding: '6px 10px',
      fontSize: 12,
    }}>
      <p style={{ fontWeight: 500 }}>{payload[0].payload?.label || payload[0].payload?.date}</p>
      <p style={{ color: 'var(--accent)', fontFamily: 'var(--font-mono)' }}>
        {symbol}{Number(payload[0].value).toFixed(2)}
      </p>
    </div>
  )
}

// Defaults to the user's main currency; a compact symbol switcher appears
// only when more than one currency had spend in the last 7 days. The
// tooltip always reflects the selected currency, never a mixed total.
function Sparkline({ byCur, primary, t, locale }) {
  const [picked, setPicked] = useState(null)
  const spendCurs = Object.keys(byCur).filter((c) => byCur[c].some((d) => d.total > 0))
  const ordered = [primary, ...spendCurs.filter((c) => c !== primary)]
    .filter((c) => spendCurs.includes(c))

  if (!ordered.length) return null

  const active = picked && ordered.includes(picked) ? picked : ordered[0]
  const data = (byCur[active] || []).map((d) => ({ ...d, label: dayLabel(d.date, locale) }))

  return (
    <>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        margin: '4px 2px 8px',
      }}>
        <p style={{ ...SECTION_LABEL, margin: 0 }}>{t('dashboard.spendTrend')}</p>
        {ordered.length > 1 && (
          <div style={{ display: 'flex', gap: 6 }}>
            {ordered.map((c) => (
              <button
                key={c}
                type="button"
                className={`chip ${active === c ? 'active' : ''}`}
                style={{ padding: '3px 10px', fontSize: 12 }}
                onClick={() => setPicked(c)}
              >
                {currencySymbol(c)}
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="card" style={{ padding: '10px 8px 4px' }}>
        <ResponsiveContainer width="100%" height={80}>
          <BarChart data={data} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
            <defs>
              <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#6C63FF" />
                <stop offset="100%" stopColor="#3B8BFF" />
              </linearGradient>
            </defs>
            <Tooltip content={<SparkTooltip symbol={currencySymbol(active)} />} cursor={{ fill: 'var(--accent-light)' }} />
            <Bar dataKey="total" fill="url(#sparkGrad)" radius={[4, 4, 0, 0]} maxBarSize={22} animationDuration={600} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </>
  )
}

export default function Dashboard({ user }) {
  const [stats,       setStats]       = useState(null)
  const [lastTx,      setLastTx]      = useState(null)
  const [streak,      setStreak]      = useState(0)
  const [loading,     setLoading]     = useState(true)
  const [showModal,   setShowModal]   = useState(false)
  const [detailOpen,  setDetailOpen]  = useState(false)
  const [deleting,    setDeleting]    = useState(false)
  const [showProfile, setShowProfile] = useState(false)
  const fabCollapsed = useFabCollapse()

  const cur  = user?.currency ?? 'EUR'
  const lang = user?.language ?? 'en'
  const locale = localeFor(lang)
  const t = useTranslation(lang)
  const budgets = user?.budgets ?? {}

  const loadAll = useCallback(() => {
    setLoading(true)
    // Pass the main currency so "top categories" is single-currency and not
    // a meaningless cross-currency sum; multi-currency totals and the per
    // currency sparkline series are unaffected by this filter.
    Promise.all([getStats('week', cur), getExpenses('month')])
      .then(([s, list]) => {
        setStats(s)
        setLastTx(list[0] || null)
        setStreak(computeStreak(list))
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [cur])

  useEffect(() => { loadAll() }, [loadAll])

  const handleExpenseAdded = () => loadAll()

  const handleDeleteLastTx = async (id) => {
    if (!window.confirm(t('history.confirmDelete'))) return
    setDeleting(true)
    try {
      await deleteExpense(id)
      setDetailOpen(false)
      loadAll()
    } catch (e) {
      console.error(e)
    } finally {
      setDeleting(false)
    }
  }

  const greeting = () => {
    const h = new Date().getHours()
    if (h < 6) return t('greeting.night')
    if (h < 12) return t('greeting.morning')
    if (h < 18) return t('greeting.afternoon')
    return t('greeting.evening')
  }

  const todayDate = new Date().toLocaleDateString(locale, {
    weekday: 'long', day: 'numeric', month: 'long',
  })

  const weekCount = stats?.count_week ?? 0
  const monthCount = stats?.count_month ?? 0
  const txWord = (n) => n === 1 ? t('dashboard.transaction') : t('dashboard.transactions')

  const lastTxCat = lastTx ? capCat(lastTx.category) : null

  return (
    <div className="page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <p style={{ fontSize: 14, color: 'var(--tg-theme-hint-color)' }}>{greeting()}</p>
          <h1 style={{ fontSize: 26, fontWeight: 700 }}>{user?.first_name ?? 'there'} 👋</h1>
          <p style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)', marginTop: 4, textTransform: 'capitalize' }}>
            {todayDate}
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          <Avatar
            photoUrl={TG_PHOTO_URL}
            name={user?.first_name}
            size={56}
            onClick={() => setShowProfile(true)}
          />
          {streak > 0 ? (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 4,
              background: 'var(--accent-light)',
              color: 'var(--accent-dark)',
              borderRadius: 999,
              padding: '3px 9px',
              fontSize: 11,
              fontWeight: 600,
              whiteSpace: 'nowrap',
            }} title={`${streak} ${t('dashboard.streak')}`}>
              🔥 {streak} {t('dashboard.streak')}
            </div>
          ) : (
            <div style={{
              fontSize: 10,
              color: 'var(--tg-theme-hint-color)',
              textAlign: 'center',
              maxWidth: 80,
              lineHeight: 1.2,
            }}>
              {t('dashboard.streakNone')}
            </div>
          )}
        </div>
      </div>

      {loading || !stats ? (
        <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 40 }}>
          <div className="spinner" />
        </div>
      ) : (
        <>
          <div className="stat-row">
            <div className="stat-card">
              <p className="stat-label">{t('dashboard.today')}</p>
              <StatValue totals={stats.today} primary={cur} />
              {stats.count_today > 0 && (
                <p className="stat-extra">{stats.count_today} {txWord(stats.count_today)}</p>
              )}
            </div>
            <div className="stat-card">
              <p className="stat-label">{t('dashboard.thisWeek')}</p>
              <StatValue totals={stats.week} primary={cur} />
              {weekCount > 0 && (
                <p className="stat-extra">{weekCount} {txWord(weekCount)}</p>
              )}
            </div>
            <div className="stat-card">
              <p className="stat-label">{t('dashboard.thisMonth')}</p>
              <StatValue totals={stats.month} primary={cur} />
              {monthCount > 0 && (
                <p className="stat-extra">{monthCount} {txWord(monthCount)}</p>
              )}
            </div>
          </div>

          <Budgets budgets={budgets} stats={stats} primary={cur} t={t} lang={lang} />

          {Object.keys(stats.today || {}).length === 0 && (
            <p style={{ fontSize: 13, color: 'var(--success)', textAlign: 'center', margin: '4px 0 12px' }}>
              {t('dashboard.motivateNoToday')}
            </p>
          )}

          <Sparkline
            byCur={stats.daily_by_currency || {}}
            primary={cur}
            t={t}
            locale={locale}
          />

          <p style={{
            fontSize: 11,
            color: 'var(--tg-theme-hint-color)',
            fontStyle: 'italic',
            margin: '4px 4px 12px',
          }}>
            ℹ️ {t('analytics.totalsNote')}
          </p>

          {lastTx && (
            <>
              <p style={SECTION_LABEL}>{t('dashboard.lastTx')}</p>
              <div
                className="card"
                onClick={() => setDetailOpen(true)}
                style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 14, cursor: 'pointer' }}
              >
                <div style={{
                  width: 44, height: 44, borderRadius: 12,
                  background: 'var(--accent-light)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 20, flexShrink: 0,
                }}>
                  {CATEGORY_EMOJI[lastTxCat] ?? '💰'}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ fontSize: 15, fontWeight: 500 }}>{translateCategory(lastTx.category, lang)}</p>
                  {lastTx.description && (
                    <p style={{ fontSize: 12, color: 'var(--tg-theme-hint-color)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {lastTx.description}
                    </p>
                  )}
                  <p style={{ fontSize: 11, color: 'var(--tg-theme-hint-color)', marginTop: 2 }}>
                    {new Date(lastTx.created_at).toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
                <p className="amount" style={{ fontSize: 16, fontWeight: 600 }}>
                  {currencySymbol(lastTx.currency)}{lastTx.amount.toFixed(2)}
                </p>
              </div>
            </>
          )}

          {stats.by_category.length > 0 ? (
            <>
              <p style={SECTION_LABEL}>{t('dashboard.topCategories')}</p>
              <div className="card" style={{ padding: '8px 0' }}>
                {stats.by_category.slice(0, 5).map((item, i) => {
                  const cap = capCat(item.category)
                  const color = CATEGORY_COLORS[cap] ?? '#94A3B8'
                  const emoji = CATEGORY_EMOJI[cap] ?? '💰'
                  const maxTotal = stats.by_category[0].total
                  const pct = (item.total / maxTotal) * 100
                  return (
                    <div key={i} style={{ padding: '10px 16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, alignItems: 'center' }}>
                        <span style={{ fontSize: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontSize: 16 }}>{emoji}</span>
                          {translateCategory(item.category, lang)}
                        </span>
                        <span className="amount" style={{ fontSize: 14, color, fontWeight: 600 }}>
                          {currencySymbol(cur)}{item.total.toFixed(2)}
                        </span>
                      </div>
                      <div style={{ height: 4, borderRadius: 2, background: 'var(--tg-theme-bg-color)' }}>
                        <div style={{ width: `${pct}%`, height: '100%', borderRadius: 2, background: color, transition: 'width 0.5s ease' }} />
                      </div>
                    </div>
                  )
                })}
              </div>
            </>
          ) : !lastTx && (
            <div className="empty">
              <div className="empty-icon">📭</div>
              <p>{t('dashboard.noTx')}</p>
              <button
                className="btn-accent"
                onClick={() => setShowModal(true)}
                style={{ marginTop: 16, width: 'auto', display: 'inline-flex', alignItems: 'center', gap: 6, padding: '10px 24px' }}
              >
                <Plus size={18} /> {t('common.addExpense')}
              </button>
            </div>
          )}
        </>
      )}

      <button
        className={`fab-extended${fabCollapsed ? ' collapsed' : ''}`}
        onClick={() => setShowModal(true)}
        aria-label={t('dashboard.add')}
      >
        <Plus size={20} />
        <span className="fab-label">{t('dashboard.add')}</span>
      </button>

      {showModal && (
        <AddExpenseModal
          user={user}
          onClose={() => setShowModal(false)}
          onAdded={handleExpenseAdded}
        />
      )}

      {detailOpen && lastTx && (
        <ExpenseDetailModal
          expense={lastTx}
          language={lang}
          onClose={() => setDetailOpen(false)}
          onDelete={handleDeleteLastTx}
          deleting={deleting}
        />
      )}

      {showProfile && (
        <UserProfileSheet
          user={user}
          photoUrl={TG_PHOTO_URL}
          onClose={() => setShowProfile(false)}
        />
      )}
    </div>
  )
}
