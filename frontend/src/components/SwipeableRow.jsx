import { useRef, useState } from 'react'
import { Trash2 } from 'lucide-react'

// Touch-driven swipe-left container. The child stays in the document flow;
// only the inner .swipe-row-content is translated. When the user releases
// past `threshold`, we call onDelete — the parent is expected to remove the
// row from state right away (optimistic delete + undo toast).
//
// We intentionally don't trigger on a brief swipe that doesn't reach the
// threshold: we snap back. That avoids accidental deletes on flicks.

const ACTION_W = 88        // matches .swipe-row-action width
// Delete fires only if the user swipes PAST the full reveal of the action
// button. A swipe that just exposes "Delete" but no further snaps back —
// that lets the user peek at what's underneath without committing.
const TRIGGER_OVERSHOOT = 40
const DELETE_THRESHOLD = ACTION_W + TRIGGER_OVERSHOOT  // 128px
const MAX_SWIPE = ACTION_W + 140                       // rubber-band ceiling
const ANGLE_LIMIT = 1.2    // |dx/dy| must exceed this to claim horizontal

export default function SwipeableRow({ children, onDelete, label = 'Delete' }) {
  const ref = useRef(null)
  const [dx, setDx] = useState(0)
  const [swiping, setSwiping] = useState(false)
  const start = useRef({ x: 0, y: 0, decided: false, claimed: false })

  const onTouchStart = (e) => {
    const t = e.touches[0]
    start.current = { x: t.clientX, y: t.clientY, decided: false, claimed: false }
  }

  const onTouchMove = (e) => {
    const t = e.touches[0]
    const rawDx = t.clientX - start.current.x
    const dy = t.clientY - start.current.y
    if (!start.current.decided) {
      // Wait until we've moved 8px in some direction before deciding whether
      // this is a horizontal swipe (ours) or a vertical scroll (let it pass).
      const dist = Math.hypot(rawDx, dy)
      if (dist < 8) return
      start.current.decided = true
      start.current.claimed = Math.abs(rawDx) > Math.abs(dy) * ANGLE_LIMIT
      if (start.current.claimed) setSwiping(true)
    }
    if (!start.current.claimed) return
    // Left-swipe only. Past the action width we apply rubber-band resistance
    // so it's clear you're "stretching" the row beyond the open position,
    // and the row can't be dragged off-screen entirely.
    let next
    if (rawDx >= 0) {
      next = 0
    } else if (rawDx >= -ACTION_W) {
      next = rawDx
    } else {
      const overshoot = -rawDx - ACTION_W
      // Resistance grows with distance: at MAX_SWIPE the function saturates.
      const damped = (MAX_SWIPE - ACTION_W) * (1 - Math.exp(-overshoot / 60))
      next = -ACTION_W - damped
    }
    setDx(next)
  }

  const onTouchEnd = () => {
    setSwiping(false)
    if (!start.current.claimed) return
    // Only fire delete when the user has clearly committed — past the full
    // action reveal plus a little overshoot. Anything short snaps back to
    // closed, so a curious "peek" swipe doesn't accidentally delete.
    if (Math.abs(dx) >= DELETE_THRESHOLD) {
      // Slide further off before the row unmounts; parent removes us after.
      setDx(-MAX_SWIPE)
      requestAnimationFrame(() => onDelete?.())
    } else {
      setDx(0)
    }
  }

  return (
    <div className="swipe-row" ref={ref}>
      <div className="swipe-row-action" aria-hidden="true">
        <Trash2 size={18} style={{ marginRight: 6 }} />
        {label}
      </div>
      <div
        className={`swipe-row-content${swiping ? ' swiping' : ''}`}
        style={{ transform: `translateX(${dx}px)` }}
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
        onTouchCancel={onTouchEnd}
      >
        {children}
      </div>
    </div>
  )
}
