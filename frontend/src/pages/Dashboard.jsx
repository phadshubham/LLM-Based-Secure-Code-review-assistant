/**
 * Dashboard page – overview cards, charts, recent scans
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import { Shield, AlertTriangle, Scan, FolderOpen, ChevronRight, Plus } from 'lucide-react'
import { getProjects, getScanFindings } from '../services/api'
import SeverityBadge from '../components/SeverityBadge'
import ScoreGauge from '../components/ScoreGauge'
import { LoadingPage } from '../components/LoadingStates'

const SEV_COLORS = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#3b82f6',
  INFO: '#6b7280',
}

function StatCard({ icon: Icon, label, value, color = 'text-white', sublabel }) {
  return (
    <div className="glass-card p-5 hover:border-dark-600/60 transition-all duration-200 group">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-dark-400 font-medium mb-1">{label}</p>
          <p className={`text-3xl font-bold ${color}`}>{value ?? '–'}</p>
          {sublabel && <p className="text-xs text-dark-500 mt-1">{sublabel}</p>}
        </div>
        <div className="w-10 h-10 rounded-lg bg-dark-800 flex items-center justify-center group-hover:bg-dark-700 transition-colors">
          <Icon size={18} className="text-dark-400" />
        </div>
      </div>
    </div>
  )
}

function ScanRow({ scan, project }) {
  const navigate = useNavigate()
  const score = Math.round(scan.security_score ?? 0)
  const scoreColor =
    score >= 80 ? 'text-emerald-400' :
    score >= 60 ? 'text-amber-400' :
    'text-red-400'

  return (
    <tr
      className="border-b border-dark-700/30 hover:bg-dark-800/50 cursor-pointer transition-colors"
      onClick={() => navigate(`/scans/${scan.scan_id}`)}
    >
      <td className="px-4 py-3 font-medium text-dark-100 text-sm">{project?.name || '–'}</td>
      <td className="px-4 py-3">
        <span className="text-xs text-dark-400">{(project?.language || []).map(l => l.name).join(', ') || '–'}</span>
      </td>
      <td className="px-4 py-3">
        <span className={`font-bold ${scoreColor}`}>{score}/100</span>
      </td>
      <td className="px-4 py-3 text-red-400 font-medium text-sm">{scan.critical_count ?? 0}</td>
      <td className="px-4 py-3 text-orange-400 font-medium text-sm">{scan.high_count ?? 0}</td>
      <td className="px-4 py-3 text-yellow-400 font-medium text-sm">{scan.medium_count ?? 0}</td>
      <td className="px-4 py-3">
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${
          scan.status === 'completed' ? 'bg-emerald-950 text-emerald-300' :
          scan.status === 'running' ? 'bg-blue-950 text-blue-300' :
          scan.status === 'failed' ? 'bg-red-950 text-red-300' :
          'bg-dark-700 text-dark-400'
        }`}>
          {scan.status}
        </span>
      </td>
      <td className="px-4 py-3 text-dark-400 text-xs">
        {scan.started_at ? new Date(scan.started_at).toLocaleDateString() : '–'}
      </td>
      <td className="px-4 py-3">
        <ChevronRight size={14} className="text-dark-500" />
      </td>
    </tr>
  )
}

export default function Dashboard() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    getProjects()
      .then(r => setProjects(r.data.projects || []))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingPage message="Loading dashboard…" />

  // Aggregate stats from all projects' latest scan
  const allScans = projects.flatMap(p => p._latestScan ? [p._latestScan] : [])

  // Collect the last scan per project from project list (they don't have scan attached)
  // We'll display recent projects instead
  const totalProjects = projects.length
  const recentProjects = projects.slice(0, 10)

  // Severity distribution for bar chart
  const sevData = [
    { name: 'Critical', value: 0, fill: SEV_COLORS.CRITICAL },
    { name: 'High', value: 0, fill: SEV_COLORS.HIGH },
    { name: 'Medium', value: 0, fill: SEV_COLORS.MEDIUM },
    { name: 'Low', value: 0, fill: SEV_COLORS.LOW },
  ]

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Security Dashboard</h1>
          <p className="text-dark-400 text-sm mt-1">
            LLM-powered code security review for student projects
          </p>
        </div>
        <button
          onClick={() => navigate('/new')}
          className="btn-primary"
          id="new-project-btn"
        >
          <Plus size={16} />
          New Project
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={FolderOpen}
          label="Total Projects"
          value={totalProjects}
          color="text-cyber-400"
        />
        <StatCard
          icon={Scan}
          label="Projects Scanned"
          value={totalProjects}
          color="text-purple-400"
        />
        <StatCard
          icon={Shield}
          label="Security Tool"
          value="Active"
          color="text-emerald-400"
          sublabel="Semgrep + Bandit + Trivy"
        />
        <StatCard
          icon={AlertTriangle}
          label="AI Model"
          value="Qwen"
          color="text-amber-400"
          sublabel="Local Ollama"
        />
      </div>

      {/* Projects list / recent scans */}
      <div className="glass-card overflow-hidden">
        <div className="px-5 py-4 border-b border-dark-700/50 flex items-center justify-between">
          <h2 className="font-semibold text-dark-100">Recent Projects</h2>
          <button
            onClick={() => navigate('/projects')}
            className="text-xs text-cyber-400 hover:text-cyber-300 transition-colors"
          >
            View all →
          </button>
        </div>

        {projects.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 gap-4">
            <div className="w-16 h-16 rounded-full bg-dark-800 flex items-center justify-center">
              <FolderOpen size={28} className="text-dark-500" />
            </div>
            <div className="text-center">
              <p className="text-dark-300 font-medium">No projects yet</p>
              <p className="text-dark-500 text-sm mt-1">Upload a ZIP or link a GitHub repo to get started</p>
            </div>
            <button onClick={() => navigate('/new')} className="btn-primary">
              <Plus size={16} /> Create First Project
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-dark-700/50">
                  {['Project', 'Language', 'Score', 'Critical', 'High', 'Medium', 'Status', 'Date', ''].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-dark-400 uppercase tracking-wider">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {recentProjects.map(p => (
                  <tr
                    key={p.project_id}
                    className="border-b border-dark-700/30 hover:bg-dark-800/50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/projects/${p.project_id}`)}
                  >
                    <td className="px-4 py-3 font-medium text-dark-100">{p.name}</td>
                    <td className="px-4 py-3 text-dark-400 text-xs">
                      {(p.language || []).map(l => l.name).join(', ') || '–'}
                    </td>
                    <td className="px-4 py-3 text-dark-400">–</td>
                    <td className="px-4 py-3 text-dark-400">–</td>
                    <td className="px-4 py-3 text-dark-400">–</td>
                    <td className="px-4 py-3 text-dark-400">–</td>
                    <td className="px-4 py-3">
                      <span className="text-xs px-2 py-1 rounded-full bg-dark-700 text-dark-400">ready</span>
                    </td>
                    <td className="px-4 py-3 text-dark-400 text-xs">
                      {p.created_at ? new Date(p.created_at).toLocaleDateString() : '–'}
                    </td>
                    <td className="px-4 py-3">
                      <ChevronRight size={14} className="text-dark-500" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Disclaimer */}
      <div className="glass-card p-4 border border-amber-800/30 bg-amber-950/10">
        <p className="text-xs text-amber-300/80">
          ⚠️ This security score is an educational/project-defined metric and is not an industry security certification.
        </p>
      </div>
    </div>
  )
}
