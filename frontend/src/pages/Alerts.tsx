import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  Bell,
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
  Clock,
  RefreshCw,
  Check,
  Settings,
  Server,
  ChevronDown,
  ChevronRight,
  X,
} from 'lucide-react'
import { Card, CardHeader, CardContent, Button, Spinner } from '../components/ui'
import {
  alertService,
  SEVERITY_LABELS,
  SEVERITY_COLORS,
  STATUS_LABELS,
  OPERATOR_LABELS,
  METRIC_TYPE_LABELS,
  formatAlertDuration,
} from '../services/alertService'
import type { Alert, AlertSeverity, AlertStatus } from '../services/alertService'
import { toast } from '../components/ui/toastStore'

type TabType = 'active' | 'history'

export const Alerts = () => {
  const [activeTab, setActiveTab] = useState<TabType>('active')
  const [severityFilter, setSeverityFilter] = useState<AlertSeverity | ''>('')
  const [statusFilter, setStatusFilter] = useState<AlertStatus | ''>('')
  const [selectedAlerts, setSelectedAlerts] = useState<Set<string>>(new Set())
  const [expandedAlert, setExpandedAlert] = useState<string | null>(null)
  const [isTabVisible, setIsTabVisible] = useState(!document.hidden)
  const queryClient = useQueryClient()

  // Handle visibility change - pause polling when tab is hidden
  useEffect(() => {
    const handleVisibilityChange = () => {
      const visible = !document.hidden
      setIsTabVisible(visible)
      if (visible) {
        queryClient.invalidateQueries({ queryKey: ['alerts'] })
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [queryClient])

  // Query for active alerts
  const {
    data: activeData,
    isLoading: activeLoading,
    refetch: refetchActive,
    isFetching: activeFetching,
  } = useQuery({
    queryKey: ['alerts', 'active', severityFilter],
    queryFn: () => alertService.getActiveAlerts({ limit: 100 }),
    enabled: activeTab === 'active',
    refetchInterval: isTabVisible ? 30_000 : false,
  })

  // Query for alert history (all alerts including resolved)
  const {
    data: historyData,
    isLoading: historyLoading,
    refetch: refetchHistory,
    isFetching: historyFetching,
  } = useQuery({
    queryKey: ['alerts', 'history', severityFilter, statusFilter],
    queryFn: () =>
      alertService.getAlerts({
        severity: severityFilter || undefined,
        status: statusFilter || undefined,
        limit: 100,
      }),
    enabled: activeTab === 'history',
    refetchInterval: isTabVisible ? 30_000 : false,
  })

  // Query for alert counts (for badge)
  const { data: countsData } = useQuery({
    queryKey: ['alerts', 'counts'],
    queryFn: () => alertService.getAlertCounts(),
    refetchInterval: isTabVisible ? 30_000 : false,
  })

  const acknowledgeMutation = useMutation({
    mutationFn: (alertId: string) => alertService.acknowledgeAlert(alertId),
    onSuccess: () => {
      toast.success('Alert acknowledged')
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      setSelectedAlerts(new Set())
    },
    onError: () => toast.error('Failed to acknowledge alert'),
  })

  const resolveMutation = useMutation({
    mutationFn: (alertId: string) => alertService.resolveAlert(alertId),
    onSuccess: () => {
      toast.success('Alert resolved')
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      setSelectedAlerts(new Set())
    },
    onError: () => toast.error('Failed to resolve alert'),
  })

  const handleBulkAcknowledge = async () => {
    const promises = Array.from(selectedAlerts).map((id) =>
      alertService.acknowledgeAlert(id)
    )
    try {
      await Promise.all(promises)
      toast.success(`Acknowledged ${selectedAlerts.size} alert(s)`)
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      setSelectedAlerts(new Set())
    } catch {
      toast.error('Failed to acknowledge some alerts')
    }
  }

  const toggleSelectAlert = (alertId: string) => {
    const newSelected = new Set(selectedAlerts)
    if (newSelected.has(alertId)) {
      newSelected.delete(alertId)
    } else {
      newSelected.add(alertId)
    }
    setSelectedAlerts(newSelected)
  }

  const toggleSelectAll = (alerts: Alert[]) => {
    if (selectedAlerts.size === alerts.length) {
      setSelectedAlerts(new Set())
    } else {
      setSelectedAlerts(new Set(alerts.map((a) => a.id)))
    }
  }

  const isLoading = activeTab === 'active' ? activeLoading : historyLoading
  const isFetching = activeTab === 'active' ? activeFetching : historyFetching
  const refetch = activeTab === 'active' ? refetchActive : refetchHistory

  // Filter alerts based on severity
  let alerts = activeTab === 'active' ? activeData?.alerts ?? [] : historyData?.alerts ?? []
  if (severityFilter && activeTab === 'active') {
    alerts = alerts.filter((a) => a.rule?.severity === severityFilter)
  }

  const criticalCount = countsData?.counts?.critical ?? 0
  const warningCount = countsData?.counts?.warning ?? 0
  const totalActive = countsData?.total ?? 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
          {totalActive > 0 && (
            <div className="flex items-center gap-2">
              {criticalCount > 0 && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-red-100 text-red-800">
                  {criticalCount} critical
                </span>
              )}
              {warningCount > 0 && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-yellow-100 text-yellow-800">
                  {warningCount} warning
                </span>
              )}
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <Link to="/alert-rules">
            <Button variant="secondary">
              <Settings className="h-4 w-4 mr-2" />
              Manage Rules
            </Button>
          </Link>
          <Button variant="secondary" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => {
              setActiveTab('active')
              setSelectedAlerts(new Set())
            }}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'active'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Active Alerts
            {totalActive > 0 && (
              <span className="ml-2 py-0.5 px-2 rounded-full text-xs bg-red-100 text-red-800">
                {totalActive}
              </span>
            )}
          </button>
          <button
            onClick={() => {
              setActiveTab('history')
              setSelectedAlerts(new Set())
            }}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'history'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            History
          </button>
        </nav>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value as AlertSeverity | '')}
          className="px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="warning">Warning</option>
          <option value="info">Info</option>
        </select>

        {activeTab === 'history' && (
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as AlertStatus | '')}
            className="px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
          </select>
        )}

        {selectedAlerts.size > 0 && (
          <Button onClick={handleBulkAcknowledge} variant="secondary" className="ml-auto">
            <Check className="h-4 w-4 mr-2" />
            Acknowledge Selected ({selectedAlerts.size})
          </Button>
        )}
      </div>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">
            {activeTab === 'active' ? 'Active Alerts' : 'Alert History'}
          </h2>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : alerts.length === 0 ? (
            <div className="text-center py-12">
              <Bell className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">
                {activeTab === 'active' ? 'No active alerts' : 'No alerts found'}
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                {activeTab === 'active'
                  ? 'All systems are operating normally.'
                  : 'Try adjusting your filters.'}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b text-left text-sm text-gray-500">
                    <th className="pb-3 pr-2">
                      <input
                        type="checkbox"
                        checked={selectedAlerts.size === alerts.length && alerts.length > 0}
                        onChange={() => toggleSelectAll(alerts)}
                        className="rounded border-gray-300"
                      />
                    </th>
                    <th className="pb-3 font-medium">Severity</th>
                    <th className="pb-3 font-medium">Server</th>
                    <th className="pb-3 font-medium">Rule</th>
                    <th className="pb-3 font-medium">Triggered</th>
                    <th className="pb-3 font-medium">Duration</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {alerts.map((alert) => (
                    <AlertRow
                      key={alert.id}
                      alert={alert}
                      isSelected={selectedAlerts.has(alert.id)}
                      isExpanded={expandedAlert === alert.id}
                      onSelect={() => toggleSelectAlert(alert.id)}
                      onExpand={() =>
                        setExpandedAlert(expandedAlert === alert.id ? null : alert.id)
                      }
                      onAcknowledge={() => acknowledgeMutation.mutate(alert.id)}
                      onResolve={() => resolveMutation.mutate(alert.id)}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Alert Detail Modal */}
      {expandedAlert && (
        <AlertDetailModal
          alert={alerts.find((a) => a.id === expandedAlert)!}
          onClose={() => setExpandedAlert(null)}
          onAcknowledge={() => acknowledgeMutation.mutate(expandedAlert)}
          onResolve={() => resolveMutation.mutate(expandedAlert)}
        />
      )}
    </div>
  )
}

interface AlertRowProps {
  alert: Alert
  isSelected: boolean
  isExpanded: boolean
  onSelect: () => void
  onExpand: () => void
  onAcknowledge: () => void
  onResolve: () => void
}

const AlertRow = ({
  alert,
  isSelected,
  isExpanded,
  onSelect,
  onExpand,
  onAcknowledge,
  onResolve,
}: AlertRowProps) => {
  const severity = alert.rule?.severity ?? 'info'
  const isActive = alert.status !== 'resolved'

  return (
    <tr className="border-b last:border-0 hover:bg-gray-50">
      <td className="py-3 pr-2">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onSelect}
          className="rounded border-gray-300"
        />
      </td>
      <td className="py-3">
        <SeverityBadge severity={severity} />
      </td>
      <td className="py-3">
        <div className="flex items-center gap-2">
          <Server className="h-4 w-4 text-gray-400" />
          {alert.server ? (
            <Link
              to={`/servers/${alert.server.id}`}
              className="text-blue-600 hover:underline"
            >
              {alert.server.name}
            </Link>
          ) : (
            <span className="text-gray-400">Unknown</span>
          )}
        </div>
      </td>
      <td className="py-3">
        <span className="font-medium">{alert.rule?.name ?? 'Unknown Rule'}</span>
        <div className="text-xs text-gray-500">
          {alert.rule?.metric_type
            ? METRIC_TYPE_LABELS[alert.rule.metric_type] || alert.rule.metric_type
            : ''}{' '}
          {alert.rule?.operator ? OPERATOR_LABELS[alert.rule.operator] : ''}{' '}
          {alert.rule?.threshold}
        </div>
      </td>
      <td className="py-3 text-sm text-gray-600">
        {new Date(alert.triggered_at).toLocaleString()}
      </td>
      <td className="py-3">
        <span className="flex items-center gap-1 text-sm text-gray-600">
          <Clock className="h-4 w-4" />
          {formatAlertDuration(alert.triggered_at, alert.resolved_at)}
        </span>
      </td>
      <td className="py-3">
        <StatusBadge status={alert.status} />
      </td>
      <td className="py-3">
        <div className="flex items-center gap-1">
          <button
            onClick={onExpand}
            className="p-1.5 text-gray-600 hover:bg-gray-100 rounded"
            title="View Details"
          >
            {isExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>
          {isActive && alert.status === 'active' && (
            <button
              onClick={onAcknowledge}
              className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
              title="Acknowledge"
            >
              <Check className="h-4 w-4" />
            </button>
          )}
          {isActive && (
            <button
              onClick={onResolve}
              className="p-1.5 text-green-600 hover:bg-green-50 rounded"
              title="Resolve"
            >
              <CheckCircle className="h-4 w-4" />
            </button>
          )}
        </div>
      </td>
    </tr>
  )
}

interface SeverityBadgeProps {
  severity: AlertSeverity
}

const SeverityBadge = ({ severity }: SeverityBadgeProps) => {
  const colors = SEVERITY_COLORS[severity]
  const Icon =
    severity === 'critical' ? AlertCircle : severity === 'warning' ? AlertTriangle : Info

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full ${colors.bg} ${colors.text}`}
    >
      <Icon className="h-3 w-3" />
      {SEVERITY_LABELS[severity]}
    </span>
  )
}

interface StatusBadgeProps {
  status: AlertStatus
}

const StatusBadge = ({ status }: StatusBadgeProps) => {
  const config: Record<AlertStatus, { color: string; icon: typeof CheckCircle }> = {
    active: { color: 'bg-red-100 text-red-800', icon: AlertCircle },
    acknowledged: { color: 'bg-yellow-100 text-yellow-800', icon: Clock },
    resolved: { color: 'bg-green-100 text-green-800', icon: CheckCircle },
  }

  const { color, icon: Icon } = config[status]

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full ${color}`}>
      <Icon className="h-3 w-3" />
      {STATUS_LABELS[status]}
    </span>
  )
}

