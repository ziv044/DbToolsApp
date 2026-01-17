import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { Card, CardHeader, CardContent, Spinner, Button } from '../ui'
import { metricsService, timeRangeLabels } from '../../services/metricsService'
import type { TimeRange, MetricDataPoint } from '../../services/metricsService'

interface MetricsChartsProps {
  serverId: string
}

interface ChartProps {
  data: MetricDataPoint[]
  title: string
  color: string
  unit: string
  domain?: [number, number]
  isLoading?: boolean
}

const formatTime = (time: string, range: TimeRange): string => {
  const date = new Date(time)
  if (range === '1h' || range === '6h') {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  if (range === '24h') {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  return date.toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit' })
}

const MetricChart = ({ data, title, color, unit, domain = [0, 100], isLoading }: ChartProps) => {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        </CardHeader>
        <CardContent>
          <div className="h-48 flex items-center justify-center">
            <Spinner size="md" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        </CardHeader>
        <CardContent>
          <div className="h-48 flex items-center justify-center text-gray-500">
            No data available
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
      </CardHeader>
      <CardContent>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 10 }}
                tickFormatter={(time: string) => formatTime(time, '24h')}
                stroke="#9ca3af"
              />
              <YAxis
                domain={domain}
                tick={{ fontSize: 10 }}
                stroke="#9ca3af"
                width={40}
              />
              <Tooltip
                labelFormatter={(label: string) => new Date(label).toLocaleString()}
                formatter={(value) => {
                  const numValue = typeof value === 'number' ? value : null
                  return [numValue !== null ? `${numValue.toFixed(2)}${unit}` : 'No data', title]
                }}
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '0.5rem',
                  padding: '0.5rem',
                }}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke={color}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}

export const MetricsCharts = ({ serverId }: MetricsChartsProps) => {
  const [timeRange, setTimeRange] = useState<TimeRange>('24h')

  const {
    data: metricsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['server-metrics', serverId, timeRange],
    queryFn: () => metricsService.getMetrics(serverId, timeRange),
    refetchInterval: 60000, // Refresh every minute
  })

  const timeRangeOptions: TimeRange[] = ['1h', '6h', '24h', '7d', '30d']

  // Calculate domain for connections chart
  const connectionsDomain = useMemo(() => {
    if (!metricsData?.connections) return [0, 100] as [number, number]
    const maxVal = Math.max(...metricsData.connections.map((d) => d.value || 0))
    return [0, Math.max(10, Math.ceil(maxVal * 1.1))] as [number, number]
  }, [metricsData?.connections])

  // Calculate domain for batch requests chart
  const batchRequestsDomain = useMemo(() => {
    if (!metricsData?.batch_requests) return [0, 1000] as [number, number]
    const maxVal = Math.max(...metricsData.batch_requests.map((d) => d.value || 0))
    return [0, Math.max(100, Math.ceil(maxVal * 1.1))] as [number, number]
  }, [metricsData?.batch_requests])

  if (error) {
    return (
      <Card>
        <CardContent>
          <div className="text-center py-8">
            <p className="text-red-600 mb-4">Failed to load metrics</p>
            <Button variant="secondary" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Time Range Selector */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Performance Metrics</h2>
        <div className="flex items-center gap-2">
          {timeRangeOptions.map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                timeRange === range
                  ? 'bg-blue-100 text-blue-700 font-medium'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {timeRangeLabels[range]}
            </button>
          ))}
        </div>
      </div>

      {/* Data Points Info */}
      {metricsData && (
        <p className="text-sm text-gray-500">
          {metricsData.data_points} data points in selected range
        </p>
      )}

      {/* Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <MetricChart
          data={metricsData?.cpu || []}
          title="CPU Utilization"
          color="#3b82f6"
          unit="%"
          domain={[0, 100]}
          isLoading={isLoading}
        />
        <MetricChart
          data={metricsData?.memory || []}
          title="Memory Utilization"
          color="#10b981"
          unit="%"
          domain={[0, 100]}
          isLoading={isLoading}
        />
        <MetricChart
          data={metricsData?.connections || []}
          title="Connection Count"
          color="#8b5cf6"
          unit=""
          domain={connectionsDomain}
          isLoading={isLoading}
        />
        <MetricChart
          data={metricsData?.batch_requests || []}
          title="Batch Requests/sec"
          color="#f59e0b"
          unit=""
          domain={batchRequestsDomain}
          isLoading={isLoading}
        />
      </div>
    </div>
  )
}
