/**
 * Activity service for managing activity log via API.
 */
import { apiClient } from './api'

export interface ActivityLog {
  id: string
  action: string
  entity_type: string | null
  entity_id: string | null
  details: Record<string, unknown> | null
  created_at: string
}

export interface ActivitiesResponse {
  activities: ActivityLog[]
  total: number
  limit: number
  offset: number
}

export interface ActivityFilters {
  action_types: string[]
  entity_types: string[]
}

export interface EntityActivitiesResponse {
  activities: ActivityLog[]
  entity_type: string
  entity_id: string
}

export const ACTION_LABELS: Record<string, string> = {
  alert_triggered: 'Alert Triggered',
  alert_resolved: 'Alert Resolved',
  alert_acknowledged: 'Alert Acknowledged',
  job_executed: 'Job Executed',
  job_failed: 'Job Failed',
  policy_deployed: 'Policy Deployed',
  server_online: 'Server Online',
  server_offline: 'Server Offline',
  server_added: 'Server Added',
  server_deleted: 'Server Deleted',
  group_created: 'Group Created',
  group_deleted: 'Group Deleted',
  config_changed: 'Config Changed',
}

export const ENTITY_TYPE_LABELS: Record<string, string> = {
  alert: 'Alert',
  job: 'Job',
  policy: 'Policy',
  server: 'Server',
  group: 'Group',
}

export const activityService = {
  /**
   * Get activity log entries with optional filters.
   */
  async getActivities(options?: {
    action?: string
    entity_type?: string
    entity_id?: string
    search?: string
    start_date?: string
    end_date?: string
    limit?: number
    offset?: number
  }): Promise<ActivitiesResponse> {
    const params = new URLSearchParams()
    if (options?.action) params.set('action', options.action)
    if (options?.entity_type) params.set('entity_type', options.entity_type)
    if (options?.entity_id) params.set('entity_id', options.entity_id)
    if (options?.search) params.set('search', options.search)
    if (options?.start_date) params.set('start_date', options.start_date)
    if (options?.end_date) params.set('end_date', options.end_date)
    if (options?.limit) params.set('limit', String(options.limit))
    if (options?.offset) params.set('offset', String(options.offset))

    const query = params.toString()
    const url = query ? `/activity?${query}` : '/activity'

    const response = await apiClient.get(url)
    return response.data
  },

  /**
   * Get a single activity entry by ID.
   */
  async getActivity(activityId: string): Promise<ActivityLog> {
    const response = await apiClient.get(`/activity/${activityId}`)
    return response.data
  },

  /**
   * Get available filter options.
   */
  async getFilters(): Promise<ActivityFilters> {
    const response = await apiClient.get('/activity/filters')
    return response.data
  },

  /**
   * Get activity for a specific entity.
   */
  async getEntityActivities(
    entityType: string,
    entityId: string,
    limit?: number
  ): Promise<EntityActivitiesResponse> {
    const params = new URLSearchParams()
    if (limit) params.set('limit', String(limit))

    const query = params.toString()
    const url = query
      ? `/activity/entity/${entityType}/${entityId}?${query}`
      : `/activity/entity/${entityType}/${entityId}`

    const response = await apiClient.get(url)
    return response.data
  },

  /**
   * Get CSV export URL with current filters.
   */
  getExportUrl(options?: {
    action?: string
    entity_type?: string
    entity_id?: string
    search?: string
    start_date?: string
    end_date?: string
  }): string {
    const params = new URLSearchParams()
    if (options?.action) params.set('action', options.action)
    if (options?.entity_type) params.set('entity_type', options.entity_type)
    if (options?.entity_id) params.set('entity_id', options.entity_id)
    if (options?.search) params.set('search', options.search)
    if (options?.start_date) params.set('start_date', options.start_date)
    if (options?.end_date) params.set('end_date', options.end_date)

    const query = params.toString()
    return query ? `/api/activity/export?${query}` : '/api/activity/export'
  },
}

/**
 * Format action for display.
 */
export function formatAction(action: string): string {
  return ACTION_LABELS[action] || action.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

/**
 * Format entity type for display.
 */
export function formatEntityType(entityType: string | null): string {
  if (!entityType) return '-'
  return ENTITY_TYPE_LABELS[entityType] || entityType.charAt(0).toUpperCase() + entityType.slice(1)
}
