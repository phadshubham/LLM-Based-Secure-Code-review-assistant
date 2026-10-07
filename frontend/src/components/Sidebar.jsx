/**
 * Sidebar navigation component
 */
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Plus, FolderOpen, History,
  FileText, Settings, Shield, ChevronRight,
} from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/new', icon: Plus, label: 'New Project' },
  { to: '/projects', icon: FolderOpen, label: 'Projects' },
  { to: '/history', icon: History, label: 'Scan History' },
  { to: '/reports', icon: FileText, label: 'Reports' },
  { to: '/status', icon: Settings, label: 'System Status' },
]

export default function Sidebar() {
  return (
    <aside className="w-60 flex-shrink-0 bg-dark-900/80 border-r border-dark-700/50 backdrop-blur-sm flex flex-col min-h-screen">
      {/* Logo */}
      <div className="p-5 border-b border-dark-700/50">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyber-600 to-purple-600 flex items-center justify-center shadow-lg shadow-cyber-500/20">
            <Shield size={18} className="text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white">SecureReview</h1>
            <p className="text-xs text-dark-400">Code Security Assistant</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-0.5">
        {navItems.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-cyber-600/20 text-cyber-300 border border-cyber-600/30'
                  : 'text-dark-400 hover:text-dark-100 hover:bg-dark-800'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={16} className={isActive ? 'text-cyber-400' : 'text-dark-500 group-hover:text-dark-300'} />
                <span className="flex-1">{label}</span>
                {isActive && <ChevronRight size={12} className="text-cyber-400" />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-dark-700/50">
        <p className="text-xs text-dark-500 leading-relaxed">
          Academic project tool.<br />
          Powered by local Qwen LLM.
        </p>
      </div>
    </aside>
  )
}
