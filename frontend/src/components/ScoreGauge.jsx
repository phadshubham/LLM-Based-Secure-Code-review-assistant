/**
 * Circular security score gauge
 */
export default function ScoreGauge({ score, size = 120 }) {
  const s = Math.round(score ?? 0)
  const radius = (size - 16) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (s / 100) * circumference

  const color =
    s >= 80 ? '#22c55e' :
    s >= 60 ? '#f59e0b' :
    s >= 40 ? '#f97316' :
    '#ef4444'

  const label =
    s >= 80 ? 'Good' :
    s >= 60 ? 'Fair' :
    s >= 40 ? 'Poor' :
    'Critical'

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#1e293b"
          strokeWidth={8}
        />
        {/* Progress */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={8}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: 'stroke-dashoffset 0.8s ease' }}
        />
        {/* Score text */}
        <text
          x={size / 2}
          y={size / 2 - 4}
          textAnchor="middle"
          dominantBaseline="middle"
          fill={color}
          fontSize={size * 0.22}
          fontWeight="bold"
          fontFamily="Inter, sans-serif"
        >
          {s}
        </text>
        <text
          x={size / 2}
          y={size / 2 + size * 0.16}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="#64748b"
          fontSize={size * 0.12}
          fontFamily="Inter, sans-serif"
        >
          / 100
        </text>
      </svg>
      <span className="text-xs font-medium" style={{ color }}>{label}</span>
    </div>
  )
}
