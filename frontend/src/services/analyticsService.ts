import { apiClient } from './api'

export interface PieData {
  label: string
  value: number
}

export interface BarData {
  label: string
  value: number
  session_id?: number
}

export interface TimeSeriesData {
  time: string
  value: number
}

export interface TableColumn {
  key: string
  label: string
  sortable?: boolean
}

export interface TableData {
  columns: TableColumn[]
  rows: Record<string, unknown>[]
  total_rows: number
  collected_at: string | null
}

export interface BlockingNode {
  session_id: number
  login_name: string | null
  host_name: string | null
  program_name: string | null
  database_name: string | null
  query_text: string | null
  duration_ms: number | null
  cpu_time_ms: number | null
  wait_type: string | null
  blocked: BlockingNode[]
}

export interface BlockingChainsResponse {
  chains: BlockingNode[]
  total_blocked_sessions: number
  collected_at: string | null
}

export interface TopQueriesResponse {
  metric: string
  data: BarData[]
  unit: string
}

export interface BreakdownResponse {
  dimension: string
  data: PieData[]
  total: number
}

export interface TimeSeriesResponse {
  metric: string
  interval: string
  data: TimeSeriesData[]
  unit: string
}

export interface DateRange {
  start: Date
  end: Date
}

const formatDate = (d: Date): string => d.toISOString()

export const analyticsService = {
  getRunningQueries: async (serverId: string): Promise<TableData> => {
    const response = await apiClient.get('/analytics/queries/running', {
      params: { server_id: serverId }
    })
    return response.data
  },

  getBlockingChains: async (serverId: string): Promise<BlockingChainsResponse> => {
    const response = await apiClient.get('/analytics/queries/blocking-chains', {
      params: { server_id: serverId }
    })
    return response.data
  },

  getTopQueries: async (
    serverId: string,
    dateRange: DateRange,
    metric: 'duration' | 'cpu' | 'io' = 'duration',
    limit: number = 10
  ): Promise<TopQueriesResponse> => {
    const response = await apiClient.get('/analytics/queries/top', {
      params: {
        server_id: serverId,
        start: formatDate(dateRange.start),
        end: formatDate(dateRange.end),
        metric,
        limit
      }
    })
    return response.data
  },

  getBreakdown: async (
    serverId: string,
    dateRange: DateRange,
    dimension: 'database' | 'login' | 'host' | 'application' | 'wait-type'
  ): Promise<BreakdownResponse> => {
    const response = await apiClient.get(`/analytics/breakdowns/by-${dimension}`, {
      params: {
        server_id: serverId,
        start: formatDate(dateRange.start),
        end: formatDate(dateRange.end)
      }
    })
    return response.data
  },

  getTimeSeries: async (
    serverId: string,
    dateRange: DateRange,
    metric: 'query-count' | 'avg-duration' | 'total-cpu' = 'query-count'
  ): Promise<TimeSeriesResponse> => {
    const response = await apiClient.get(`/analytics/timeseries/${metric}`, {
      params: {
        server_id: serverId,
        start: formatDate(dateRange.start),
        end: formatDate(dateRange.end)
      }
    })
    return response.data
  }
}
