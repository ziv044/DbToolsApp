import type { ReactNode } from 'react'
import { Card, CardHeader, CardContent, Spinner } from '../ui'

interface PanelProps {
  title: string
  subtitle?: string
  isLoading: boolean
  error?: Error | null
  isEmpty?: boolean
  emptyMessage?: string
  height?: number
  children: ReactNode
  actions?: ReactNode
}

export const Panel = ({
  title,
  subtitle,
  isLoading,
  error,
  isEmpty,
  emptyMessage = 'No data available',
  height = 300,
  children,
  actions
}: PanelProps) => {
  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between py-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
          {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
        </div>
        {actions}
      </CardHeader>
      <CardContent style={{ height }}>
        {isLoading ? (
          <div className="h-full flex items-center justify-center">
            <Spinner size="md" />
          </div>
        ) : error ? (
          <div className="h-full flex items-center justify-center text-red-500 text-sm">
            Failed to load data
          </div>
        ) : isEmpty ? (
          <div className="h-full flex items-center justify-center text-gray-400 text-sm">
            {emptyMessage}
          </div>
        ) : (
          children
        )}
      </CardContent>
    </Card>
  )
}