interface AlertDetailModalProps {
  alert: Alert
  onClose: () => void
  onAcknowledge: () => void
  onResolve: () => void
}

const AlertDetailModal = ({ alert, onClose, onAcknowledge, onResolve }: AlertDetailModalProps) => {
  const severity = alert.rule?.severity ?? 'info'
  const isActive = alert.status !== 'resolved'

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <SeverityBadge severity={severity} />
              <StatusBadge status={alert.status} />
            </div>
            <button
              onClick={onClose}
              className="p-1 text-gray-400 hover:text-gray-600 rounded"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <h2 className="text-xl font-semibold mb-4">{alert.rule?.name ?? 'Alert Details'}</h2>

          <dl className="space-y-3">
            <div>
              <dt className="text-sm font-medium text-gray-500">Server</dt>
              <dd className="mt-1">
                {alert.server ? (
                  <Link
                    to={`/servers/${alert.server.id}`}
                    className="text-blue-600 hover:underline"
                  >
                    {alert.server.name} ({alert.server.hostname})
                  </Link>
                ) : (
                  <span className="text-gray-400">Unknown</span>
                )}
              </dd>
            </div>

            <div>
              <dt className="text-sm font-medium text-gray-500">Metric</dt>
              <dd className="mt-1">
                {alert.rule?.metric_type
                  ? METRIC_TYPE_LABELS[alert.rule.metric_type] || alert.rule.metric_type
                  : 'Unknown'}
              </dd>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">Current Value</dt>
                <dd className="mt-1 text-lg font-semibold text-red-600">
                  {alert.metric_value !== null ? alert.metric_value.toFixed(2) : 'N/A'}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Threshold</dt>
                <dd className="mt-1 text-lg">
                  {alert.rule?.operator ? OPERATOR_LABELS[alert.rule.operator] : ''}{' '}
                  {alert.rule?.threshold}
                </dd>
              </div>
            </div>

            <div>
              <dt className="text-sm font-medium text-gray-500">Triggered At</dt>
              <dd className="mt-1">{new Date(alert.triggered_at).toLocaleString()}</dd>
            </div>

            <div>
              <dt className="text-sm font-medium text-gray-500">Duration</dt>
              <dd className="mt-1">
                {formatAlertDuration(alert.triggered_at, alert.resolved_at)}
              </dd>
            </div>

            {alert.acknowledged_at && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Acknowledged</dt>
                <dd className="mt-1">
                  {new Date(alert.acknowledged_at).toLocaleString()}
                  {alert.acknowledged_by && ` by ${alert.acknowledged_by}`}
                </dd>
              </div>
            )}

            {alert.resolved_at && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Resolved At</dt>
                <dd className="mt-1">{new Date(alert.resolved_at).toLocaleString()}</dd>
              </div>
            )}

            {alert.notes && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Notes</dt>
                <dd className="mt-1 text-sm text-gray-600">{alert.notes}</dd>
              </div>
            )}
          </dl>

          {isActive && (
            <div className="mt-6 flex gap-2">
              {alert.status === 'active' && (
                <Button variant="secondary" onClick={onAcknowledge}>
                  <Check className="h-4 w-4 mr-2" />
                  Acknowledge
                </Button>
              )}
              <Button onClick={onResolve}>
                <CheckCircle className="h-4 w-4 mr-2" />
                Resolve
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
