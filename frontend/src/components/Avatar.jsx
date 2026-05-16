import { useState } from 'react'

export default function Avatar({ photoUrl, name, size = 40, onClick }) {
  const [failed, setFailed] = useState(false)
  const letter = (name?.trim()?.[0] ?? '?').toUpperCase()
  const clickable = typeof onClick === 'function'

  const base = {
    width: size,
    height: size,
    borderRadius: '50%',
    flexShrink: 0,
    overflow: 'hidden',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'var(--accent-gradient, linear-gradient(135deg, #8B5CF6 0%, #3B82F6 100%))',
    color: '#fff',
    fontWeight: 700,
    fontSize: Math.round(size * 0.42),
    boxShadow: 'var(--shadow-accent)',
    border: 'none',
    padding: 0,
    cursor: clickable ? 'pointer' : 'default',
    userSelect: 'none',
  }

  const inner = photoUrl && !failed ? (
    <img
      src={photoUrl}
      alt=""
      onError={() => setFailed(true)}
      style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
    />
  ) : letter

  if (clickable) {
    return (
      <button type="button" onClick={onClick} aria-label="Profile" style={base}>
        {inner}
      </button>
    )
  }

  return <div style={base}>{inner}</div>
}
