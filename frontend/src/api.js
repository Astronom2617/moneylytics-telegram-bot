/**
 * Все запросы к FastAPI бэкенду — через этот модуль.
 * Токен хранится в памяти (не localStorage — TMA чистит стейт при закрытии).
 */

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

// Auth
export const authUser  = (initData) => request('POST', '/api/auth', { initData })

// Расходы
export const getExpenses    = (period = 'week')    => request('GET', `/api/expenses?period=${period}`)
export const createExpense  = (data)               => request('POST', '/api/expenses', data)
export const deleteExpense  = (id)                 => request('DELETE', `/api/expenses/${id}`)
export const updateExpense = (id, data) => request('PUT', `/api/expenses/${id}`, data)

// Статистика
export const getStats = (period = 'week') => request('GET', `/api/stats?period=${period}`)

// Пользователь
export const getUser    = ()     => request('GET', '/api/user')
export const updateUser = (data) => request('PUT', '/api/user', data)
