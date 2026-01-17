import { apiClient } from './api'

export type TimeRange = '1h' | '6h' | '24h' | '7d' | '30d'
export type MetricType = 'cpu' | 'memory' | 'connections' | 'batch_requests'

export interface MetricDataPoint {
  time: string
  value: number | null
}

export interface MetricsResponse {
  server_id: string
  time_range: string
  data_points: number
  cpu?: MetricDataPoint[]
  memory?: MetricDataPoint[]
  connections?: MetricDataPoint[]
  batch_requests?: MetricDataPoint[]
}

export interface Snapshot {
  id: string
  server_id: string
  collected_at: string
  cpu_percent: number | null
  memory_percent: number | null
  connection_count: number | null
  batch_requests_sec: number | null
  page_life_expectancy: number | null
  blocked_processes: number | null
  extended_metrics: Record<string, unknown> | null
  status: string | null
}

export const metricsService = {
  getMetrics: async (
    serverId: string,
    range: TimeRange = '24h',
    metric?: MetricType
  ): Promise<MetricsResponse> => {
    const params = new URLSearchParams({ range })
    if (metric) {
      params.append('metric', metric)
    }
    const { data } = await apiClient.get<MetricsResponse>(
      `/servers/${serverId}/metrics?${params.toString()}`
    )
    return data
  },

  getLatestSnapshot: async (serverId: string): Promise<Snapshot | null> => {
    const { data } = await apiClient.get<{ snapshot: Snapshot | null }>(
      `/servers/${serverId}/metrics/latest`
    )
    return data.snapshot
  },
}

// Time range display labels
export const timeRangeLabels: Record<TimeRange, string> = {
  '1h': 'Last 1 hour',
  '6h': 'Last 6 hours',
  '24h': 'Last 24 hours',
  '7d': 'Last 7 days',
  '30d': 'Last 30 days',
}
