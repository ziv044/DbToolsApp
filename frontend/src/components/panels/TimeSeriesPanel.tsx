import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { Panel } from './Panel'

interface TimeSeriesData {
  time: string
  value: number
}

interface TimeSeriesPanelProps {
  title: string
  data: TimeSeriesData[] | null | undefined
  isLoading: boolean
  error?: Error | null
  color?: string
  unit?: string
  height?: number
}

const formatTime = (time: string): string => {
  const date = new Date(time)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export const TimeSeriesPanel = ({
  title,
  data,
  isLoading,
  error,
  color = '#3b82f6',
  unit = '',
  height = 250
}: TimeSeriesPanelProps) => {
  // Calculate domain
  const maxValue = Math.max(...(data?.map(d => d.value) || [0]))
  const domain: [number, number] = [0, Math.max(10, Math.ceil(maxValue * 1.1))]

  return (
    <Panel
      title={title}
      isLoading={isLoading}
      error={error}
      isEmpty={!data?.length}
      height={height}
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data || []} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 10 }}
            tickFormatter={formatTime}
            stroke="#9ca3af"
          />
          <YAxis
            domain={domain}
            tick={{ fontSize: 10 }}
            stroke="#9ca3af"
            width={50}
            tickFormatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v}
          />
          <Tooltip
            labelFormatter={(label) => new Date(String(label)).toLocaleString()}
            formatter={(value) => [`${(value ?? 0).toLocaleString()}${unit}`, title]}
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '0.375rem',
              fontSize: '12px',
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
    </Panel>
  )
}
