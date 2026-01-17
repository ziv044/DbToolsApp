import { apiClient } from './api'

export interface CollectionConfig {
  server_id: string
  interval_seconds: number
  enabled: boolean
  metrics_enabled: string[]
  last_collected_at: string | null
  created_at: string | null
  updated_at: string | null
  // Query collection fields
  query_collection_enabled: boolean
  query_collection_interval: number
  query_min_duration_ms: number
  last_query_collected_at: string | null
  // Query collection filters
  query_filter_database: string | null
  query_filter_login: string | null
  query_filter_user: string | null
  query_filter_text_include: string | null
  query_filter_text_exclude: string | null
}

export interface UpdateQueryConfigInput {
  query_collection_interval?: number
  query_min_duration_ms?: number
  query_filter_database?: string | null
  query_filter_login?: string | null
  query_filter_user?: string | null
  query_filter_text_include?: string | null
  query_filter_text_exclude?: string | null
}

export const collectionConfigService = {
  getConfig: async (serverId: string): Promise<CollectionConfig> => {
    const { data } = await apiClient.get<CollectionConfig>(`/servers/${serverId}/collection-config`)
    return data
  },

  updateQueryConfig: async (serverId: string, input: UpdateQueryConfigInput): Promise<CollectionConfig> => {
    const { data } = await apiClient.put<CollectionConfig>(
      `/servers/${serverId}/query-collection/config`,
      input
    )
    return data
  },

  startQueryCollection: async (serverId: string): Promise<{ success: boolean; config: CollectionConfig }> => {
    const { data } = await apiClient.post<{ success: boolean; config: CollectionConfig }>(
      `/servers/${serverId}/query-collection/start`
    )
    return data
  },

  stopQueryCollection: async (serverId: string): Promise<{ success: boolean; config: CollectionConfig }> => {
    const { data } = await apiClient.post<{ success: boolean; config: CollectionConfig }>(
      `/servers/${serverId}/query-collection/stop`
    )
    return data
  },
}
