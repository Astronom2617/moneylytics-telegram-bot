import { LayoutDashboard, History, BarChart2, Settings } from 'lucide-react'
import { useTranslation } from '../i18n.js'

const TABS = [
  { id: 'dashboard', tKey: 'nav.home',      Icon: LayoutDashboard },
  { id: 'history',   tKey: 'nav.history',   Icon: History },
  { id: 'analytics', tKey: 'nav.analytics', Icon: BarChart2 },
  { id: 'settings',  tKey: 'nav.settings',  Icon: Settings },
]

const styles = {
  nav: {
    position: 'fixed',
    bottom: 0,
    left: 0,
    right: 0,
    height: 'calc(60px + env(safe-area-inset-bottom, 0px))',
    background: 'var(--tg-theme-bg-color)',
    borderTop: '1px solid var(--tg-theme-secondary-bg-color)',
    display: 'flex',
    alignItems: 'flex-start',
    paddingTop: 6,
    zIndex: 200,
  },
  tab: (active) => ({
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 3,
    padding: '6px 0',
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    color: active ? 'var(--accent)' : 'var(--tg-theme-hint-color)',
    transition: 'color 0.15s',
  }),
  label: (active) => ({
    fontSize: 10,
    fontFamily: 'var(--font-body)',
    fontWeight: active ? 600 : 400,
    letterSpacing: '0.2px',
  }),
}

export default function BottomNav({ page, setPage, language }) {
  const t = useTranslation(language)
  return (
    <nav style={styles.nav}>
      {TABS.map(({ id, tKey, Icon }) => {
        const active = page === id
        return (
          <button key={id} style={styles.tab(active)} onClick={() => setPage(id)}>
            <Icon size={22} strokeWidth={active ? 2.2 : 1.8} />
            <span style={styles.label(active)}>{t(tKey)}</span>
          </button>
        )
      })}
    </nav>
  )
}
