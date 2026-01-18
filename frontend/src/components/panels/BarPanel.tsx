import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { Panel } from './Panel'

interface BarData {
  label: string
  value: number
}

interface BarPanelProps {
  title: string
  data: BarData[] | null | undefined
  isLoading: boolean
  error?: Error | null
  color?: string
  unit?: string
  height?: number
}

export const BarPanel = ({
  title,
  data,
  isLoading,
  error,
  color = '#3b82f6',
  unit = '',
  height = 250
}: BarPanelProps) => {
  // Truncate labels for display
  const chartData = data?.map(d => ({
    ...d,
    displayLabel: d.label.length > 25 ? d.label.slice(0, 25) + '...' : d.label,
    fullLabel: d.label
  })) || []

  return (
    <Panel
      title={title}
      isLoading={isLoading}
      error={error}
      isEmpty={!data?.length}
      height={height}
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ left: 10, right: 20, top: 10, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" horizontal={true} vertical={false} />
          <XAxis
            type="number"
            tick={{ fontSize: 10 }}
            tickFormatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}k${unit}` : `${v}${unit}`}
            stroke="#9ca3af"
          />
          <YAxis
            type="category"
            dataKey="displayLabel"
            width={100}
            tick={{ fontSize: 10 }}
            stroke="#9ca3af"
          />
          <Tooltip
            formatter={(value) => [`${(value ?? 0).toLocaleString()}${unit}`, 'Value']}
            labelFormatter={(_, payload) => payload?.[0]?.payload?.fullLabel || ''}
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '0.375rem',
              fontSize: '12px',
            }}
          />
          <Bar dataKey="value" fill={color} radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </Panel>
  )
}
