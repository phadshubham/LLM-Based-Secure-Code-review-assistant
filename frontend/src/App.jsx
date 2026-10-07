import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import NewProject from './pages/NewProject'
import Projects from './pages/Projects'
import ProjectDetail from './pages/ProjectDetail'
import ScanResults from './pages/ScanResults'
import FindingDetail from './pages/FindingDetail'
import ScanHistory from './pages/ScanHistory'
import Reports from './pages/Reports'
import SystemStatus from './pages/SystemStatus'

function Layout({ children }) {
  return (
    <div className="flex min-h-screen bg-dark-950">
      <Sidebar />
      <main className="flex-1 overflow-x-hidden">
        {children}
      </main>
    </div>
  )
}

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/new" element={<NewProject />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/projects/:projectId" element={<ProjectDetail />} />
          <Route path="/scans/:scanId" element={<ScanResults />} />
          <Route path="/findings/:findingId" element={<FindingDetail />} />
          <Route path="/history" element={<ScanHistory />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/status" element={<SystemStatus />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
