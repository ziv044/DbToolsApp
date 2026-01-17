import { apiClient } from './api'

export interface RunningQuery {
  id: string
  server_id: string
  server_name: string | null
  collected_at: string
  session_id: number
  request_id: number | null
  database_name: string | null
  query_text: string | null
  start_time: string | null
  duration_ms: number | null
  status: string | null
  wait_type: string | null
  wait_time_ms: number | null
  cpu_time_ms: number | null
  logical_reads: number | null
  physical_reads: number | null
  writes: number | null
}

export interface RunningQueriesResponse {
  time_range: string
  server_id: string | null
  total: number
  queries: RunningQuery[]
}

export interface GetRunningQueriesParams {
  server_id?: string
  range?: string
  limit?: number
}

export const runningQueriesService = {
  getAll: async (params: GetRunningQueriesParams = {}): Promise<RunningQueriesResponse> => {
    const { data } = await apiClient.get<RunningQueriesResponse>('/running-queries', {
      params: {
        server_id: params.server_id,
        range: params.range || '1h',
        limit: params.limit || 500,
      },
    })
    return data
  },
}

export const COLUMN_DEFINITIONS = {
  server_name: { label: 'Server', defaultVisible: true },
  database_name: { label: 'Database', defaultVisible: true },
  session_id: { label: 'Session ID', defaultVisible: true },
  status: { label: 'Status', defaultVisible: true },
  duration_ms: { label: 'Duration (ms)', defaultVisible: true },
  cpu_time_ms: { label: 'CPU Time (ms)', defaultVisible: true },
  wait_type: { label: 'Wait Type', defaultVisible: true },
  wait_time_ms: { label: 'Wait Time (ms)', defaultVisible: false },
  logical_reads: { label: 'Logical Reads', defaultVisible: false },
  physical_reads: { label: 'Physical Reads', defaultVisible: false },
  writes: { label: 'Writes', defaultVisible: false },
  query_text: { label: 'Query', defaultVisible: true },
  collected_at: { label: 'Collected At', defaultVisible: false },
  start_time: { label: 'Start Time', defaultVisible: false },
} as const

export type ColumnKey = keyof typeof COLUMN_DEFINITIONS

export const DEFAULT_VISIBLE_COLUMNS: ColumnKey[] = Object.entries(COLUMN_DEFINITIONS)
  .filter(([, config]) => config.defaultVisible)
  .map(([key]) => key as ColumnKey)
