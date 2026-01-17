import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Server, FolderTree, Shield, Clock, Bell, Settings } from 'lucide-react'

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/servers', label: 'Servers', icon: Server },
  { path: '/groups', label: 'Groups', icon: FolderTree },
  { path: '/policies', label: 'Policies', icon: Shield },
  { path: '/jobs', label: 'Jobs', icon: Clock },
  { path: '/alerts', label: 'Alerts', icon: Bell },
  { path: '/settings', label: 'Settings', icon: Settings },
]

export const Sidebar = () => {
  return (
    <aside className="w-64 bg-gray-900 text-white min-h-screen">
      <nav className="mt-6">
        <ul className="space-y-1 px-3">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                    }`
                  }
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.label}</span>
                </NavLink>
              </li>
            )
          })}
        </ul>
      </nav>
    </aside>
  )
}
