import { useState, useRef, useEffect } from 'react'
import { ChevronLeft, ChevronRight, Calendar } from 'lucide-react'
import { monthNames, weekdayNames, localeFor } from '../i18n.js'

const pad = (n) => String(n).padStart(2, '0')
const toYMD = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`

const parseYMD = (s) => {
  if (!s || typeof s !== 'string') return null
  const [y, m, d] = s.split('-').map(Number)
  if (!y || !m || !d) return null
  return new Date(y, m - 1, d)
}

const sameDay = (a, b) =>
  a.getFullYear() === b.getFullYear() &&
  a.getMonth() === b.getMonth() &&
  a.getDate() === b.getDate()

export default function DatePicker({ value, onChange, language, maxDate }) {
  const [open, setOpen] = useState(false)
  const [slideDir, setSlideDir] = useState(0)
  const ref = useRef(null)

  const selected = parseYMD(value)
  const base = selected ?? new Date()
  const [view, setView] = useState({ y: base.getFullYear(), m: base.getMonth() })

  const months = monthNames(language)
  const weekdays = weekdayNames(language)

  const max = parseYMD(maxDate)
  if (max) max.setHours(23, 59, 59, 999)

  useEffect(() => {
    if (!open) return
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  useEffect(() => {
    const d = parseYMD(value)
    if (d) setView({ y: d.getFullYear(), m: d.getMonth() })
  }, [value])

  const goMonth = (delta) => {
    setSlideDir(delta)
    setView((v) => {
      let m = v.m + delta
      let y = v.y
      if (m < 0) { m = 11; y -= 1 }
      if (m > 11) { m = 0; y += 1 }
      return { y, m }
    })
  }

  // 6×7 grid starting on the Monday on/before the 1st of the month.
  const firstWeekday = (new Date(view.y, view.m, 1).getDay() + 6) % 7
  const gridStart = new Date(view.y, view.m, 1 - firstWeekday)
  const days = Array.from({ length: 42 }, (_, i) => {
    const d = new Date(gridStart)
    d.setDate(gridStart.getDate() + i)
    return d
  })

  const today = new Date()

  const pick = (d) => {
    if (max && d > max) return
    onChange(toYMD(d))
    setOpen(false)
  }

  const label = selected
    ? selected.toLocaleDateString(localeFor(language), {
        day: 'numeric', month: 'long', year: 'numeric',
      })
    : ''

  return (
    <div className="dp-wrap" ref={ref}>
      <button
        type="button"
        className="dp-input"
        onClick={() => setOpen((o) => !o)}
      >
        <span className={label ? '' : 'dp-placeholder'}>{label || '—'}</span>
        <Calendar size={18} />
      </button>

      {open && (
        <div className="dp-pop">
          <div className="dp-head">
            <button type="button" className="dp-nav" onClick={() => goMonth(-1)} aria-label="Previous month">
              <ChevronLeft size={18} />
            </button>
            <div className="dp-title">{months[view.m]} {view.y}</div>
            <button type="button" className="dp-nav" onClick={() => goMonth(1)} aria-label="Next month">
              <ChevronRight size={18} />
            </button>
          </div>

          <div className="dp-weekdays">
            {weekdays.map((w) => (
              <div key={w} className="dp-weekday">{w}</div>
            ))}
          </div>

          <div className="dp-grid-clip">
            <div
              className="dp-grid"
              key={`${view.y}-${view.m}`}
              data-dir={slideDir}
            >
              {days.map((d, i) => {
                const other = d.getMonth() !== view.m
                const disabled = max && d > max
                const isToday = sameDay(d, today)
                const isSel = selected && sameDay(d, selected)
                return (
                  <button
                    key={i}
                    type="button"
                    disabled={disabled}
                    onClick={() => pick(d)}
                    className={
                      'dp-day' +
                      (other ? ' dp-other' : '') +
                      (isToday ? ' dp-today' : '') +
                      (isSel ? ' dp-sel' : '') +
                      (disabled ? ' dp-disabled' : '')
                    }
                  >
                    {d.getDate()}
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
