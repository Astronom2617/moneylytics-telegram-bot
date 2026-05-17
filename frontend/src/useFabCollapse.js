import { useEffect, useRef, useState } from 'react'

// The FAB collapses to a compact icon while the user scrolls down a long
// list — so it stops covering rows on short screens — and expands back when
// they scroll up or reach the top. Scrolling lives on `.page-content`
// (the window itself never scrolls), so the listener attaches there.
export function useFabCollapse(threshold = 6) {
  const [collapsed, setCollapsed] = useState(false)
  const lastY = useRef(0)

  useEffect(() => {
    const el = document.querySelector('.page-content')
    if (!el) return
    lastY.current = el.scrollTop

    const onScroll = () => {
      const y = el.scrollTop
      if (y <= 4) {
        setCollapsed(false)
      } else if (y - lastY.current > threshold) {
        setCollapsed(true)
      } else if (lastY.current - y > threshold) {
        setCollapsed(false)
      }
      lastY.current = y
    }

    el.addEventListener('scroll', onScroll, { passive: true })
    return () => el.removeEventListener('scroll', onScroll)
  }, [threshold])

  return collapsed
}
