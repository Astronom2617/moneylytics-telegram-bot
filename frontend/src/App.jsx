import { useState, useEffect } from 'react'
import Dashboard     from './pages/Dashboard.jsx'
import History       from './pages/History.jsx'
import Analytics     from './pages/Analytics.jsx'
import Settings      from './pages/Settings.jsx'
import Subscriptions from './pages/Subscriptions.jsx'
import BottomNav  from './components/BottomNav.jsx'
import { authUser, setToken } from './api.js'

const tg = window.Telegram?.WebApp

export default function App() {
  const [page, setPage]   = useState('dashboard')
  const [user, setUser]   = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (tg) {
      tg.ready()
      tg.expand()
    }

    const initData = tg?.initData ?? ''

    authUser(initData)
      .then(({ token, user }) => {
        setToken(token)
        setUser(user)
        setLoading(false)
      })
      .catch((err) => {
        // Fall back to a mock user when running locally outside Telegram
        if (import.meta.env.DEV) {
          console.warn('Auth failed in dev mode, using mock user:', err.message)
          setToken('dev-token')
          setUser({
            id: 0,
            first_name: 'Dev',
            currency: 'EUR',
            language: 'en',
            budgets: { EUR: { daily: 30, weekly: 150 } },
          })
          setLoading(false)
        } else {
          setError('Could not authorize. Try opening the app again.')
          setLoading(false)
        }
      })
  }, [])

  if (loading) return (
    <div className="loading">
      <div className="spinner" />
    </div>
  )

  if (error) return (
    <div className="loading" style={{ flexDirection: 'column', gap: 12, textAlign: 'center', padding: 24 }}>
      <span style={{ fontSize: 32 }}>😕</span>
      <p style={{ color: 'var(--tg-theme-hint-color)', fontSize: 14 }}>{error}</p>
    </div>
  )

  const pages = {
    dashboard:     <Dashboard     user={user} />,
    history:       <History       user={user} />,
    subscriptions: <Subscriptions user={user} />,
    analytics:     <Analytics     user={user} />,
    settings:      <Settings      user={user} setUser={setUser} />,
  }

  return (
    <div className="app">
      <div className="page-content">
        {pages[page]}
      </div>
      <BottomNav page={page} setPage={setPage} language={user?.language} />
    </div>
  )
}
