/**
 * Project Detail page – shows project info and allows triggering scans
 */
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Play, Clock, ChevronRight, Github, Archive, Code } from 'lucide-react'
import { getProject, getProjectHistory, triggerScan } from '../services/api'
import { LoadingPage, Spinner } from '../components/LoadingStates'
import ScoreGauge from '../components/ScoreGauge'

function ScanHistoryRow({ scan, index }) {
  const navigate = useNavigate()
  const score = Math.round(scan.security_score ?? 0)
  return (
    <div
      className="flex items-center gap-4 p-4 rounded-lg border border-dark-700/30 hover:bg-dark-800/50 cursor-pointer transition-all"
      onClick={() => navigate(`/scans/${scan.scan_id}`)}
    >
      <div className="text-sm text-dark-500 w-8 font-mono">#{index + 1}</div>
      <ScoreGauge score={score} size={60} />
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
            scan.status === 'completed' ? 'bg-emerald-950 text-emerald-300' :
            scan.status === 'running' ? 'bg-blue-950 text-blue-300 animate-pulse' :
            scan.status === 'failed' ? 'bg-red-950 text-red-300' :
            'bg-dark-700 text-dark-400'
          }`}>
            {scan.status}
          </span>
          {scan.status === 'running' && <Spinner size={12} />}
        </div>
        <div className="text-xs text-dark-400">
          {scan.total_findings ?? 0} findings •{' '}
          <span className="text-red-400">{scan.critical_count ?? 0} critical</span>,{' '}
          <span className="text-orange-400">{scan.high_count ?? 0} high</span>,{' '}
          <span className="text-yellow-400">{scan.medium_count ?? 0} medium</span>
        </div>
        <div className="text-xs text-dark-500 mt-0.5">
          {scan.started_at ? new Date(scan.started_at).toLocaleString() : ''}
        </div>
      </div>
      <ChevronRight size={16} className="text-dark-500" />
    </div>
  )
}

export default function ProjectDetail() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const [project, setProject] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [scanning, setScanning] = useState(false)

  useEffect(() => {
    Promise.all([
      getProject(projectId),
      getProjectHistory(projectId),
    ]).then(([pResp, hResp]) => {
      setProject(pResp.data.project)
      setHistory(hResp.data.scans || [])
    }).finally(() => setLoading(false))
  }, [projectId])

  // Poll if a scan is running
  useEffect(() => {
    const running = history.some(s => s.status === 'running' || s.status === 'pending')
    if (!running) return
    const timer = setInterval(() => {
      getProjectHistory(projectId).then(r => {
        const scans = r.data.scans || []
        setHistory(scans)
        const stillRunning = scans.some(s => s.status === 'running' || s.status === 'pending')
        if (!stillRunning) {
          setScanning(false)
          clearInterval(timer)
          toast.success('Scan completed!')
        }
      })
    }, 3000)
    return () => clearInterval(timer)
  }, [history, projectId])

  const handleScan = async () => {
    setScanning(true)
    try {
      await triggerScan(projectId)
      toast.success('Scan started!')
      // Refresh history
      const hResp = await getProjectHistory(projectId)
      setHistory(hResp.data.scans || [])
    } catch {
      setScanning(false)
    }
  }

  if (loading) return <LoadingPage message="Loading project…" />
  if (!project) return <div className="p-6 text-dark-400">Project not found.</div>

  const langs = project.language || []
  const latestScan = history[history.length - 1]

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            {project.source_type === 'github' ? (
              <Github size={16} className="text-dark-400" />
            ) : (
              <Archive size={16} className="text-dark-400" />
            )}
            <span className="text-xs text-dark-500 uppercase tracking-wider">
              {project.source_type === 'github' ? 'GitHub Repository' : 'ZIP Upload'}
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white">{project.name}</h1>
          {project.repository_url && (
            <a
              href={project.repository_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyber-400 text-sm hover:text-cyber-300 flex items-center gap-1 mt-0.5"
            >
              <Github size={12} /> {project.repository_url}
            </a>
          )}
          <p className="text-dark-400 text-xs mt-1">
            Created {project.created_at ? new Date(project.created_at).toLocaleString() : ''}
          </p>
        </div>
        <button
          id="run-scan-btn"
          onClick={handleScan}
          disabled={scanning}
          className="btn-primary"
        >
          {scanning ? <><Spinner size={16} /> Scanning…</> : <><Play size={16} /> Run Security Scan</>}
        </button>
      </div>

      {/* Info cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="glass-card p-4">
          <h3 className="text-xs font-semibold text-dark-400 uppercase mb-3 flex items-center gap-2">
            <Code size={12} /> Detected Languages
          </h3>
          {langs.length === 0 ? (
            <p className="text-dark-500 text-sm">No source code detected</p>
          ) : (
            <div className="space-y-2">
              {langs.map(l => (
                <div key={l.name} className="flex items-center justify-between">
                  <span className="text-sm text-dark-200 font-medium">{l.name}</span>
                  <span className="text-xs text-dark-400">{l.file_count} files</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="glass-card p-4">
          <h3 className="text-xs font-semibold text-dark-400 uppercase mb-3">Dependencies Found</h3>
          {Object.keys(project.dependencies || {}).length === 0 ? (
            <p className="text-dark-500 text-sm">No dependency files detected</p>
          ) : (
            <div className="space-y-1">
              {Object.entries(project.dependencies || {}).map(([lang, files]) => (
                <div key={lang}>
                  <span className="text-xs text-dark-400">{lang}:</span>{' '}
                  <span className="text-xs text-dark-200">{files.join(', ')}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Latest scan summary */}
      {latestScan && latestScan.status === 'completed' && (
        <div className="glass-card p-5">
          <h2 className="font-semibold text-dark-100 mb-4">Latest Scan Summary</h2>
          <div className="flex items-center gap-8">
            <ScoreGauge score={latestScan.security_score} size={100} />
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 flex-1">
              {[
                { label: 'Critical', count: latestScan.critical_count, color: 'text-red-400' },
                { label: 'High', count: latestScan.high_count, color: 'text-orange-400' },
                { label: 'Medium', count: latestScan.medium_count, color: 'text-yellow-400' },
                { label: 'Low', count: latestScan.low_count, color: 'text-blue-400' },
                { label: 'Info', count: latestScan.info_count, color: 'text-dark-400' },
              ].map(({ label, count, color }) => (
                <div key={label} className="text-center p-3 bg-dark-800 rounded-lg">
                  <div className={`text-2xl font-bold ${color}`}>{count ?? 0}</div>
                  <div className="text-xs text-dark-500 mt-0.5">{label}</div>
                </div>
              ))}
            </div>
          </div>
          <button
            className="btn-secondary mt-4 text-sm"
            onClick={() => navigate(`/scans/${latestScan.scan_id}`)}
          >
            View Full Results <ChevronRight size={14} />
          </button>
        </div>
      )}

      {/* Scan history */}
      <div className="glass-card overflow-hidden">
        <div className="px-5 py-4 border-b border-dark-700/50">
          <h2 className="font-semibold text-dark-100">Scan History</h2>
        </div>
        <div className="p-4 space-y-3">
          {history.length === 0 ? (
            <div className="text-center py-8 text-dark-500">
              <Clock size={24} className="mx-auto mb-2 text-dark-600" />
              <p>No scans yet. Click "Run Security Scan" to start.</p>
            </div>
          ) : (
            [...history].reverse().map((scan, i) => (
              <ScanHistoryRow key={scan.scan_id} scan={scan} index={history.length - 1 - i} />
            ))
          )}
        </div>
      </div>
    </div>
  )
}
