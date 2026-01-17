/**
 * Job service for managing scheduled jobs via API.
 */
import { apiClient } from './api'

export type JobType = 'policy_execution' | 'data_collection' | 'custom_script' | 'alert_check'
export type ScheduleType = 'once' | 'interval' | 'cron' | 'event_triggered'
export type ExecutionStatus = 'pending' | 'running' | 'success' | 'failed' | 'cancelled'

export const JOB_TYPE_LABELS: Record<JobType, string> = {
  policy_execution: 'Policy Execution',
  data_collection: 'Data Collection',
  custom_script: 'Custom Script',
  alert_check: 'Alert Check',
}

export const JOB_TYPE_ICONS: Record<JobType, string> = {
  policy_execution: '📋',
  data_collection: '📊',
  custom_script: '📝',
  alert_check: '🔔',
}

export const SCHEDULE_TYPE_LABELS: Record<ScheduleType, string> = {
  once: 'Run Once',
  interval: 'Interval',
  cron: 'Cron Schedule',
  event_triggered: 'Event Triggered',
}

export interface Job {
  id: string
  name: string
  type: JobType
  configuration: Record<string, unknown>
  schedule_type: ScheduleType
  schedule_config: Record<string, unknown>
  is_enabled: boolean
  next_run_at: string | null
  last_run_at: string | null
  created_at: string
  updated_at: string
  last_status?: ExecutionStatus | null
  last_execution_at?: string | null
  recent_executions?: JobExecution[]
}

export interface JobExecution {
  id: string
  job_id: string
  server_id: string | null
  status: ExecutionStatus
  started_at: string | null
  completed_at: string | null
  result: Record<string, unknown> | null
  error_message: string | null
  created_at: string
  job?: {
    name: string
    type: JobType
  }
  server?: {
    name: string
    hostname: string
  }
}

export interface CreateJobInput {
  name: string
  type: JobType
  schedule_type: ScheduleType
  schedule_config: Record<string, unknown>
  configuration?: Record<string, unknown>
  is_enabled?: boolean
}

export interface UpdateJobInput {
  name?: string
  configuration?: Record<string, unknown>
  schedule_type?: ScheduleType
  schedule_config?: Record<string, unknown>
  is_enabled?: boolean
}

export interface JobsResponse {
  jobs: Job[]
  total: number
  limit: number
  offset: number
}

export interface ExecutionsResponse {
  job_id: string
  executions: JobExecution[]
  total: number
  limit: number
  offset: number
}

export const jobService = {
  /**
   * Get all jobs with optional filters.
   */
  async getAll(options?: {
    type?: JobType
    enabled?: boolean
    limit?: number
    offset?: number
  }): Promise<JobsResponse> {
    const params = new URLSearchParams()
    if (options?.type) params.set('type', options.type)
    if (options?.enabled !== undefined) params.set('enabled', String(options.enabled))
    if (options?.limit) params.set('limit', String(options.limit))
    if (options?.offset) params.set('offset', String(options.offset))

    const query = params.toString()
    const url = query ? `/jobs?${query}` : '/jobs'

    const response = await apiClient.get(url)
    return response.data
  },

  /**
   * Get a single job by ID with recent executions.
   */
  async get(jobId: string): Promise<Job> {
    const response = await apiClient.get(`/jobs/${jobId}`)
    return response.data
  },

  /**
   * Create a new job.
   */
  async create(input: CreateJobInput): Promise<Job> {
    const response = await apiClient.post('/jobs', input)
    return response.data
  },

  /**
   * Update a job.
   */
  async update(jobId: string, input: UpdateJobInput): Promise<Job> {
    const response = await apiClient.put(`/jobs/${jobId}`, input)
    return response.data
  },

  /**
   * Delete a job.
   */
  async delete(jobId: string): Promise<void> {
    await apiClient.delete(`/jobs/${jobId}`)
  },

  /**
   * Trigger immediate execution of a job.
   */
  async runNow(jobId: string): Promise<{ message: string; job: Job }> {
    const response = await apiClient.post(`/jobs/${jobId}/run`)
    return response.data
  },

  /**
   * Enable a job.
   */
  async enable(jobId: string): Promise<Job> {
    const response = await apiClient.post(`/jobs/${jobId}/enable`)
    return response.data
  },

  /**
   * Disable a job.
   */
  async disable(jobId: string): Promise<Job> {
    const response = await apiClient.post(`/jobs/${jobId}/disable`)
    return response.data
  },

  /**
   * Get execution history for a job.
   */
  async getExecutions(
    jobId: string,
    options?: { limit?: number; offset?: number; status?: ExecutionStatus }
  ): Promise<ExecutionsResponse> {
    const params = new URLSearchParams()
    if (options?.limit) params.set('limit', String(options.limit))
    if (options?.offset) params.set('offset', String(options.offset))
    if (options?.status) params.set('status', options.status)

    const query = params.toString()
    const url = query ? `/jobs/${jobId}/executions?${query}` : `/jobs/${jobId}/executions`

    const response = await apiClient.get(url)
    return response.data
  },

  /**
   * Get a specific execution.
   */
  async getExecution(jobId: string, executionId: string): Promise<JobExecution> {
    const response = await apiClient.get(`/jobs/${jobId}/executions/${executionId}`)
    return response.data
  },
}

/**
 * Format schedule config for display.
 */
export function formatSchedule(scheduleType: ScheduleType, config: Record<string, unknown>): string {
  switch (scheduleType) {
    case 'interval': {
      const seconds = config.interval_seconds as number
      if (seconds >= 86400) return `Every ${Math.floor(seconds / 86400)} day(s)`
      if (seconds >= 3600) return `Every ${Math.floor(seconds / 3600)} hour(s)`
      if (seconds >= 60) return `Every ${Math.floor(seconds / 60)} minute(s)`
      return `Every ${seconds} seconds`
    }
    case 'cron':
      return `Cron: ${config.expression}`
    case 'once':
      return config.run_at ? `Once at ${new Date(config.run_at as string).toLocaleString()}` : 'Run Once'
    case 'event_triggered':
      return 'Event Triggered'
    default:
      return scheduleType
  }
}
