import { useEffect, useState } from 'react'

// Lightweight singleton toast manager. No context provider — anyone can call
// `showToast({ message, action })` and the <ToastHost /> mounted once in
// App.jsx picks it up. We chose a singleton over context because toasts are
// rarely concurrent and a global queue keeps usage trivial.

let _listeners = new Set()
let _current = null
let _hideTimer = null
let _idCounter = 0

function clearTimer() {
  if (_hideTimer) {
    clearTimeout(_hideTimer)
    _hideTimer = null
  }
}

function emit() {
  for (const l of _listeners) l(_current)
}

/**
 * @param {object} opts
 * @param {string} opts.message    — main text
 * @param {string} [opts.actionLabel] — label of the right-hand button
 * @param {function} [opts.onAction]  — called when the user taps the action
 * @param {number} [opts.duration=4000] — ms before auto-hide; 0 = sticky
 */
export function showToast({ message, actionLabel, onAction, duration = 4000 }) {
  clearTimer()
  _current = {
    id: ++_idCounter,
    message,
    actionLabel,
    onAction,
  }
  emit()
  if (duration > 0) {
    _hideTimer = setTimeout(() => { _current = null; emit() }, duration)
  }
  return _current.id
}

export function hideToast() {
  clearTimer()
  _current = null
  emit()
}

export function ToastHost() {
  const [toast, setToast] = useState(_current)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const listener = (t) => setToast(t)
    _listeners.add(listener)
    return () => _listeners.delete(listener)
  }, [])

  // Two-step mount/unmount so the CSS transition can play both ways.
  useEffect(() => {
    if (toast) {
      // tick after mount so the .shown class transition kicks in
      const id = requestAnimationFrame(() => setVisible(true))
      return () => cancelAnimationFrame(id)
    }
    setVisible(false)
  }, [toast])

  if (!toast) return null
  return (
    <div className={`toast${visible ? ' shown' : ''}`}>
      <span>{toast.message}</span>
      {toast.actionLabel && (
        <button
          type="button"
          className="toast-action"
          onClick={() => {
            const cb = toast.onAction
            hideToast()
            if (cb) cb()
          }}
        >
          {toast.actionLabel}
        </button>
      )}
    </div>
  )
}
