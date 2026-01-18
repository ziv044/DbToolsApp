import { NavLink } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { LayoutDashboard, Server, Database, FolderTree, Shield, Clock, Bell, FileText, Settings, BarChart3 } from 'lucide-react'
import { alertService } from '../../services/alertService'
import { useTenantStore } from '../../stores/tenantStore'

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/servers', label: 'Servers', icon: Server },
  { path: '/running-queries', label: 'Running Queries', icon: Database },
  { path: '/analytics', label: 'Query Analytics', icon: BarChart3 },
  { path: '/groups', label: 'Groups', icon: FolderTree },
  { path: '/policies', label: 'Policies', icon: Shield },
  { path: '/jobs', label: 'Jobs', icon: Clock },
  { path: '/alerts', label: 'Alerts', icon: Bell, showBadge: true },
  { path: '/activity', label: 'Activity', icon: FileText },
  { path: '/settings', label: 'Settings', icon: Settings },
]

export const Sidebar = () => {
  const { currentTenant } = useTenantStore()

  // Fetch alert counts for the badge (only when tenant is selected)
  const { data: alertCounts } = useQuery({
    queryKey: ['alerts', 'counts', currentTenant],
    queryFn: () => alertService.getAlertCounts(),
    refetchInterval: 30_000, // Refresh every 30 seconds
    staleTime: 10_000,
    enabled: !!currentTenant,
  })

  const criticalCount = alertCounts?.counts?.critical ?? 0
  const totalActive = alertCounts?.total ?? 0

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
                  <span className="flex-1">{item.label}</span>
                  {item.showBadge && totalActive > 0 && (
                    <span
                      className={`px-1.5 py-0.5 text-xs font-medium rounded-full ${
                        criticalCount > 0
                          ? 'bg-red-500 text-white'
                          : 'bg-yellow-500 text-gray-900'
                      }`}
                    >
                      {totalActive}
                    </span>
                  )}
                </NavLink>
              </li>
            )
          })}
        </ul>
      </nav>
    </aside>
  )
}
