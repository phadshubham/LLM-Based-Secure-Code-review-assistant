/**
 * Axios API client configured to talk to the FastAPI backend.
 */
import axios from 'axios'
import toast from 'react-hot-toast'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// Global error handler
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred'
    // Don't toast on 404s for polling
    if (error.response?.status !== 404) {
      toast.error(message)
    }
    return Promise.reject(error)
  }
)

// ─── Projects ─────────────────────────────────────────────────────────────────

export const uploadProject = (formData, onUploadProgress) =>
  api.post('/projects/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
    onUploadProgress,
  })

export const addGithubProject = (url, projectName) =>
  api.post('/projects/github', { url, project_name: projectName })

export const getProjects = () => api.get('/projects')

export const getProject = (projectId) => api.get(`/projects/${projectId}`)

export const triggerScan = (projectId) =>
  api.post(`/projects/${projectId}/scan`)

export const getProjectHistory = (projectId) =>
  api.get(`/projects/${projectId}/history`)

// ─── Scans ────────────────────────────────────────────────────────────────────

export const getScan = (scanId) => api.get(`/scans/${scanId}`)

export const getScanFindings = (scanId, params = {}) =>
  api.get(`/scans/${scanId}/findings`, { params })

// ─── Findings ─────────────────────────────────────────────────────────────────

export const getFinding = (findingId) => api.get(`/findings/${findingId}`)

export const getAIReview = (findingId) => api.get(`/findings/${findingId}/review`)

// ─── Reports ──────────────────────────────────────────────────────────────────

export const downloadPDF = (scanId) =>
  api.get(`/reports/${scanId}/pdf`, { responseType: 'blob' })

export const downloadJSON = (scanId) =>
  api.get(`/reports/${scanId}/json`, { responseType: 'blob' })

// ─── System ───────────────────────────────────────────────────────────────────

export const getSystemStatus = () => api.get('/system/status')

export default api
