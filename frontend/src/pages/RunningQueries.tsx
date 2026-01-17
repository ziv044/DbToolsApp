import { useState, useEffect, useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  RefreshCw,
  Search,
  Database,
  Settings2,
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
  X,
} from 'lucide-react'
import { Card, CardHeader, CardContent, Button, Spinner, Badge } from '../components/ui'
import { serverService } from '../services/serverService'
import {
  runningQueriesService,
  COLUMN_DEFINITIONS,
  DEFAULT_VISIBLE_COLUMNS,
  type RunningQuery,
  type ColumnKey,
} from '../services/runningQueriesService'
import { useTenantStore } from '../stores/tenantStore'

type SortDirection = 'asc' | 'desc'

interface SortConfig {
  key: keyof RunningQuery
  direction: SortDirection
}

const TIME_RANGES = [
  { value: '1h', label: 'Last 1 hour' },
  { value: '6h', label: 'Last 6 hours' },
  { value: '24h', label: 'Last 24 hours' },
  { value: '7d', label: 'Last 7 days' },
  { value: '30d', label: 'Last 30 days' },
]

const ITEMS_PER_PAGE = 50

const statusVariants: Record<string, 'success' | 'error' | 'warning' | 'default'> = {
  running: 'success',
  runnable: 'success',
  suspended: 'warning',
  sleeping: 'default',
  background: 'default',
}

