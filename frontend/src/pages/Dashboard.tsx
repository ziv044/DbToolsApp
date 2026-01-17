import { useState, useMemo, useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Card, CardHeader, CardContent, Badge, Spinner, Button } from '../components/ui'
import { useTenantStore } from '../stores/tenantStore'
import { healthService } from '../services/healthService'
import type { HealthStatus, ServerHealth } from '../services/healthService'

// Status color mapping
const statusColors: Record<HealthStatus, { bg: string; text: string; border: string }> = {
  healthy: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
  warning: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
  critical: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
  offline: { bg: 'bg-gray-50', text: 'text-gray-500', border: 'border-gray-200' },
  unknown: { bg: 'bg-gray-50', text: 'text-gray-400', border: 'border-gray-200' },
}

const statusBadgeVariants: Record<HealthStatus, 'default' | 'success' | 'warning' | 'error' | 'info'> = {
  healthy: 'success',
  warning: 'warning',
  critical: 'error',
  offline: 'default',
  unknown: 'default',
}

interface SummaryCardProps {
  title: string
  count: number
  color: string
  textColor: string
  borderColor: string
  icon: string
  isActive: boolean
  onClick: () => void
}

const SummaryCard = ({
  title,
  count,
  color,
  textColor,
  borderColor,
  icon,
  isActive,
  onClick,
}: SummaryCardProps) => (
  <button
    onClick={onClick}
    className={`w-full text-left transition-all duration-200 ${
      isActive ? 'ring-2 ring-blue-500 ring-offset-2' : ''
    }`}
  >
    <Card className={`${color} border ${borderColor} hover:shadow-md cursor-pointer`}>
      <CardContent className="py-4">
        <div className="flex items-center justify-between">
          <div>
            <p className={`text-sm font-medium ${textColor} opacity-75`}>{title}</p>
            <p className={`text-3xl font-bold ${textColor}`}>{count}</p>
          </div>
          <span className="text-3xl">{icon}</span>
        </div>
      </CardContent>
    </Card>
  </button>
)

