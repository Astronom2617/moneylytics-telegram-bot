// Thin wrapper around Telegram.WebApp.HapticFeedback. Every call is wrapped
// in try/catch + a feature check so the app still works in a regular browser
// (dev mode) or in a Telegram client that doesn't support haptics — it just
// becomes a no-op there.

const hf = () => {
  try { return window.Telegram?.WebApp?.HapticFeedback ?? null }
  catch { return null }
}

// Light = subtle tap (FAB, tabs, modal open/close). Medium = decisive action
// (save, add, toggle). Heavy = destructive (delete confirm).
export function impact(strength = 'light') {
  const api = hf()
  if (!api?.impactOccurred) return
  try { api.impactOccurred(strength) } catch { /* ignore */ }
}

// success = green flash equivalent (saved, created). warning = recoverable
// issue (validation). error = failure (network, server).
export function notify(kind = 'success') {
  const api = hf()
  if (!api?.notificationOccurred) return
  try { api.notificationOccurred(kind) } catch { /* ignore */ }
}

// For chip/tab switches where you want the lightest possible feedback.
export function selection() {
  const api = hf()
  if (!api?.selectionChanged) return
  try { api.selectionChanged() } catch { /* ignore */ }
}
