/**
 * System Status page – backend, database, Ollama, scanners
 */
import { useState, useEffect } from 'react'
import { getSystemStatus } from '../services/api'
import { LoadingPage, Spinner } from '../components/LoadingStates'
import { RefreshCw, CheckCircle2, XCircle, AlertCircle } from 'lucide-react'

function StatusRow({ label, available, error, detail }) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-dark-700/20 last:border-0">
      <div>
        <span className="text-sm font-medium text-dark-200">{label}</span>
        {detail && <span className="text-xs text-dark-500 ml-2">({detail})</span>}
        {error && <p className="text-xs text-red-400 mt-0.5">{error}</p>}
      </div>
      <div className="flex items-center gap-2">
        {available === true ? (
          <>
            <span className="status-dot-green" />
            <span className="text-xs text-emerald-400 font-medium">Available</span>
          </>
        ) : available === false ? (
          <>
            <span className="status-dot-red" />
            <span className="text-xs text-red-400 font-medium">Unavailable</span>
          </>
        ) : (
          <>
            <span className="status-dot-yellow" />
            <span className="text-xs text-amber-400 font-medium">Unknown</span>
          </>
        )}
      </div>
    </div>
  )
}

export default function SystemStatus() {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const fetchStatus = () => {
    setRefreshing(true)
    return getSystemStatus()
      .then(r => setStatus(r.data))
      .finally(() => { setLoading(false); setRefreshing(false) })
  }

  useEffect(() => { fetchStatus() }, [])

  if (loading) return <LoadingPage message="Checking system status…" />

  const s = status || {}
  const ollama = s.ollama || {}
  const scanners = s.scanners || {}
  const config = s.config || {}

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">System Status</h1>
          <p className="text-dark-400 text-sm mt-1">Health check for all system components</p>
        </div>
        <button
          onClick={fetchStatus}
          disabled={refreshing}
          className="btn-secondary"
          id="refresh-status-btn"
        >
          {refreshing ? <Spinner size={14} /> : <RefreshCw size={14} />}
          Refresh
        </button>
      </div>

      {/* Core services */}
      <div className="glass-card p-5">
        <h2 className="text-sm font-semibold text-dark-400 uppercase tracking-wider mb-3">Core Services</h2>
        <StatusRow label="Backend API" available={s.backend?.available} />
        <StatusRow label="Database" available={s.database?.available} error={s.database?.error} />
        <StatusRow
          label="Ollama"
          available={ollama.available}
          error={ollama.error}
          detail={ollama.available ? 'Connected' : undefined}
        />
        <StatusRow
          label={`LLM Model: ${ollama.model || config.ollama_model || 'N/A'}`}
          available={ollama.model_available}
          error={ollama.model_available ? null : ollama.available ? `Model "${ollama.model}" not found. Run: ollama pull ${ollama.model}` : null}
        />
      </div>

      {/* Ollama info */}
      {ollama.available && (
        <div className="glass-card p-4">
          <h3 className="text-xs font-semibold text-dark-400 uppercase mb-2">Available Models</h3>
          {(ollama.available_models || []).length === 0 ? (
            <p className="text-xs text-dark-500">No models found. Run <code className="text-cyber-300">ollama pull {ollama.model}</code></p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {ollama.available_models.map(m => (
                <span
                  key={m}
                  className={`text-xs px-2 py-1 rounded font-mono ${
                    m.includes(ollama.model?.split(':')[0] || '')
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-700'
                      : 'bg-dark-800 text-dark-400'
                  }`}
                >
                  {m}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Scanners */}
      <div className="glass-card p-5">
        <h2 className="text-sm font-semibold text-dark-400 uppercase tracking-wider mb-3">Security Scanners</h2>
        {Object.entries(scanners).map(([name, info]) => (
          <StatusRow
            key={name}
            label={name.charAt(0).toUpperCase() + name.slice(1)}
            available={info.available}
          />
        ))}
        {Object.keys(scanners).length === 0 && (
          <p className="text-dark-500 text-sm">No scanner information available.</p>
        )}
      </div>

      {/* Config */}
      <div className="glass-card p-5">
        <h2 className="text-sm font-semibold text-dark-400 uppercase tracking-wider mb-3">Configuration</h2>
        <div className="space-y-2">
          {[
            ['LLM Model', config.ollama_model],
            ['Max Upload', `${config.max_upload_mb} MB`],
            ['Context Lines', `±${config.context_lines_before || 20} lines`],
            ['LLM Timeout', `${config.llm_timeout_seconds}s`],
          ].map(([label, value]) => (
            <div key={label} className="flex items-center justify-between py-1">
              <span className="text-sm text-dark-400">{label}</span>
              <span className="text-sm text-dark-200 font-mono">{value || 'N/A'}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Ollama setup instructions */}
      {!ollama.available && (
        <div className="glass-card p-5 border border-amber-800/30 bg-amber-950/10">
          <h3 className="text-sm font-semibold text-amber-300 mb-3 flex items-center gap-2">
            <AlertCircle size={14} /> Ollama Setup Instructions
          </h3>
          <div className="space-y-2 text-xs text-dark-300">
            <p>1. Install Ollama from <a href="https://ollama.ai" target="_blank" rel="noopener noreferrer" className="text-cyber-400 hover:text-cyber-300">ollama.ai</a></p>
            <p>2. Start Ollama:</p>
            <pre className="code-block text-xs p-2">ollama serve</pre>
            <p>3. Pull the Qwen model:</p>
            <pre className="code-block text-xs p-2">ollama pull {config.ollama_model || 'qwen2.5-coder:3b'}</pre>
            <p className="text-dark-500">Scanner results are still available even without Ollama.</p>
          </div>
        </div>
      )}
    </div>
  )
}