export const Dashboard = () => {
  const { tenantData, currentTenant } = useTenantStore()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<HealthStatus | 'all'>('all')
  const [refreshInterval, setRefreshInterval] = useState(30000) // 30 seconds
  const [isTabVisible, setIsTabVisible] = useState(!document.hidden)
  const previousStatusesRef = useRef<Map<string, HealthStatus>>(new Map())
  const [changedServerIds, setChangedServerIds] = useState<Set<string>>(new Set())

  // Handle visibility change - pause polling when tab is hidden
  useEffect(() => {
    const handleVisibilityChange = () => {
      const visible = !document.hidden
      setIsTabVisible(visible)
      if (visible) {
        // Immediately refetch when tab becomes visible
        queryClient.invalidateQueries({ queryKey: ['servers-health'] })
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [queryClient])

  // Fetch health data with auto-refresh (pauses when tab is hidden)
  const {
    data: healthData,
    isLoading,
    error,
    refetch,
    dataUpdatedAt,
  } = useQuery({
    queryKey: ['servers-health'],
    queryFn: healthService.getAllHealth,
    refetchInterval: isTabVisible && refreshInterval ? refreshInterval : false,
    enabled: !!currentTenant,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff
  })

  // Calculate summary from health data
  const summary = useMemo(() => {
    if (!healthData?.servers) {
      return { total: 0, healthy: 0, warning: 0, critical: 0, offline: 0, unknown: 0 }
    }
    return healthService.calculateSummary(healthData.servers)
  }, [healthData?.servers])

  // Update browser tab title with critical/warning count
  useEffect(() => {
    const alertCount = summary.critical + summary.warning
    if (alertCount > 0) {
      document.title = `(${alertCount}) DbTools`
    } else {
      document.title = 'DbTools'
    }

    // Cleanup - reset title on unmount
    return () => {
      document.title = 'DbTools'
    }
  }, [summary.critical, summary.warning])

  // Track status changes for animations
  useEffect(() => {
    if (!healthData?.servers) return

    const newChangedIds = new Set<string>()
    const currentStatuses = new Map<string, HealthStatus>()

    healthData.servers.forEach((server) => {
      currentStatuses.set(server.server_id, server.status)
      const prevStatus = previousStatusesRef.current.get(server.server_id)

      // If we have a previous status and it changed, mark for animation
      if (prevStatus !== undefined && prevStatus !== server.status) {
        newChangedIds.add(server.server_id)
      }
    })

    if (newChangedIds.size > 0) {
      setChangedServerIds(newChangedIds)
      // Clear animation after delay
      const timer = setTimeout(() => setChangedServerIds(new Set()), 2000)
      return () => clearTimeout(timer)
    }

    previousStatusesRef.current = currentStatuses
  }, [healthData?.servers])

  // Filter servers based on status selection
  const filteredServers = useMemo(() => {
    if (!healthData?.servers) return []
    if (statusFilter === 'all') return healthData.servers
    return healthData.servers.filter((s) => s.status === statusFilter)
  }, [healthData?.servers, statusFilter])

  // Format last updated time
  const lastUpdated = useMemo(() => {
    if (!dataUpdatedAt) return null
    return new Date(dataUpdatedAt).toLocaleTimeString()
  }, [dataUpdatedAt])

  const handleCardClick = (status: HealthStatus | 'all') => {
    setStatusFilter(statusFilter === status ? 'all' : status)
  }

  const handleServerClick = (serverId: string) => {
    navigate(`/servers/${serverId}`)
  }

  if (!currentTenant) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Please select a tenant to view the dashboard.</p>
      </div>
    )
  }

  if (isLoading && !healthData) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    )
  }

  // Connection error banner component (shown at top of page)
  const ConnectionErrorBanner = () => {
    if (!error) return null
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-red-500">⚠</span>
          <p className="text-red-700">
            Connection error - retrying automatically...
          </p>
        </div>
        <Button variant="ghost" size="sm" onClick={() => refetch()}>
          Retry Now
        </Button>
      </div>
    )
  }

  // Empty state (also shows error banner if needed)
  if (summary.total === 0 && !error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome to {tenantData?.name || currentTenant || 'DbTools'}
        </h1>
        <Card className="text-center py-12">
          <CardContent>
            <div className="text-gray-400 text-5xl mb-4">🖥️</div>
            <h2 className="text-xl font-semibold text-gray-700 mb-2">No servers configured</h2>
            <p className="text-gray-500 mb-4">
              Add your first SQL Server to start monitoring.
            </p>
            <Button onClick={() => navigate('/servers')}>Add Server</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Connection Error Banner */}
      <ConnectionErrorBanner />

      {/* Header with refresh controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-900">
          {tenantData?.name || currentTenant || 'Dashboard'}
        </h1>
        <div className="flex items-center gap-3 text-sm text-gray-500">
          {lastUpdated && <span>Last updated: {lastUpdated}</span>}
          <Button variant="ghost" size="sm" onClick={() => refetch()}>
            Refresh
          </Button>
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="text-sm border rounded px-2 py-1"
          >
            <option value={15000}>15s</option>
            <option value={30000}>30s</option>
            <option value={60000}>1m</option>
            <option value={300000}>5m</option>
            <option value={0}>Off</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <SummaryCard
          title="Total"
          count={summary.total}
          color="bg-blue-50"
          textColor="text-blue-700"
          borderColor="border-blue-200"
          icon="🖥️"
          isActive={statusFilter === 'all'}
          onClick={() => handleCardClick('all')}
        />
        <SummaryCard
          title="Healthy"
          count={summary.healthy}
          color={statusColors.healthy.bg}
          textColor={statusColors.healthy.text}
          borderColor={statusColors.healthy.border}
          icon="✓"
          isActive={statusFilter === 'healthy'}
          onClick={() => handleCardClick('healthy')}
        />
        <SummaryCard
          title="Warning"
          count={summary.warning}
          color={statusColors.warning.bg}
          textColor={statusColors.warning.text}
          borderColor={statusColors.warning.border}
          icon="⚠"
          isActive={statusFilter === 'warning'}
          onClick={() => handleCardClick('warning')}
        />
        <SummaryCard
          title="Critical"
          count={summary.critical}
          color={statusColors.critical.bg}
          textColor={statusColors.critical.text}
          borderColor={statusColors.critical.border}
          icon="✕"
          isActive={statusFilter === 'critical'}
          onClick={() => handleCardClick('critical')}
        />
        <SummaryCard
          title="Offline"
          count={summary.offline}
          color={statusColors.offline.bg}
          textColor={statusColors.offline.text}
          borderColor={statusColors.offline.border}
          icon="○"
          isActive={statusFilter === 'offline'}
          onClick={() => handleCardClick('offline')}
        />
        <SummaryCard
          title="Unknown"
          count={summary.unknown}
          color={statusColors.unknown.bg}
          textColor={statusColors.unknown.text}
          borderColor={statusColors.unknown.border}
          icon="?"
          isActive={statusFilter === 'unknown'}
          onClick={() => handleCardClick('unknown')}
        />
      </div>

      {/* Server Status Grid */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">
              Server Status
              {statusFilter !== 'all' && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  (filtered: {statusFilter})
                </span>
              )}
            </h2>
            {statusFilter !== 'all' && (
              <Button variant="ghost" size="sm" onClick={() => setStatusFilter('all')}>
                Clear filter
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredServers.map((server) => (
              <ServerStatusCard
                key={server.server_id}
                server={server}
                onClick={() => handleServerClick(server.server_id)}
                hasStatusChanged={changedServerIds.has(server.server_id)}
              />
            ))}
          </div>
          {filteredServers.length === 0 && (
            <p className="text-center text-gray-500 py-8">
              No servers match the selected filter.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

interface ServerStatusCardProps {
  server: ServerHealth
  onClick: () => void
  hasStatusChanged?: boolean
}

const ServerStatusCard = ({ server, onClick, hasStatusChanged }: ServerStatusCardProps) => {
  const colors = statusColors[server.status]

  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-4 rounded-lg border ${colors.border} ${colors.bg}
        hover:shadow-md transition-all duration-200 cursor-pointer
        ${hasStatusChanged ? 'animate-pulse ring-2 ring-offset-2 ring-blue-400' : ''}`}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-gray-900 truncate">{server.name}</h3>
          <p className="text-sm text-gray-500 truncate">{server.hostname}</p>
        </div>
        <Badge variant={statusBadgeVariants[server.status]}>{server.status}</Badge>
      </div>

      {server.status !== 'unknown' && server.status !== 'offline' && (
        <div className="grid grid-cols-3 gap-2 mt-3 text-sm">
          <div>
            <p className="text-gray-500">CPU</p>
            <p className={`font-medium ${getMetricColor(server.cpu_percent, 80, 95)}`}>
              {server.cpu_percent !== null ? `${server.cpu_percent.toFixed(1)}%` : '-'}
            </p>
          </div>
          <div>
            <p className="text-gray-500">Memory</p>
            <p className={`font-medium ${getMetricColor(server.memory_percent, 85, 95)}`}>
              {server.memory_percent !== null ? `${server.memory_percent.toFixed(1)}%` : '-'}
            </p>
          </div>
          <div>
            <p className="text-gray-500">Connections</p>
            <p className="font-medium text-gray-900">
              {server.connection_count !== null ? server.connection_count : '-'}
            </p>
          </div>
        </div>
      )}

      {server.last_collected_at && (
        <p className="text-xs text-gray-400 mt-2">
          Last collected: {new Date(server.last_collected_at).toLocaleString()}
        </p>
      )}

      {!server.collection_enabled && (
        <p className="text-xs text-orange-500 mt-2">Collection disabled</p>
      )}
    </button>
  )
}

const getMetricColor = (
  value: number | null,
  warningThreshold: number,
  criticalThreshold: number
): string => {
  if (value === null) return 'text-gray-500'
  if (value > criticalThreshold) return 'text-red-600'
  if (value > warningThreshold) return 'text-yellow-600'
  return 'text-green-600'
}
