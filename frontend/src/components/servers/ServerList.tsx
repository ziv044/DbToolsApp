import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Server, ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react'
import { Badge } from '../ui/Badge'
import { Input } from '../ui/Input'
import type { Server as ServerType } from '../../services/serverService'

const statusVariants: Record<string, 'success' | 'error' | 'warning' | 'default'> = {
  healthy: 'success',
  online: 'success',
  critical: 'error',
  offline: 'error',
  warning: 'warning',
  unknown: 'default',
}

type SortKey = 'name' | 'hostname' | 'status' | 'created_at'
type SortDirection = 'asc' | 'desc'

interface SortConfig {
  key: SortKey
  direction: SortDirection
}

interface ServerListProps {
  servers: ServerType[]
  onBulkAction?: (ids: string[], action: string) => void
}

const ITEMS_PER_PAGE = 20

export const ServerList = ({ servers, onBulkAction }: ServerListProps) => {
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const [sortConfig, setSortConfig] = useState<SortConfig | null>(null)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [currentPage, setCurrentPage] = useState(1)

  // Filter servers by search query
  const filteredServers = useMemo(() => {
    if (!searchQuery.trim()) return servers
    const query = searchQuery.toLowerCase()
    return servers.filter(
      (server) =>
        server.name.toLowerCase().includes(query) ||
        server.hostname.toLowerCase().includes(query) ||
        (server.instance_name?.toLowerCase().includes(query) ?? false)
    )
  }, [servers, searchQuery])

  // Sort servers
  const sortedServers = useMemo(() => {
    if (!sortConfig) return filteredServers
    return [...filteredServers].sort((a, b) => {
      const aValue = a[sortConfig.key] ?? ''
      const bValue = b[sortConfig.key] ?? ''
      if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1
      if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1
      return 0
    })
  }, [filteredServers, sortConfig])

  // Paginate servers
  const totalPages = Math.ceil(sortedServers.length / ITEMS_PER_PAGE)
  const paginatedServers = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE
    return sortedServers.slice(start, start + ITEMS_PER_PAGE)
  }, [sortedServers, currentPage])

  // Reset to page 1 when search changes
  useMemo(() => {
    setCurrentPage(1)
  }, [searchQuery])

  const handleSort = (key: SortKey) => {
    setSortConfig((current) => {
      if (current?.key === key) {
        if (current.direction === 'asc') return { key, direction: 'desc' }
        if (current.direction === 'desc') return null
      }
      return { key, direction: 'asc' }
    })
  }

  const handleSelectAll = () => {
    if (selectedIds.size === paginatedServers.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(paginatedServers.map((s) => s.id)))
    }
  }

  const handleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const handleRowClick = (id: string) => {
    navigate(`/servers/${id}`)
  }

  const SortIcon = ({ column }: { column: SortKey }) => {
    if (sortConfig?.key !== column) {
      return <ChevronsUpDown className="h-4 w-4 text-gray-400" />
    }
    return sortConfig.direction === 'asc' ? (
      <ChevronUp className="h-4 w-4 text-blue-500" />
    ) : (
      <ChevronDown className="h-4 w-4 text-blue-500" />
    )
  }

  const isAllSelected = paginatedServers.length > 0 && selectedIds.size === paginatedServers.length

  return (
    <div className="space-y-4">
      {/* Search and bulk actions */}
      <div className="flex items-center justify-between gap-4">
        <div className="w-80">
          <Input
            placeholder="Search by name or host..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        {selectedIds.size > 0 && onBulkAction && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">{selectedIds.size} selected</span>
            <button
              onClick={() => onBulkAction(Array.from(selectedIds), 'delete')}
              className="px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-md"
            >
              Delete
            </button>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto border border-gray-200 rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="w-12 px-4 py-3">
                <input
                  type="checkbox"
                  checked={isAllSelected}
                  onChange={handleSelectAll}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none"
                onClick={() => handleSort('name')}
              >
                <div className="flex items-center gap-1">
                  Name
                  <SortIcon column="name" />
                </div>
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none"
                onClick={() => handleSort('hostname')}
              >
                <div className="flex items-center gap-1">
                  Host
                  <SortIcon column="hostname" />
                </div>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Auth Type
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none"
                onClick={() => handleSort('status')}
              >
                <div className="flex items-center gap-1">
                  Status
                  <SortIcon column="status" />
                </div>
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none"
                onClick={() => handleSort('created_at')}
              >
                <div className="flex items-center gap-1">
                  Added
                  <SortIcon column="created_at" />
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {paginatedServers.map((server) => (
              <tr
                key={server.id}
                className="hover:bg-gray-50 cursor-pointer"
                onClick={() => handleRowClick(server.id)}
              >
                <td className="px-4 py-4 whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                  <input
                    type="checkbox"
                    checked={selectedIds.has(server.id)}
                    onChange={() => handleSelect(server.id)}
                    className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <Server className="h-5 w-5 text-gray-400 mr-3" />
                    <span className="font-medium text-gray-900">{server.name}</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {server.instance_name
                    ? `${server.hostname}\\${server.instance_name}`
                    : server.port === 1433
                      ? server.hostname
                      : `${server.hostname},${server.port}`}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {server.auth_type === 'windows' ? 'Windows' : 'SQL Server'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <Badge variant={statusVariants[server.status] ?? 'default'}>
                    {server.status}
                  </Badge>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(server.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">
            Showing {(currentPage - 1) * ITEMS_PER_PAGE + 1} to{' '}
            {Math.min(currentPage * ITEMS_PER_PAGE, sortedServers.length)} of {sortedServers.length}{' '}
            servers
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

      {/* No results */}
      {filteredServers.length === 0 && searchQuery && (
        <div className="text-center py-8">
          <p className="text-gray-500">No servers match "{searchQuery}"</p>
        </div>
      )}
    </div>
  )
}
