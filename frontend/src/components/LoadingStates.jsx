/**
 * Loading spinner and skeleton components
 */

export function Spinner({ size = 20, className = '' }) {
  return (
    <svg
      className={`animate-spin text-cyber-400 ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  )
}

export function SkeletonCard() {
  return (
    <div className="glass-card p-5 animate-pulse">
      <div className="h-4 bg-dark-700 rounded w-1/3 mb-3" />
      <div className="h-8 bg-dark-700 rounded w-1/2 mb-2" />
      <div className="h-3 bg-dark-800 rounded w-2/3" />
    </div>
  )
}

export function SkeletonRow() {
  return (
    <tr className="border-b border-dark-700/30 animate-pulse">
      {[...Array(6)].map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 bg-dark-700 rounded" style={{ width: `${60 + i * 10}%` }} />
        </td>
      ))}
    </tr>
  )
}

export function LoadingPage({ message = 'Loading…' }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-4">
      <Spinner size={32} />
      <p className="text-dark-400 text-sm">{message}</p>
    </div>
  )
}
