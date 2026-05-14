import { useState, useCallback } from 'react'

export default function BottomSheet({ onClose, children }) {
  const [closing, setClosing] = useState(false)

  const close = useCallback(() => {
    if (closing) return
    setClosing(true)
    setTimeout(onClose, 280)
  }, [closing, onClose])

  return (
    <div
      className={`modal-overlay ${closing ? 'closing' : ''}`}
      onClick={(e) => e.target === e.currentTarget && close()}
    >
      <div className={`modal-sheet ${closing ? 'closing' : ''}`}>
        {typeof children === 'function' ? children(close) : children}
      </div>
    </div>
  )
}
