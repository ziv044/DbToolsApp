import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  RefreshCw,
  Search,
  Download,
  FileText,
  Bell,
  Server,
  Calendar,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { Card, CardHeader, CardContent, Button, Spinner } from '../components/ui'
import {
  activityService,
  formatAction,
  formatEntityType,
} from '../services/activityService'
import type { ActivityLog } from '../services/activityService'

const ITEMS_PER_PAGE = 50

export const Activity = () => {
  const [actionFilter, setActionFilter] = useState<string>('')
  const [entityTypeFilter, setEntityTypeFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [debouncedSearch, setDebouncedSearch] = useState<string>('')
  const [currentPage, setCurrentPage] = useState(1)
  const [isTabVisible, setIsTabVisible] = useState(!document.hidden)

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery)
      setCurrentPage(1)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  // Handle visibility change
  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsTabVisible(!document.hidden)
    }
    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [])

  // Get available filters
  const { data: filters } = useQuery({
    queryKey: ['activity', 'filters'],
    queryFn: () => activityService.getFilters(),
  })

  // Get activities
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['activity', actionFilter, entityTypeFilter, debouncedSearch, currentPage],
    queryFn: () =>
      activityService.getActivities({
        action: actionFilter || undefined,
        entity_type: entityTypeFilter || undefined,
        search: debouncedSearch || undefined,
        limit: ITEMS_PER_PAGE,
        offset: (currentPage - 1) * ITEMS_PER_PAGE,
      }),
    refetchInterval: isTabVisible ? 30_000 : false,
  })

  const activities = data?.activities ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / ITEMS_PER_PAGE)

  const handleExport = () => {
    const url = activityService.getExportUrl({
      action: actionFilter || undefined,
      entity_type: entityTypeFilter || undefined,
      search: debouncedSearch || undefined,
    })
    window.open(url, '_blank')
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Activity Log</h1>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
          <Button variant="secondary" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <select
          value={actionFilter}
          onChange={(e) => {
            setActionFilter(e.target.value)
            setCurrentPage(1)
          }}
          className="px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Actions</option>
          {filters?.action_types.map((action) => (
            <option key={action} value={action}>
              {formatAction(action)}
            </option>
          ))}
        </select>

        <select
          value={entityTypeFilter}
          onChange={(e) => {
            setEntityTypeFilter(e.target.value)
            setCurrentPage(1)
          }}
          className="px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Entity Types</option>
          {filters?.entity_types.map((type) => (
            <option key={type} value={type}>
              {formatEntityType(type)}
            </option>
          ))}
        </select>

        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search activities..."
            className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Recent Activity</h2>
            <span className="text-sm text-gray-500">
              {total} total entries
            </span>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : activities.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No activity found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {debouncedSearch || actionFilter || entityTypeFilter
                  ? 'Try adjusting your filters.'
                  : 'Activity will appear here as actions are performed.'}
              </p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b text-left text-sm text-gray-500">
                      <th className="pb-3 font-medium">Timestamp</th>
                      <th className="pb-3 font-medium">Action</th>
                      <th className="pb-3 font-medium">Entity Type</th>
                      <th className="pb-3 font-medium">Entity</th>
                      <th className="pb-3 font-medium">Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activities.map((activity) => (
                      <ActivityRow key={activity.id} activity={activity} />
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4 pt-4 border-t">
                  <span className="text-sm text-gray-500">
                    Showing {(currentPage - 1) * ITEMS_PER_PAGE + 1} to{' '}
                    {Math.min(currentPage * ITEMS_PER_PAGE, total)} of {total}
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className="p-2 text-gray-600 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </button>
                    <span className="text-sm text-gray-600">
                      Page {currentPage} of {totalPages}
                    </span>
                    <button
                      onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className="p-2 text-gray-600 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

interface ActivityRowProps {
  activity: ActivityLog
}

const ActivityRow = ({ activity }: ActivityRowProps) => {
  const getEntityLink = (): string | null => {
    if (!activity.entity_type || !activity.entity_id) return null

    switch (activity.entity_type) {
      case 'server':
        return `/servers/${activity.entity_id}`
      case 'job':
        return `/jobs/${activity.entity_id}`
      case 'policy':
        return `/policies/${activity.entity_id}`
      case 'group':
        return `/groups/${activity.entity_id}`
      default:
        return null
    }
  }

  const getEntityIcon = () => {
    switch (activity.entity_type) {
      case 'server':
        return <Server className="h-4 w-4 text-gray-400" />
      case 'alert':
        return <Bell className="h-4 w-4 text-gray-400" />
      default:
        return <FileText className="h-4 w-4 text-gray-400" />
    }
  }

  const getActionColor = (action: string): string => {
    if (action.includes('failed') || action.includes('error') || action.includes('offline')) {
      return 'text-red-600'
    }
    if (action.includes('triggered')) {
      return 'text-yellow-600'
    }
    if (action.includes('resolved') || action.includes('online') || action.includes('success')) {
      return 'text-green-600'
    }
    return 'text-gray-900'
  }

  const entityLink = getEntityLink()
  const entityName = String(activity.details?.name || activity.details?.rule_name || activity.entity_id || '')

  return (
    <tr className="border-b last:border-0 hover:bg-gray-50">
      <td className="py-3 text-sm">
        <div className="flex items-center gap-2 text-gray-600">
          <Calendar className="h-4 w-4" />
          {new Date(activity.created_at).toLocaleString()}
        </div>
      </td>
      <td className="py-3">
        <span className={`font-medium ${getActionColor(activity.action)}`}>
          {formatAction(activity.action)}
        </span>
      </td>
      <td className="py-3 text-sm text-gray-600">
        {formatEntityType(activity.entity_type)}
      </td>
      <td className="py-3">
        <div className="flex items-center gap-2">
          {getEntityIcon()}
          {entityLink ? (
            <Link to={entityLink} className="text-blue-600 hover:underline text-sm">
              {entityName || '-'}
            </Link>
          ) : (
            <span className="text-sm text-gray-600">{entityName || '-'}</span>
          )}
        </div>
      </td>
      <td className="py-3 text-sm text-gray-600 max-w-xs truncate">
        {activity.details ? (
          <span title={JSON.stringify(activity.details, null, 2)}>
            {formatDetails(activity.details)}
          </span>
        ) : (
          '-'
        )}
      </td>
    </tr>
  )
}

function formatDetails(details: Record<string, unknown>): string {
  // Extract key information from details
  const parts: string[] = []

  if (details.metric_type) {
    parts.push(`${details.metric_type}`)
  }
  if (details.metric_value !== undefined) {
    parts.push(`value: ${details.metric_value}`)
  }
  if (details.threshold !== undefined) {
    parts.push(`threshold: ${details.threshold}`)
  }
  if (details.severity) {
    parts.push(`${details.severity}`)
  }
  if (details.status) {
    parts.push(`status: ${details.status}`)
  }

  if (parts.length > 0) {
    return parts.join(', ')
  }

  // Fallback to JSON
  const json = JSON.stringify(details)
  return json.length > 50 ? json.slice(0, 47) + '...' : json
}
