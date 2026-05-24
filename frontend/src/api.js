// Token is held in memory rather than localStorage — Telegram Mini Apps
// wipe storage when the app is closed, so persisting it buys nothing.
let _token = null

export const setToken = (t) => { _token = t }

const request = async (method, path, body = undefined) => {
  const headers = { 'Content-Type': 'application/json' }
  if (_token) headers['Authorization'] = `Bearer ${_token}`

  const res = await fetch(path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || `HTTP ${res.status}`)
  }
  return res.json()
}

export const authUser  = (initData) => request('POST', '/api/auth', { initData })

const rangeQS = (range) => {
  if (!range || !range.from || !range.to) return ''
  return `&from=${encodeURIComponent(range.from)}&to=${encodeURIComponent(range.to)}`
}

export const getExpenses    = (period = 'week', range)    => request('GET', `/api/expenses?period=${period}${rangeQS(range)}`)
export const createExpense  = (data)               => request('POST', '/api/expenses', data)
export const updateExpense  = (id, data)           => request('PUT', `/api/expenses/${id}`, data)
export const deleteExpense  = (id)                 => request('DELETE', `/api/expenses/${id}`)

export const getStats        = (period = 'week', currency, range) =>
  request('GET', `/api/stats?period=${period}${currency ? `&currency=${encodeURIComponent(currency)}` : ''}${rangeQS(range)}`)
export const getAlltimeStats = ()                => request('GET', '/api/stats/alltime')

export const exportCSV = async () => {
  const headers = {}
  if (_token) headers['Authorization'] = `Bearer ${_token}`
  const res = await fetch('/api/expenses/export', { headers })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const blob = await res.blob()
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = 'moneylytics_export.csv'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export const getUser    = ()     => request('GET', '/api/user')
export const updateUser = (data) => request('PUT', '/api/user', data)

export const setupMono     = (token) => request('POST', '/api/mono/setup', { token })
export const removeMono    = ()      => request('DELETE', '/api/mono/setup')
export const getMonoStatus = ()      => request('GET', '/api/mono/status')

export const getSubscriptions   = ()         => request('GET', '/api/subscriptions')
export const createSubscription = (data)     => request('POST', '/api/subscriptions', data)
export const updateSubscription = (id, data) => request('PUT', `/api/subscriptions/${id}`, data)
export const deleteSubscription = (id)       => request('DELETE', `/api/subscriptions/${id}`)
