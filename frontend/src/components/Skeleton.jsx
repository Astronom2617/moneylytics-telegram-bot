// Primitive skeleton blocks. Compose them inline at the call site — that way
// each loading view mirrors the shape of the content it's standing in for,
// which is the whole point (perceived speed > generic shimmer).

export const SkLine = ({ width = '100%', height, style }) => (
  <span
    className="sk sk-line"
    style={{ width, ...(height ? { height } : null), ...style }}
  />
)

export const SkCircle = ({ size = 40, style }) => (
  <span
    className="sk sk-circle"
    style={{ width: size, height: size, ...style }}
  />
)

// Stat-card placeholder used on Dashboard's three top cards.
export const SkStatCard = () => (
  <div className="stat-card">
    <span className="sk sk-line-sm" style={{ width: 50, marginBottom: 10 }} />
    <span className="sk sk-line-lg" style={{ width: 80, marginBottom: 6 }} />
    <span className="sk sk-line-sm" style={{ width: 60 }} />
  </div>
)

// A row of (icon + two lines of text + amount) — the shape every list page
// (History, Subscriptions, last-tx card) shows.
export const SkExpenseRow = ({ withDivider = false }) => (
  <>
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12,
      padding: '12px 16px',
    }}>
      <SkCircle size={40} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <SkLine width="40%" height={13} style={{ marginBottom: 6 }} />
        <SkLine width="60%" height={11} />
      </div>
      <SkLine width={64} height={14} />
    </div>
    {withDivider && (
      <div style={{ height: 1, background: 'var(--tg-theme-bg-color)', marginLeft: 68 }} />
    )}
  </>
)

// Whole-page placeholders: drop these into the `if (loading)` branch.

export function DashboardSkeleton() {
  return (
    <>
      <div className="stat-row">
        <SkStatCard /><SkStatCard /><SkStatCard />
      </div>
      <div className="sk-card">
        <SkLine width="40%" height={14} style={{ marginBottom: 14 }} />
        <SkLine width="100%" height={8} style={{ marginBottom: 8 }} />
        <SkLine width="100%" height={8} />
      </div>
      <div className="sk-card" style={{ padding: 0 }}>
        <SkExpenseRow withDivider />
        <SkExpenseRow withDivider />
        <SkExpenseRow />
      </div>
    </>
  )
}

export function ListSkeleton({ rows = 6 }) {
  return (
    <div className="sk-card" style={{ padding: 0 }}>
      {Array.from({ length: rows }).map((_, i) => (
        <SkExpenseRow key={i} withDivider={i < rows - 1} />
      ))}
    </div>
  )
}

export function AnalyticsSkeleton() {
  return (
    <>
      <div className="sk-card" style={{ display: 'flex', gap: 12 }}>
        {[0, 1, 2].map((i) => (
          <div key={i} style={{ flex: 1, textAlign: 'center' }}>
            <SkLine width="50%" height={10} style={{ marginBottom: 8, marginLeft: 'auto', marginRight: 'auto' }} />
            <SkLine width="70%" height={14} style={{ marginLeft: 'auto', marginRight: 'auto' }} />
          </div>
        ))}
      </div>
      <div className="sk-card" style={{ height: 260 }}>
        <SkCircle size={170} style={{ margin: '20px auto', display: 'block' }} />
      </div>
      <div className="sk-card" style={{ height: 190 }} />
    </>
  )
}
