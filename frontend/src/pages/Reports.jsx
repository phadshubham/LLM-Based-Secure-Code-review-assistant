/**
 * Reports page – list and download scan reports
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Download, FileText, FileJson, ChevronRight } from 'lucide-react'
import { getProjects, getProjectHistory, downloadPDF, downloadJSON } from '../services/api'
import { LoadingPage, Spinner } from '../components/LoadingStates'
import ScoreGauge from '../components/ScoreGauge'
import toast from 'react-hot-toast'

export default function Reports() {
  const navigate = useNavigate()
  const [completedScans, setCompletedScans] = useState([])
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState({})

  useEffect(() => {
    getProjects().then(async r => {
      const projects = r.data.projects || []
      const all = []
      for (const p of projects) {
        try {
          const hr = await getProjectHistory(p.project_id)
          const scans = (hr.data.scans || []).filter(s => s.status === 'completed')
          scans.forEach(s => all.push({ scan: s, project: p }))
        } catch {}
      }
      all.sort((a, b) => (b.scan.completed_at || '').localeCompare(a.scan.completed_at || ''))
      setCompletedScans(all)
    }).finally(() => setLoading(false))
  }, [])

  const handleDownload = async (scanId, format) => {
    setDownloading(d => ({ ...d, [`${scanId}-${format}`]: true }))
    try {
      const resp = format === 'pdf' ? await downloadPDF(scanId) : await downloadJSON(scanId)
      const url = URL.createObjectURL(new Blob([resp.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `security_report_${scanId.slice(0, 8)}.${format}`
      a.click()
      URL.revokeObjectURL(url)
      toast.success(`${format.toUpperCase()} downloaded`)
    } catch (err) {
      toast.error('Download failed')
    } finally {
      setDownloading(d => ({ ...d, [`${scanId}-${format}`]: false }))
    }
  }

  if (loading) return <LoadingPage message="Loading reports…" />

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Reports</h1>
        <p className="text-dark-400 text-sm mt-1">
          Download PDF and JSON security reports for completed scans
        </p>
      </div>

      {completedScans.length === 0 ? (
        <div className="glass-card flex flex-col items-center justify-center py-20 gap-3">
          <FileText size={32} className="text-dark-600" />
          <p className="text-dark-400">No completed scans available for reporting.</p>
          <button onClick={() => navigate('/new')} className="btn-primary mt-2">
            Start a Scan
          </button>
        </div>
      ) : (
        <div className="glass-card overflow-hidden">
          <div className="px-5 py-3 border-b border-dark-700/50">
            <h2 className="font-semibold text-dark-100">Available Reports ({completedScans.length})</h2>
          </div>
          <div className="divide-y divide-dark-700/20">
            {completedScans.map(({ scan, project }) => (
              <div key={scan.scan_id} className="flex items-center gap-4 p-4 hover:bg-dark-800/30 transition-colors">
                <ScoreGauge score={scan.security_score} size={55} />
                <div className="flex-1 min-w-0">
                  <div
                    className="font-medium text-dark-100 text-sm cursor-pointer hover:text-cyber-300 transition-colors"
                    onClick={() => navigate(`/scans/${scan.scan_id}`)}
                  >
                    {project.name}
                  </div>
                  <div className="text-xs text-dark-400 mt-0.5">
                    {(project.language || []).map(l => l.name).join(', ')} ·{' '}
                    {scan.total_findings ?? 0} findings ·{' '}
                    {scan.completed_at ? new Date(scan.completed_at).toLocaleString() : ''}
                  </div>
                  <div className="text-xs text-dark-600 font-mono mt-0.5">{scan.scan_id.slice(0, 8)}…</div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    id={`download-json-${scan.scan_id.slice(0,8)}`}
                    onClick={() => handleDownload(scan.scan_id, 'json')}
                    disabled={downloading[`${scan.scan_id}-json`]}
                    className="btn-secondary text-xs"
                    title="Download JSON Report"
                  >
                    {downloading[`${scan.scan_id}-json`] ? <Spinner size={12} /> : <FileJson size={13} />}
                    JSON
                  </button>
                  <button
                    id={`download-pdf-${scan.scan_id.slice(0,8)}`}
                    onClick={() => handleDownload(scan.scan_id, 'pdf')}
                    disabled={downloading[`${scan.scan_id}-pdf`]}
                    className="btn-secondary text-xs"
                    title="Download PDF Report"
                  >
                    {downloading[`${scan.scan_id}-pdf`] ? <Spinner size={12} /> : <FileText size={13} />}
                    PDF
                  </button>
                  <button
                    onClick={() => navigate(`/scans/${scan.scan_id}`)}
                    className="btn-secondary text-xs"
                  >
                    <ChevronRight size={13} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="glass-card p-4 border border-amber-800/20">
        <p className="text-xs text-amber-400/80">
          ⚠️ AI-generated recommendations in reports should be reviewed by a developer before implementation.
          Reports are for educational purposes only.
        </p>
      </div>
    </div>
  )
}
