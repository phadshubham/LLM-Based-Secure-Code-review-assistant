/**
 * Severity badge component
 */
export default function SeverityBadge({ severity }) {
  const classes = {
    CRITICAL: 'badge-critical',
    HIGH: 'badge-high',
    MEDIUM: 'badge-medium',
    LOW: 'badge-low',
    INFO: 'badge-info',
  }

  const dots = {
    CRITICAL: '🔴',
    HIGH: '🟠',
    MEDIUM: '🟡',
    LOW: '🔵',
    INFO: '⚪',
  }

  const cls = classes[severity?.toUpperCase()] || 'badge-info'
  const dot = dots[severity?.toUpperCase()] || '⚪'

  return (
    <span className={cls}>
      <span>{dot}</span>
      {severity?.toUpperCase() || 'INFO'}
    </span>
  )
}
