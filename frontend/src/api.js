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

export const getExpenses    = (period = 'week')    => request('GET', `/api/expenses?period=${period}`)
export const createExpense  = (data)               => request('POST', '/api/expenses', data)
export const updateExpense  = (id, data)           => request('PUT', `/api/expenses/${id}`, data)
export const deleteExpense  = (id)                 => request('DELETE', `/api/expenses/${id}`)

export const getStats = (period = 'week') => request('GET', `/api/stats?period=${period}`)

export const getUser    = ()     => request('GET', '/api/user')
export const updateUser = (data) => request('PUT', '/api/user', data)
