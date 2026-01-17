/**
 * Alert service for managing alerts and alert rules via API.
 */
import { apiClient } from './api'

export type AlertSeverity = 'info' | 'warning' | 'critical'
export type AlertStatus = 'active' | 'acknowledged' | 'resolved'
export type AlertOperator = 'gt' | 'gte' | 'lt' | 'lte' | 'eq'

export const SEVERITY_LABELS: Record<AlertSeverity, string> = {
  info: 'Info',
  warning: 'Warning',
  critical: 'Critical',
}

export const SEVERITY_COLORS: Record<AlertSeverity, { bg: string; text: string; icon: string }> = {
  info: { bg: 'bg-blue-100', text: 'text-blue-800', icon: 'text-blue-500' },
  warning: { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: 'text-yellow-500' },
  critical: { bg: 'bg-red-100', text: 'text-red-800', icon: 'text-red-500' },
}

export const STATUS_LABELS: Record<AlertStatus, string> = {
  active: 'Active',
  acknowledged: 'Acknowledged',
  resolved: 'Resolved',
}

export const OPERATOR_LABELS: Record<AlertOperator, string> = {
  gt: '>',
  gte: '>=',
  lt: '<',
  lte: '<=',
  eq: '=',
}

export const METRIC_TYPE_LABELS: Record<string, string> = {
  cpu_percent: 'CPU %',
  memory_percent: 'Memory %',
  connection_count: 'Connections',
  batch_requests_sec: 'Batch Req/s',
  page_life_expectancy: 'Page Life Expectancy',
  blocked_processes: 'Blocked Processes',
}

export interface AlertRule {
  id: string
  name: string
  metric_type: string
  operator: AlertOperator
  threshold: number
  severity: AlertSeverity
  is_enabled: boolean
  created_at: string
  updated_at: string
}

export interface Alert {
  id: string
  rule_id: string
  server_id: string
  status: AlertStatus
  metric_value: number | null
  triggered_at: string
  acknowledged_at: string | null
  acknowledged_by: string | null
  resolved_at: string | null
  notes: string | null
  rule?: {
    name: string
    metric_type: string
    operator: AlertOperator
    threshold: number
    severity: AlertSeverity
  }
  server?: {
    id: string
    name: string
    hostname: string
  }
}

export interface CreateRuleInput {
  name: string
  metric_type: string
  operator: AlertOperator
  threshold: number
  severity: AlertSeverity
  is_enabled?: boolean
}

export interface UpdateRuleInput {
  name?: string
  metric_type?: string
  operator?: AlertOperator
  threshold?: number
  severity?: AlertSeverity
  is_enabled?: boolean
}

export interface AlertRulesResponse {
  rules: AlertRule[]
  total: number
  limit: number
  offset: number
}

export interface AlertsResponse {
  alerts: Alert[]
  total: number
  limit: number
  offset: number
}

export interface AlertCountsResponse {
  counts: Record<AlertSeverity, number>
  total: number
}

