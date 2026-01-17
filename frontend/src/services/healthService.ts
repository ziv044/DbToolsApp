import { apiClient } from './api'

export type HealthStatus = 'healthy' | 'warning' | 'critical' | 'offline' | 'unknown'

export interface ServerHealth {
  server_id: string
  name: string
  hostname: string
  status: HealthStatus
  last_collected_at: string | null
  cpu_percent: number | null
  memory_percent: number | null
  connection_count: number | null
  collection_enabled: boolean
}

export interface HealthThresholds {
  cpu_warning: number
  cpu_critical: number
  memory_warning: number
  memory_critical: number
  offline_seconds: number
}

export interface HealthSummary {
  total: number
  healthy: number
  warning: number
  critical: number
  offline: number
  unknown: number
}

export const healthService = {
  getAllHealth: async (): Promise<{ servers: ServerHealth[]; total: number }> => {
    const { data } = await apiClient.get<{ servers: ServerHealth[]; total: number }>(
      '/servers/health'
    )
    return data
  },

  getServerHealth: async (serverId: string): Promise<ServerHealth> => {
    const { data } = await apiClient.get<ServerHealth>(`/servers/${serverId}/health`)
    return data
  },

  getThresholds: async (): Promise<HealthThresholds> => {
    const { data } = await apiClient.get<{ thresholds: HealthThresholds }>(
      '/settings/health-thresholds'
    )
    return data.thresholds
  },

  updateThresholds: async (thresholds: Partial<HealthThresholds>): Promise<HealthThresholds> => {
    const { data } = await apiClient.put<{ thresholds: HealthThresholds }>(
      '/settings/health-thresholds',
      thresholds
    )
    return data.thresholds
  },

  calculateSummary: (servers: ServerHealth[]): HealthSummary => {
    return servers.reduce(
      (acc, server) => {
        acc.total++
        acc[server.status]++
        return acc
      },
      { total: 0, healthy: 0, warning: 0, critical: 0, offline: 0, unknown: 0 }
    )
  },
}
