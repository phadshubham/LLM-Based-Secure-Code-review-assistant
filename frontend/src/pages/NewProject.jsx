/**
 * New Project page – ZIP upload or GitHub URL
 */
import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import toast from 'react-hot-toast'
import {
  Upload, Github, FileArchive, CheckCircle2,
  AlertCircle, X, Info,
} from 'lucide-react'
import { uploadProject, addGithubProject } from '../services/api'
import { Spinner } from '../components/LoadingStates'

const PROGRESS_STEPS = [
  'Uploading',
  'Processing',
  'Detecting Languages',
  'Detecting Dependencies',
  'Project Ready',
]

export default function NewProject() {
  const navigate = useNavigate()
  const [tab, setTab] = useState('zip') // 'zip' | 'github'
  const [file, setFile] = useState(null)
  const [projectName, setProjectName] = useState('')
  const [githubUrl, setGithubUrl] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState(-1)

  const onDrop = useCallback((accepted) => {
    const f = accepted[0]
    if (!f) return
    if (!f.name.endsWith('.zip')) {
      toast.error('Only .zip files are accepted.')
      return
    }
    if (f.size > 100 * 1024 * 1024) {
      toast.error('File exceeds 100 MB limit.')
      return
    }
    setFile(f)
    if (!projectName) setProjectName(f.name.replace('.zip', ''))
  }, [projectName])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/zip': ['.zip'] },
    multiple: false,
  })

  const handleZipUpload = async () => {
    if (!file) { toast.error('Please select a ZIP file.'); return }
    setUploading(true)
    setCurrentStep(0)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('project_name', projectName || file.name.replace('.zip', ''))

    try {
      setCurrentStep(1)
      const resp = await uploadProject(formData, (e) => {
        setUploadProgress(Math.round((e.loaded / e.total) * 100))
      })
      setCurrentStep(4)
      toast.success('Project uploaded successfully!')
      const projectId = resp.data.project.project_id
      navigate(`/projects/${projectId}`)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed.')
      setUploading(false)
      setCurrentStep(-1)
    }
  }

  const handleGithubSubmit = async () => {
    if (!githubUrl.trim()) { toast.error('Please enter a GitHub URL.'); return }
    setUploading(true)
    setCurrentStep(0)

    try {
      setCurrentStep(1)
      const resp = await addGithubProject(githubUrl, projectName)
      setCurrentStep(4)
      toast.success('Repository cloned successfully!')
      const projectId = resp.data.project.project_id
      navigate(`/projects/${projectId}`)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to clone repository.')
      setUploading(false)
      setCurrentStep(-1)
    }
  }

  return (
    <div className="p-6 max-w-2xl mx-auto animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">New Project</h1>
        <p className="text-dark-400 text-sm mt-1">
          Upload your project for security analysis
        </p>
      </div>

      {/* Tab selector */}
      <div className="flex gap-1 p-1 bg-dark-800 rounded-lg mb-6">
        <button
          id="tab-zip"
          onClick={() => setTab('zip')}
          className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium transition-all ${
            tab === 'zip'
              ? 'bg-dark-700 text-white shadow'
              : 'text-dark-400 hover:text-dark-200'
          }`}
        >
          <FileArchive size={15} /> ZIP Upload
        </button>
        <button
          id="tab-github"
          onClick={() => setTab('github')}
          className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium transition-all ${
            tab === 'github'
              ? 'bg-dark-700 text-white shadow'
              : 'text-dark-400 hover:text-dark-200'
          }`}
        >
          <Github size={15} /> GitHub URL
        </button>
      </div>

      <div className="glass-card p-6 space-y-5">
        {/* Project Name */}
        <div>
          <label className="block text-sm font-medium text-dark-200 mb-1.5">
            Project Name
          </label>
          <input
            id="project-name-input"
            type="text"
            value={projectName}
            onChange={e => setProjectName(e.target.value)}
            placeholder="My Student Project"
            className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-sm text-dark-100 placeholder-dark-500 focus:outline-none focus:border-cyber-500 focus:ring-1 focus:ring-cyber-500 transition-colors"
          />
        </div>

        {tab === 'zip' ? (
          <>
            {/* Dropzone */}
            <div>
              <label className="block text-sm font-medium text-dark-200 mb-1.5">
                Project ZIP File
              </label>
              <div
                {...getRootProps()}
                id="dropzone"
                className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-200 ${
                  isDragActive
                    ? 'border-cyber-500 bg-cyber-500/5'
                    : file
                    ? 'border-emerald-600/50 bg-emerald-950/10'
                    : 'border-dark-600 hover:border-dark-500 hover:bg-dark-800/30'
                }`}
              >
                <input {...getInputProps()} id="file-input" />
                {file ? (
                  <div className="flex flex-col items-center gap-2">
                    <CheckCircle2 size={36} className="text-emerald-400" />
                    <p className="font-medium text-emerald-300">{file.name}</p>
                    <p className="text-xs text-dark-400">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                    <button
                      onClick={e => { e.stopPropagation(); setFile(null) }}
                      className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1"
                    >
                      <X size={12} /> Remove
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-2">
                    <Upload size={36} className="text-dark-500" />
                    <p className="text-dark-300 font-medium">
                      {isDragActive ? 'Drop your ZIP here…' : 'Drag & drop your ZIP file here'}
                    </p>
                    <p className="text-dark-500 text-sm">or click to browse</p>
                    <p className="text-dark-600 text-xs mt-2">Maximum size: 100 MB</p>
                  </div>
                )}
              </div>
            </div>

            {/* Upload progress */}
            {uploading && uploadProgress > 0 && uploadProgress < 100 && (
              <div>
                <div className="flex justify-between text-xs text-dark-400 mb-1">
                  <span>Uploading…</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="h-1.5 bg-dark-700 rounded-full overflow-hidden">
                  <div
                    className="h-full progress-bar rounded-full transition-all"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            <button
              id="upload-btn"
              onClick={handleZipUpload}
              disabled={!file || uploading}
              className="btn-primary w-full justify-center py-3"
            >
              {uploading ? (
                <><Spinner size={16} /> Processing…</>
              ) : (
                <><Upload size={16} /> Upload &amp; Analyse</>
              )}
            </button>
          </>
        ) : (
          <>
            {/* GitHub URL */}
            <div>
              <label className="block text-sm font-medium text-dark-200 mb-1.5">
                Public GitHub Repository URL
              </label>
              <div className="relative">
                <Github size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-500" />
                <input
                  id="github-url-input"
                  type="url"
                  value={githubUrl}
                  onChange={e => setGithubUrl(e.target.value)}
                  placeholder="https://github.com/username/repository"
                  className="w-full pl-9 pr-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-sm text-dark-100 placeholder-dark-500 focus:outline-none focus:border-cyber-500 focus:ring-1 focus:ring-cyber-500 transition-colors"
                />
              </div>
              <p className="text-xs text-dark-500 mt-1 flex items-center gap-1">
                <Info size={11} /> Only public repositories are supported
              </p>
            </div>

            <button
              id="github-submit-btn"
              onClick={handleGithubSubmit}
              disabled={!githubUrl.trim() || uploading}
              className="btn-primary w-full justify-center py-3"
            >
              {uploading ? (
                <><Spinner size={16} /> Cloning…</>
              ) : (
                <><Github size={16} /> Clone &amp; Analyse</>
              )}
            </button>
          </>
        )}

        {/* Step progress */}
        {uploading && (
          <div className="mt-4">
            <div className="flex flex-col gap-2">
              {PROGRESS_STEPS.map((step, i) => (
                <div key={step} className={`flex items-center gap-3 text-sm transition-all ${
                  i < currentStep ? 'text-emerald-400' :
                  i === currentStep ? 'text-cyber-300' :
                  'text-dark-600'
                }`}>
                  {i < currentStep ? (
                    <CheckCircle2 size={14} />
                  ) : i === currentStep ? (
                    <Spinner size={14} />
                  ) : (
                    <div className="w-3.5 h-3.5 rounded-full border border-dark-600" />
                  )}
                  {step}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Info box */}
      <div className="mt-4 glass-card p-4 border border-dark-600/50">
        <h3 className="text-sm font-semibold text-dark-200 mb-2 flex items-center gap-2">
          <Info size={14} className="text-cyber-400" /> What happens next?
        </h3>
        <ul className="text-xs text-dark-400 space-y-1">
          <li>• Language detection (Python, JavaScript, Java)</li>
          <li>• Security scanning with Semgrep, Bandit, ESLint, SpotBugs, Trivy</li>
          <li>• Finding normalisation and severity scoring</li>
          <li>• AI explanation via local Qwen model through Ollama</li>
          <li>• PDF &amp; JSON report generation</li>
        </ul>
      </div>
    </div>
  )
}
