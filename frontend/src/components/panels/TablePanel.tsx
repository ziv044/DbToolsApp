import { useState } from 'react'
import { ChevronUp, ChevronDown } from 'lucide-react'
import { Panel } from './Panel'

interface Column {
  key: string
  label: string
  sortable?: boolean
  width?: number
  render?: (value: unknown, row: Record<string, unknown>) => React.ReactNode
}

interface TablePanelProps {
  title: string
  subtitle?: string
  columns: Column[]
  rows: Record<string, unknown>[] | null | undefined
  isLoading: boolean
  error?: Error | null
  onRowClick?: (row: Record<string, unknown>) => void
  height?: number
  maxRows?: number
}

export const TablePanel = ({
  title,
  subtitle,
  columns,
  rows,
  isLoading,
  error,
  onRowClick,
  height = 300,
  maxRows = 50
}: TablePanelProps) => {
  const [sortKey, setSortKey] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')

  const sortedRows = [...(rows || [])].sort((a, b) => {
    if (!sortKey) return 0
    const aVal = a[sortKey]
    const bVal = b[sortKey]
    if (aVal === null || aVal === undefined) return 1
    if (bVal === null || bVal === undefined) return -1
    const cmp = aVal < bVal ? -1 : aVal > bVal ? 1 : 0
    return sortDir === 'asc' ? cmp : -cmp
  }).slice(0, maxRows)

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  return (
    <Panel
      title={title}
      subtitle={subtitle}
      isLoading={isLoading}
      error={error}
      isEmpty={!rows?.length}
      height={height}
    >
      <div className="overflow-auto h-full -mx-6 -my-4">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 sticky top-0">
            <tr>
              {columns.map(col => (
                <th
                  key={col.key}
                  className={`px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap
                    ${col.sortable ? 'cursor-pointer hover:bg-gray-100 select-none' : ''}`}
                  style={{ width: col.width }}
                  onClick={() => col.sortable && handleSort(col.key)}
                >
                  <div className="flex items-center gap-1">
                    {col.label}
                    {sortKey === col.key && (
                      sortDir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {sortedRows.map((row, i) => (
              <tr
                key={i}
                className={onRowClick ? 'cursor-pointer hover:bg-blue-50' : 'hover:bg-gray-50'}
                onClick={() => onRowClick?.(row)}
              >
                {columns.map(col => (
                  <td key={col.key} className="px-4 py-2 text-gray-700 truncate max-w-xs">
                    {col.render
                      ? col.render(row[col.key], row)
                      : String(row[col.key] ?? '-')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  )
}
