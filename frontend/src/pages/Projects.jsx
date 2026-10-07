/**
 * Projects list page
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, FolderOpen, ChevronRight, Github, Archive } from 'lucide-react'
import { getProjects } from '../services/api'
import { LoadingPage } from '../components/LoadingStates'

export default function Projects() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getProjects()
      .then(r => setProjects(r.data.projects || []))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingPage message="Loading projects…" />

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Projects</h1>
          <p className="text-dark-400 text-sm mt-1">{projects.length} project(s) total</p>
        </div>
        <button onClick={() => navigate('/new')} className="btn-primary" id="create-project-btn">
          <Plus size={16} /> New Project
        </button>
      </div>

      {projects.length === 0 ? (
        <div className="glass-card flex flex-col items-center justify-center py-20 gap-4">
          <div className="w-16 h-16 rounded-full bg-dark-800 flex items-center justify-center">
            <FolderOpen size={28} className="text-dark-500" />
          </div>
          <div className="text-center">
            <p className="text-dark-300 font-medium">No projects yet</p>
            <p className="text-dark-500 text-sm mt-1">Upload a ZIP or link a GitHub repository</p>
          </div>
          <button onClick={() => navigate('/new')} className="btn-primary">
            <Plus size={16} /> Create First Project
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {projects.map(p => (
            <div
              key={p.project_id}
              className="glass-card p-5 hover:border-dark-600/60 cursor-pointer transition-all duration-200 group"
              onClick={() => navigate(`/projects/${p.project_id}`)}
              id={`project-${p.project_id}`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="w-10 h-10 rounded-lg bg-dark-800 flex items-center justify-center group-hover:bg-dark-700 transition-colors">
                  {p.source_type === 'github'
                    ? <Github size={18} className="text-dark-400" />
                    : <Archive size={18} className="text-dark-400" />
                  }
                </div>
                <ChevronRight size={16} className="text-dark-600 group-hover:text-dark-400 transition-colors" />
              </div>
              <h3 className="font-semibold text-dark-100 text-sm">{p.name}</h3>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs text-dark-500">
                  {(p.language || []).map(l => l.name).join(', ') || 'Unknown language'}
                </span>
              </div>
              {p.repository_url && (
                <p className="text-xs text-cyber-500 mt-1 truncate">{p.repository_url}</p>
              )}
              <p className="text-xs text-dark-600 mt-2">
                {p.created_at ? new Date(p.created_at).toLocaleDateString() : ''}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
