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
const THRESHOLD = 60       // px past which release = delete
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
    // Only allow left-swipe; clamp right-swipe at 0 and a bit past action width.
    const next = Math.max(-ACTION_W - 24, Math.min(0, rawDx))
    setDx(next)
  }

  const onTouchEnd = () => {
    setSwiping(false)
    if (!start.current.claimed) return
    if (Math.abs(dx) >= THRESHOLD) {
      // Slide the row fully off before unmounting feels nicer than an instant
      // disappearance; the parent removes us after onDelete runs.
      setDx(-ACTION_W - 80)
      // Defer the callback so the slide-out frame has a chance to paint.
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