export const RunningQueries = () => {
  const [selectedServerId, setSelectedServerId] = useState<string>('')
  const [timeRange, setTimeRange] = useState<string>('1h')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [debouncedSearch, setDebouncedSearch] = useState<string>('')
  const [sortConfig, setSortConfig] = useState<SortConfig | null>({
    key: 'duration_ms',
    direction: 'desc',
  })
  const [visibleColumns, setVisibleColumns] = useState<Set<ColumnKey>>(
    new Set(DEFAULT_VISIBLE_COLUMNS)
  )
  const [showColumnSettings, setShowColumnSettings] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [isTabVisible, setIsTabVisible] = useState(!document.hidden)
  const [expandedQueryId, setExpandedQueryId] = useState<string | null>(null)

  const queryClient = useQueryClient()
  const currentTenant = useTenantStore((state) => state.currentTenant)

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery)
      setCurrentPage(1)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  // Handle visibility change - pause polling when tab is hidden
  useEffect(() => {
    const handleVisibilityChange = () => {
      const visible = !document.hidden
      setIsTabVisible(visible)
      if (visible && currentTenant) {
        queryClient.invalidateQueries({ queryKey: ['running-queries'] })
      }
    }
    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [queryClient, currentTenant])

  // Close column settings when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (showColumnSettings && !(e.target as Element).closest('.column-settings')) {
        setShowColumnSettings(false)
      }
    }
    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [showColumnSettings])

  // Fetch servers for dropdown
  const { data: serversData } = useQuery({
    queryKey: ['servers', currentTenant],
    queryFn: () => serverService.getAll(),
    enabled: !!currentTenant,
  })

  // Fetch running queries
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['running-queries', currentTenant, selectedServerId, timeRange],
    queryFn: () =>
      runningQueriesService.getAll({
        server_id: selectedServerId || undefined,
        range: timeRange,
        limit: 500,
      }),
    enabled: !!currentTenant,
    refetchInterval: isTabVisible ? 30_000 : false,
  })

  const queries = data?.queries ?? []

  // Filter queries by search
  const filteredQueries = useMemo(() => {
    if (!debouncedSearch.trim()) return queries
    const search = debouncedSearch.toLowerCase()
    return queries.filter(
      (q) =>
        q.query_text?.toLowerCase().includes(search) ||
        q.database_name?.toLowerCase().includes(search) ||
        q.server_name?.toLowerCase().includes(search) ||
        q.status?.toLowerCase().includes(search) ||
        q.wait_type?.toLowerCase().includes(search)
    )
  }, [queries, debouncedSearch])

  // Sort queries
  const sortedQueries = useMemo(() => {
    if (!sortConfig) return filteredQueries
    return [...filteredQueries].sort((a, b) => {
      const aValue = a[sortConfig.key] ?? ''
      const bValue = b[sortConfig.key] ?? ''
      if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1
      if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1
      return 0
    })
  }, [filteredQueries, sortConfig])

  // Paginate
  const totalPages = Math.ceil(sortedQueries.length / ITEMS_PER_PAGE)
  const paginatedQueries = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE
    return sortedQueries.slice(start, start + ITEMS_PER_PAGE)
  }, [sortedQueries, currentPage])

  const handleSort = (key: keyof RunningQuery) => {
    setSortConfig((current) => {
      if (current?.key === key) {
        if (current.direction === 'asc') return { key, direction: 'desc' }
        if (current.direction === 'desc') return null
      }
      return { key, direction: 'asc' }
    })
  }

  const toggleColumn = (column: ColumnKey) => {
    setVisibleColumns((prev) => {
      const next = new Set(prev)
      if (next.has(column)) {
        next.delete(column)
      } else {
        next.add(column)
      }
      return next
    })
  }

  const formatDuration = (ms: number | null) => {
    if (ms === null) return '-'
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    if (ms < 3600000) return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`
    return `${Math.floor(ms / 3600000)}h ${Math.floor((ms % 3600000) / 60000)}m`
  }

  const formatNumber = (n: number | null) => {
    if (n === null) return '-'
    return n.toLocaleString()
  }

  const truncateQuery = (text: string | null, maxLen: number = 100) => {
    if (!text) return '-'
    if (text.length <= maxLen) return text
    return text.substring(0, maxLen) + '...'
  }

  const SortIcon = ({ column }: { column: keyof RunningQuery }) => {
    if (sortConfig?.key !== column) {
      return <ChevronsUpDown className="h-4 w-4 text-gray-400" />
    }
    return sortConfig.direction === 'asc' ? (
      <ChevronUp className="h-4 w-4 text-blue-500" />
    ) : (
      <ChevronDown className="h-4 w-4 text-blue-500" />
    )
  }

  const renderCellValue = (query: RunningQuery, column: ColumnKey) => {
    switch (column) {
      case 'server_name':
        return query.server_name || '-'
      case 'database_name':
        return query.database_name || '-'
      case 'session_id':
        return query.session_id
      case 'status':
        return (
          <Badge variant={statusVariants[query.status ?? ''] ?? 'default'}>
            {query.status || '-'}
          </Badge>
        )
      case 'duration_ms':
        return formatDuration(query.duration_ms)
      case 'cpu_time_ms':
        return formatNumber(query.cpu_time_ms)
      case 'wait_type':
        return query.wait_type || '-'
      case 'wait_time_ms':
        return formatNumber(query.wait_time_ms)
      case 'logical_reads':
        return formatNumber(query.logical_reads)
      case 'physical_reads':
        return formatNumber(query.physical_reads)
      case 'writes':
        return formatNumber(query.writes)
      case 'query_text':
        return (
          <span
            className="cursor-pointer hover:text-blue-600"
            onClick={(e) => {
              e.stopPropagation()
              setExpandedQueryId(expandedQueryId === query.id ? null : query.id)
            }}
          >
            {truncateQuery(query.query_text)}
          </span>
        )
      case 'collected_at':
        return query.collected_at ? new Date(query.collected_at).toLocaleString() : '-'
      case 'start_time':
        return query.start_time ? new Date(query.start_time).toLocaleString() : '-'
      default:
        return '-'
    }
  }

  // Get visible columns in order
  const orderedVisibleColumns = (Object.keys(COLUMN_DEFINITIONS) as ColumnKey[]).filter((col) =>
    visibleColumns.has(col)
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Running Queries</h1>
        <Button variant="secondary" onClick={() => refetch()} disabled={isFetching}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Query Snapshots</h2>
            <span className="text-sm text-gray-500">{data?.total ?? 0} total queries</span>
          </div>
        </CardHeader>
        <CardContent>
          {!currentTenant ? (
            <div className="text-center py-12">
              <Database className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No tenant selected</h3>
              <p className="mt-1 text-sm text-gray-500">
                Please select a tenant from the dropdown above.
              </p>
            </div>
          ) : (
            <>
              {/* Filters */}
              <div className="flex flex-wrap items-center gap-4 mb-6">
                {/* Server filter */}
                <div>
                  <select
                    value={selectedServerId}
                    onChange={(e) => {
                      setSelectedServerId(e.target.value)
                      setCurrentPage(1)
                    }}
                    className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All Servers</option>
                    {serversData?.servers.map((server) => (
                      <option key={server.id} value={server.id}>
                        {server.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Time range filter */}
                <div>
                  <select
                    value={timeRange}
                    onChange={(e) => {
                      setTimeRange(e.target.value)
                      setCurrentPage(1)
                    }}
                    className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {TIME_RANGES.map((range) => (
                      <option key={range.value} value={range.value}>
                        {range.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Search */}
                <div className="flex-1 max-w-md">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search queries, databases, servers..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                {/* Column settings */}
                <div className="relative column-settings">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      setShowColumnSettings(!showColumnSettings)
                    }}
                  >
                    <Settings2 className="h-4 w-4 mr-2" />
                    Columns
                  </Button>
                  {showColumnSettings && (
                    <div className="absolute right-0 top-full mt-1 w-56 bg-white border border-gray-200 rounded-lg shadow-lg z-10 p-2">
                      {(Object.keys(COLUMN_DEFINITIONS) as ColumnKey[]).map((key) => (
                        <label
                          key={key}
                          className="flex items-center gap-2 px-2 py-1.5 hover:bg-gray-50 rounded cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={visibleColumns.has(key)}
                            onChange={() => toggleColumn(key)}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-sm">{COLUMN_DEFINITIONS[key].label}</span>
                        </label>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Table */}
              {isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Spinner size="lg" />
                </div>
              ) : queries.length === 0 ? (
                <div className="text-center py-12">
                  <Database className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No running queries</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    No query snapshots found for the selected time range.
                  </p>
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto border border-gray-200 rounded-lg">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          {orderedVisibleColumns.map((column) => (
                            <th
                              key={column}
                              className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none whitespace-nowrap"
                              onClick={() => handleSort(column)}
                            >
                              <div className="flex items-center gap-1">
                                {COLUMN_DEFINITIONS[column].label}
                                <SortIcon column={column} />
                              </div>
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {paginatedQueries.map((query) => (
                          <>
                            <tr key={query.id} className="hover:bg-gray-50">
                              {orderedVisibleColumns.map((column) => (
                                <td
                                  key={column}
                                  className="px-4 py-3 text-sm text-gray-900 whitespace-nowrap"
                                >
                                  {renderCellValue(query, column)}
                                </td>
                              ))}
                            </tr>
                            {expandedQueryId === query.id && (
                              <tr key={`${query.id}-expanded`}>
                                <td
                                  colSpan={orderedVisibleColumns.length}
                                  className="px-4 py-4 bg-gray-50"
                                >
                                  <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                      <div className="text-xs font-medium text-gray-500 uppercase mb-2">
                                        Full Query Text
                                      </div>
                                      <pre className="p-3 bg-gray-900 text-gray-100 rounded-lg text-sm overflow-x-auto max-h-64 overflow-y-auto">
                                        {query.query_text || 'No query text available'}
                                      </pre>
                                    </div>
                                    <button
                                      onClick={() => setExpandedQueryId(null)}
                                      className="ml-4 p-1 hover:bg-gray-200 rounded"
                                    >
                                      <X className="h-4 w-4 text-gray-500" />
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            )}
                          </>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Pagination */}
                  {totalPages > 1 && (
                    <div className="flex items-center justify-between mt-4">
                      <p className="text-sm text-gray-600">
                        Showing {(currentPage - 1) * ITEMS_PER_PAGE + 1} to{' '}
                        {Math.min(currentPage * ITEMS_PER_PAGE, sortedQueries.length)} of{' '}
                        {sortedQueries.length} queries
                      </p>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                          disabled={currentPage === 1}
                          className="px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Previous
                        </button>
                        <span className="text-sm text-gray-600">
                          Page {currentPage} of {totalPages}
                        </span>
                        <button
                          onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                          disabled={currentPage === totalPages}
                          className="px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Next
                        </button>
                      </div>
                    </div>
                  )}

                  {/* No search results */}
                  {filteredQueries.length === 0 && debouncedSearch && (
                    <div className="text-center py-8">
                      <p className="text-gray-500">No queries match "{debouncedSearch}"</p>
                    </div>
                  )}
                </>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