export const alertService = {
  // ==================== Alert Rules ====================

  /**
   * Get all alert rules with optional filters.
   */
  async getRules(options?: {
    metric_type?: string
    severity?: AlertSeverity
    enabled?: boolean
    limit?: number
    offset?: number
  }): Promise<AlertRulesResponse> {
    const params = new URLSearchParams()
    if (options?.metric_type) params.set('metric_type', options.metric_type)
    if (options?.severity) params.set('severity', options.severity)
    if (options?.enabled !== undefined) params.set('enabled', String(options.enabled))
    if (options?.limit) params.set('limit', String(options.limit))
    if (options?.offset) params.set('offset', String(options.offset))

    const query = params.toString()
    const url = query ? `/alert-rules?${query}` : '/alert-rules'

    const response = await apiClient.get(url)
    return response.data
  },

  /**
   * Get a single alert rule by ID.
   */
  async getRule(ruleId: string): Promise<AlertRule> {
    const response = await apiClient.get(`/alert-rules/${ruleId}`)
    return response.data
  },

  /**
   * Create a new alert rule.
   */
  async createRule(input: CreateRuleInput): Promise<AlertRule> {
    const response = await apiClient.post('/alert-rules', input)
    return response.data
  },

  /**
   * Update an alert rule.
   */
  async updateRule(ruleId: string, input: UpdateRuleInput): Promise<AlertRule> {
    const response = await apiClient.put(`/alert-rules/${ruleId}`, input)
    return response.data
  },

  /**
   * Delete an alert rule.
   */
  async deleteRule(ruleId: string): Promise<void> {
    await apiClient.delete(`/alert-rules/${ruleId}`)
  },

  /**
   * Enable an alert rule.
   */
  async enableRule(ruleId: string): Promise<AlertRule> {
    const response = await apiClient.post(`/alert-rules/${ruleId}/enable`)
    return response.data
  },

  /**
   * Disable an alert rule.
   */
  async disableRule(ruleId: string): Promise<AlertRule> {
    const response = await apiClient.post(`/alert-rules/${ruleId}/disable`)
    return response.data
  },

  // ==================== Alerts ====================

  /**
   * Get all alerts with optional filters.
   */
  async getAlerts(options?: {
    status?: AlertStatus
    severity?: AlertSeverity
    server_id?: string
    rule_id?: string
    limit?: number
    offset?: number
  }): Promise<AlertsResponse> {
    const params = new URLSearchParams()
    if (options?.status) params.set('status', options.status)
    if (options?.severity) params.set('severity', options.severity)
    if (options?.server_id) params.set('server_id', options.server_id)
    if (options?.rule_id) params.set('rule_id', options.rule_id)
    if (options?.limit) params.set('limit', String(options.limit))
    if (options?.offset) params.set('offset', String(options.offset))

    const query = params.toString()
    const url = query ? `/alerts?${query}` : '/alerts'

    const response = await apiClient.get(url)
    return response.data
  },

  /**
   * Get active (non-resolved) alerts.
   */
  async getActiveAlerts(options?: {
    server_id?: string
    limit?: number
    offset?: number
  }): Promise<AlertsResponse> {
    const params = new URLSearchParams()
    if (options?.server_id) params.set('server_id', options.server_id)
    if (options?.limit) params.set('limit', String(options.limit))
    if (options?.offset) params.set('offset', String(options.offset))

    const query = params.toString()
    const url = query ? `/alerts/active?${query}` : '/alerts/active'

    const response = await apiClient.get(url)
    return response.data
  },

  /**
   * Get alert counts by severity.
   */
  async getAlertCounts(): Promise<AlertCountsResponse> {
    const response = await apiClient.get('/alerts/counts')
    return response.data
  },

  /**
   * Get a single alert by ID.
   */
  async getAlert(alertId: string): Promise<Alert> {
    const response = await apiClient.get(`/alerts/${alertId}`)
    return response.data
  },

  /**
   * Acknowledge an alert.
   */
  async acknowledgeAlert(
    alertId: string,
    options?: { acknowledged_by?: string; notes?: string }
  ): Promise<Alert> {
    const response = await apiClient.post(`/alerts/${alertId}/acknowledge`, options || {})
    return response.data
  },

  /**
   * Resolve an alert.
   */
  async resolveAlert(alertId: string, options?: { notes?: string }): Promise<Alert> {
    const response = await apiClient.post(`/alerts/${alertId}/resolve`, options || {})
    return response.data
  },
}

/**
 * Format duration from triggered_at to now or resolved_at.
 */
export function formatAlertDuration(triggeredAt: string, resolvedAt?: string | null): string {
  const start = new Date(triggeredAt)
  const end = resolvedAt ? new Date(resolvedAt) : new Date()
  const diffMs = end.getTime() - start.getTime()

  const seconds = Math.floor(diffMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) return `${days}d ${hours % 24}h`
  if (hours > 0) return `${hours}h ${minutes % 60}m`
  if (minutes > 0) return `${minutes}m`
  return `${seconds}s`
}

/**
 * Get severity icon color class.
 */
export function getSeverityIcon(severity: AlertSeverity): string {
  return SEVERITY_COLORS[severity].icon
}
