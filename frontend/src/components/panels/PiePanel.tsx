import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from 'recharts'
import { Panel } from './Panel'

interface PieData {
  label: string
  value: number
  color?: string
}

interface PiePanelProps {
  title: string
  data: PieData[] | null | undefined
  isLoading: boolean
  error?: Error | null
  height?: number
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#6366f1', '#14b8a6']

export const PiePanel = ({ title, data, isLoading, error, height = 250 }: PiePanelProps) => {
  const chartData = data?.map(d => ({ name: d.label, value: d.value })) || []

  return (
    <Panel
      title={title}
      isLoading={isLoading}
      error={error}
      isEmpty={!data?.length}
      height={height}
    >
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={70}
            innerRadius={35}
            paddingAngle={2}
            label={({ percent }) =>
              (percent ?? 0) > 0.05 ? `${((percent ?? 0) * 100).toFixed(0)}%` : ''
            }
            labelLine={false}
          >
            {chartData.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value) => [(value ?? 0).toLocaleString(), 'Count']}
          />
          <Legend
            layout="vertical"
            align="right"
            verticalAlign="middle"
            iconSize={8}
            wrapperStyle={{ fontSize: '11px' }}
          />
        </PieChart>
      </ResponsiveContainer>
    </Panel>
  )
}
