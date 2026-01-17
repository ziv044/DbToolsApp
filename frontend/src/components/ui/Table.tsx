import type { ReactNode } from 'react'

interface TableProps {
  children: ReactNode
  className?: string
}

export const Table = ({ children, className = '' }: TableProps) => {
  return (
    <div className="overflow-x-auto">
      <table className={`min-w-full divide-y divide-gray-200 ${className}`}>{children}</table>
    </div>
  )
}

export const TableHeader = ({ children, className = '' }: TableProps) => {
  return <thead className={`bg-gray-50 ${className}`}>{children}</thead>
}

export const TableBody = ({ children, className = '' }: TableProps) => {
  return <tbody className={`bg-white divide-y divide-gray-200 ${className}`}>{children}</tbody>
}

export const TableRow = ({ children, className = '' }: TableProps) => {
  return <tr className={`hover:bg-gray-50 ${className}`}>{children}</tr>
}

interface TableCellProps extends TableProps {
  header?: boolean
  colSpan?: number
}

export const TableCell = ({
  children,
  className = '',
  header = false,
  colSpan,
}: TableCellProps) => {
  if (header) {
    return (
      <th
        colSpan={colSpan}
        className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${className}`}
      >
        {children}
      </th>
    )
  }
  return (
    <td
      colSpan={colSpan}
      className={`px-6 py-4 whitespace-nowrap text-sm text-gray-900 ${className}`}
    >
      {children}
    </td>
  )
}
