/**
 * Scan History page – all scans across all projects
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronRight, History } from 'lucide-react'
import { getProjects, getProjectHistory } from '../services/api'
import ScoreGauge from '../components/ScoreGauge'
import { LoadingPage } from '../components/LoadingStates'

export default function ScanHistory() {
  const navigate = useNavigate()
  const [entries, setEntries] = useState([]) // [{project, scans}]
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getProjects().then(async r => {
      const projects = r.data.projects || []
      const results = await Promise.all(
        projects.map(async p => {
          try {
            const hr = await getProjectHistory(p.project_id)
            return { project: p, scans: hr.data.scans || [] }
          } catch {
            return { project: p, scans: [] }
          }
        })
      )
      // Sort by most recent scan date
      results.sort((a, b) => {
        const aDate = a.scans.at(-1)?.started_at || a.project.created_at || ''
        const bDate = b.scans.at(-1)?.started_at || b.project.created_at || ''
        return bDate.localeCompare(aDate)
      })
      setEntries(results)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingPage message="Loading scan history…" />

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Scan History</h1>
        <p className="text-dark-400 text-sm mt-1">All security scans across all projects</p>
      </div>

      {entries.length === 0 || entries.every(e => e.scans.length === 0) ? (
        <div className="glass-card flex flex-col items-center justify-center py-20 gap-3">
          <History size={32} className="text-dark-600" />
          <p className="text-dark-400">No scans have been run yet.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {entries.filter(e => e.scans.length > 0).map(({ project, scans }) => (
            <div key={project.project_id} className="glass-card overflow-hidden">
              <div
                className="px-5 py-3 border-b border-dark-700/50 cursor-pointer hover:bg-dark-800/30 transition-colors"
                onClick={() => navigate(`/projects/${project.project_id}`)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="font-semibold text-dark-100">{project.name}</h2>
                    <p className="text-xs text-dark-500">
                      {(project.language || []).map(l => l.name).join(', ') || 'Unknown'} · {scans.length} scan(s)
                    </p>
                  </div>
                  <ChevronRight size={16} className="text-dark-500" />
                </div>
              </div>

              {/* Score progression */}
              <div className="p-5">
                {scans.length > 1 && (
                  <div className="mb-4">
                    <p className="text-xs text-dark-500 mb-2">Score Progression</p>
                    <div className="flex items-center gap-2">
                      {scans.map((s, i) => (
                        <div key={s.scan_id} className="flex items-center gap-1">
                          <div
                            className="text-center cursor-pointer"
                            onClick={() => navigate(`/scans/${s.scan_id}`)}
                          >
                            <div className={`text-sm font-bold ${
                              (s.security_score || 0) >= 80 ? 'text-emerald-400' :
                              (s.security_score || 0) >= 60 ? 'text-amber-400' :
                              'text-red-400'
                            }`}>
                              {Math.round(s.security_score ?? 0)}
                            </div>
                            <div className="text-xs text-dark-600">#{i + 1}</div>
                          </div>
                          {i < scans.length - 1 && (
                            <ChevronRight size={12} className="text-dark-600" />
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="space-y-2">
                  {[...scans].reverse().slice(0, 5).map((scan, i) => (
                    <div
                      key={scan.scan_id}
                      className="flex items-center gap-4 p-3 rounded-lg hover:bg-dark-800/50 cursor-pointer transition-colors border border-dark-700/20"
                      onClick={() => navigate(`/scans/${scan.scan_id}`)}
                    >
                      <ScoreGauge score={scan.security_score} size={50} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                            scan.status === 'completed' ? 'bg-emerald-950 text-emerald-300' :
                            scan.status === 'running' ? 'bg-blue-950 text-blue-300' :
                            scan.status === 'failed' ? 'bg-red-950 text-red-300' :
                            'bg-dark-700 text-dark-400'
                          }`}>
                            {scan.status}
                          </span>
                          <span className="text-xs text-dark-400">
                            {scan.total_findings ?? 0} findings
                          </span>
                        </div>
                        <div className="flex gap-3 mt-0.5 text-xs">
                          <span className="text-red-400">{scan.critical_count ?? 0} crit</span>
                          <span className="text-orange-400">{scan.high_count ?? 0} high</span>
                          <span className="text-yellow-400">{scan.medium_count ?? 0} med</span>
                        </div>
                      </div>
                      <div className="text-xs text-dark-500">
                        {scan.started_at ? new Date(scan.started_at).toLocaleDateString() : ''}
                      </div>
                      <ChevronRight size={13} className="text-dark-600" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
