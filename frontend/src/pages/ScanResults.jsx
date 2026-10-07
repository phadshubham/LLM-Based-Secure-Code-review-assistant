/**
 * Scan Results page – findings table with filters
 */
import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Legend,
} from 'recharts'
import { Filter, Download, RefreshCw, ChevronRight, AlertTriangle } from 'lucide-react'
import { getScan, getScanFindings, downloadPDF, downloadJSON } from '../services/api'
import SeverityBadge from '../components/SeverityBadge'
import ClassificationLabel from '../components/ClassificationLabel'
import ScoreGauge from '../components/ScoreGauge'
import { LoadingPage, Spinner, SkeletonRow } from '../components/LoadingStates'
import toast from 'react-hot-toast'

const SEV_COLORS = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#3b82f6',
  INFO: '#6b7280',
}

const SEVERITIES = ['', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
const TOOLS = ['', 'Semgrep', 'Bandit', 'ESLint', 'SpotBugs', 'Trivy']

export default function ScanResults() {
  const { scanId } = useParams()
  const navigate = useNavigate()
  const [scan, setScan] = useState(null)
  const [findings, setFindings] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [findingsLoading, setFindingsLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState({ severity: '', tool: '' })
  const [showFilters, setShowFilters] = useState(false)
  const [downloading, setDownloading] = useState(null)
  const [polling, setPolling] = useState(false)

  const fetchScan = useCallback(() => {
    return getScan(scanId).then(r => setScan(r.data.scan))
  }, [scanId])

  const fetchFindings = useCallback(() => {
    setFindingsLoading(true)
    return getScanFindings(scanId, {
      ...filters,
      page,
      page_size: 50,
    }).then(r => {
      setFindings(r.data.findings || [])
      setTotal(r.data.total || 0)
    }).finally(() => setFindingsLoading(false))
  }, [scanId, filters, page])

  useEffect(() => {
    Promise.all([fetchScan(), fetchFindings()]).finally(() => setLoading(false))
  }, [fetchScan, fetchFindings])

  // Poll if scan is running
  useEffect(() => {
    if (!scan) return
    if (scan.status !== 'running' && scan.status !== 'pending') return
    setPolling(true)
    const timer = setInterval(() => {
      fetchScan().then(r => {
        const s = r?.data?.scan || scan
        if (s.status === 'completed' || s.status === 'failed') {
          clearInterval(timer)
          setPolling(false)
          fetchFindings()
        }
      })
    }, 3000)
    return () => clearInterval(timer)
  }, [scan?.status])

  const handleDownload = async (format) => {
    setDownloading(format)
    try {
      const resp = format === 'pdf'
        ? await downloadPDF(scanId)
        : await downloadJSON(scanId)
      const url = URL.createObjectURL(new Blob([resp.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `security_report.${format}`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      toast.error('Download failed: ' + (err.message || 'Unknown error'))
    } finally {
      setDownloading(null)
    }
  }

  if (loading) return <LoadingPage message="Loading scan results…" />
  if (!scan) return <div className="p-6 text-dark-400">Scan not found.</div>

  const isRunning = scan.status === 'running' || scan.status === 'pending'

  // Chart data
  const severityData = [
    { name: 'Critical', value: scan.critical_count || 0, fill: SEV_COLORS.CRITICAL },
    { name: 'High', value: scan.high_count || 0, fill: SEV_COLORS.HIGH },
    { name: 'Medium', value: scan.medium_count || 0, fill: SEV_COLORS.MEDIUM },
    { name: 'Low', value: scan.low_count || 0, fill: SEV_COLORS.LOW },
    { name: 'Info', value: scan.info_count || 0, fill: SEV_COLORS.INFO },
  ].filter(d => d.value > 0)

  // Category breakdown from findings
  const catCounts = {}
  findings.forEach(f => {
    const cat = f.category || 'Unknown'
    catCounts[cat] = (catCounts[cat] || 0) + 1
  })
  const catData = Object.entries(catCounts)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 6)

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Scan Results</h1>
          <p className="text-dark-400 text-xs mt-1 font-mono">{scanId}</p>
        </div>
        <div className="flex items-center gap-2">
          {isRunning && (
            <div className="flex items-center gap-2 text-blue-300 text-sm">
              <Spinner size={14} />
              <span>{scan.progress_step || 'Running…'}</span>
            </div>
          )}
          {scan.status === 'completed' && (
            <>
              <button
                id="download-json-btn"
                onClick={() => handleDownload('json')}
                disabled={!!downloading}
                className="btn-secondary text-sm"
              >
                {downloading === 'json' ? <Spinner size={14} /> : <Download size={14} />}
                JSON
              </button>
              <button
                id="download-pdf-btn"
                onClick={() => handleDownload('pdf')}
                disabled={!!downloading}
                className="btn-secondary text-sm"
              >
                {downloading === 'pdf' ? <Spinner size={14} /> : <Download size={14} />}
                PDF
              </button>
            </>
          )}
          <button onClick={() => { fetchScan(); fetchFindings() }} className="btn-secondary text-sm">
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {/* Progress for running scan */}
      {isRunning && (
        <div className="glass-card p-5 border border-blue-800/30">
          <div className="flex items-center gap-3 mb-3">
            <div className="status-dot-yellow" />
            <span className="text-blue-300 font-medium">{scan.progress_step || 'Scanning…'}</span>
          </div>
          <div className="h-1.5 bg-dark-700 rounded-full overflow-hidden">
            <div className="h-full progress-bar rounded-full w-2/3" />
          </div>
        </div>
      )}

      {/* Score + summary */}
      {scan.status === 'completed' && (
        <div className="glass-card p-5">
          <div className="flex items-center gap-8 flex-wrap">
            <div className="flex flex-col items-center">
              <ScoreGauge score={scan.security_score} size={110} />
              <p className="text-xs text-dark-500 mt-2 text-center max-w-28">
                Educational metric — not a certification
              </p>
            </div>
            <div className="flex-1 grid grid-cols-5 gap-3">
              {[
                { label: 'Critical', count: scan.critical_count, color: 'text-red-400 bg-red-950' },
                { label: 'High', count: scan.high_count, color: 'text-orange-400 bg-orange-950' },
                { label: 'Medium', count: scan.medium_count, color: 'text-yellow-400 bg-yellow-950' },
                { label: 'Low', count: scan.low_count, color: 'text-blue-400 bg-blue-950' },
                { label: 'Info', count: scan.info_count, color: 'text-dark-300 bg-dark-800' },
              ].map(({ label, count, color }) => (
                <div key={label} className={`rounded-lg p-3 text-center ${color.split(' ')[1]}`}>
                  <div className={`text-2xl font-bold ${color.split(' ')[0]}`}>{count ?? 0}</div>
                  <div className="text-xs text-dark-400 mt-0.5">{label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      {scan.status === 'completed' && severityData.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="glass-card p-4">
            <h3 className="text-sm font-semibold text-dark-300 mb-3">Severity Distribution</h3>
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie data={severityData} dataKey="value" nameKey="name" outerRadius={65} label>
                  {severityData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
          {catData.length > 0 && (
            <div className="glass-card p-4">
              <h3 className="text-sm font-semibold text-dark-300 mb-3">Findings by Category</h3>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={catData} layout="vertical">
                  <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} />
                  <YAxis type="category" dataKey="name" width={120} tick={{ fill: '#94a3b8', fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  />
                  <Bar dataKey="value" fill="#2563eb" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Filters */}
      <div className="glass-card overflow-hidden">
        <div className="px-5 py-3 border-b border-dark-700/50 flex items-center justify-between">
          <h2 className="font-semibold text-dark-100">
            Findings <span className="text-dark-500 font-normal text-sm">({total})</span>
          </h2>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="btn-secondary text-xs"
          >
            <Filter size={13} /> Filter
          </button>
        </div>

        {showFilters && (
          <div className="px-5 py-3 border-b border-dark-700/30 flex gap-3 flex-wrap">
            <select
              value={filters.severity}
              onChange={e => setFilters(f => ({ ...f, severity: e.target.value }))}
              className="bg-dark-800 border border-dark-600 text-dark-200 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-cyber-500"
            >
              {SEVERITIES.map(s => (
                <option key={s} value={s}>{s || 'All Severities'}</option>
              ))}
            </select>
            <select
              value={filters.tool}
              onChange={e => setFilters(f => ({ ...f, tool: e.target.value }))}
              className="bg-dark-800 border border-dark-600 text-dark-200 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-cyber-500"
            >
              {TOOLS.map(t => (
                <option key={t} value={t}>{t || 'All Scanners'}</option>
              ))}
            </select>
            <button
              onClick={() => setFilters({ severity: '', tool: '' })}
              className="text-xs text-dark-400 hover:text-dark-200"
            >
              Clear
            </button>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-dark-700/30">
                {['Severity', 'Category', 'File', 'Line', 'Scanner', 'Status', 'AI', ''].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-dark-500 uppercase tracking-wider">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {findingsLoading ? (
                [...Array(5)].map((_, i) => <SkeletonRow key={i} />)
              ) : findings.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-12 text-dark-500">
                    {isRunning ? (
                      <div className="flex flex-col items-center gap-2">
                        <Spinner size={24} />
                        <span>Scanning in progress…</span>
                      </div>
                    ) : (
                      <div>
                        <AlertTriangle size={24} className="mx-auto mb-2 text-dark-600" />
                        <span>No findings match the current filters</span>
                      </div>
                    )}
                  </td>
                </tr>
              ) : (
                findings.map(f => (
                  <tr
                    key={f.finding_id}
                    className="border-b border-dark-700/20 hover:bg-dark-800/50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/findings/${f.finding_id}`)}
                  >
                    <td className="px-4 py-3"><SeverityBadge severity={f.severity} /></td>
                    <td className="px-4 py-3 text-dark-200 text-xs max-w-32 truncate">{f.category}</td>
                    <td className="px-4 py-3 text-dark-300 text-xs font-mono max-w-40 truncate" title={f.file}>
                      {f.file.split(/[\\/]/).slice(-2).join('/')}
                    </td>
                    <td className="px-4 py-3 text-dark-400 text-xs font-mono">{f.line ?? '–'}</td>
                    <td className="px-4 py-3 text-dark-300 text-xs">{f.tool}</td>
                    <td className="px-4 py-3">
                      {f.verified ? (
                        <span className="text-xs text-emerald-400">✓ Verified</span>
                      ) : (
                        <span className="text-xs text-purple-400">AI Obs.</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {f.ai_review ? (
                        <span className="text-xs text-cyber-400">✓ AI</span>
                      ) : (
                        <span className="text-xs text-dark-600">–</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <ChevronRight size={13} className="text-dark-600" />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {total > 50 && (
          <div className="px-5 py-3 border-t border-dark-700/30 flex items-center justify-between">
            <span className="text-xs text-dark-500">Showing {findings.length} of {total}</span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-secondary text-xs"
              >
                Previous
              </button>
              <span className="text-xs text-dark-400 py-2">Page {page}</span>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={findings.length < 50}
                className="btn-secondary text-xs"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Disclaimer */}
      <div className="glass-card p-3 border border-amber-800/20 bg-amber-950/5">
        <p className="text-xs text-amber-400/70">
          ⚠️ This security score is an educational/project-defined metric and is not an industry security certification.
        </p>
      </div>
    </div>
  )
}
