import type { SessionSummary } from '../types'

interface SummaryViewProps {
  summary: SessionSummary
  onBackHome: () => void
}

export function SummaryView({ summary, onBackHome }: SummaryViewProps) {
  const breakdown = Object.entries(summary.habit_breakdown)

  return (
    <div className="view summary-view">
      <header className="view-header">
        <h1>セッションサマリー</h1>
      </header>

      <section className="card">
        <h2 className="summary-goal">{summary.goal}</h2>
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-value">{summary.focused_minutes}分</div>
            <div className="metric-label">集中時間</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{summary.habit_detected}</div>
            <div className="metric-label">サボり検知</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{summary.interventions}</div>
            <div className="metric-label">介入回数</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{summary.returned_count}</div>
            <div className="metric-label">介入後の復帰</div>
          </div>
        </div>
      </section>

      <section className="card">
        <h3>悪習慣別の検知回数</h3>
        {breakdown.length > 0 ? (
          <ul className="breakdown-list">
            {breakdown.map(([label, count]) => (
              <li key={label}>
                <span className="habit-label">{label}</span>
                <span className="breakdown-count">{count}回</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">悪習慣は検知されませんでした。お見事です！</p>
        )}
      </section>

      <button type="button" className="btn btn-primary btn-large" onClick={onBackHome}>
        ホームに戻る
      </button>
    </div>
  )
}
