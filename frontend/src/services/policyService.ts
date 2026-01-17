/**
 * Policy service for managing policies via API.
 */
import { apiClient } from './api'

export type PolicyType = 'backup' | 'index_maintenance' | 'integrity_check' | 'custom_script'

export const POLICY_TYPE_LABELS: Record<PolicyType, string> = {
  backup: 'Backup',
  index_maintenance: 'Index Maintenance',
  integrity_check: 'Integrity Check',
  custom_script: 'Custom Script',
}

export const POLICY_TYPE_DESCRIPTIONS: Record<PolicyType, string> = {
  backup: 'Automated database backup with configurable type, compression, and retention',
  index_maintenance: 'Rebuild or reorganize indexes based on fragmentation thresholds',
  integrity_check: 'Run DBCC CHECKDB to verify database integrity',
  custom_script: 'Execute custom T-SQL scripts on target servers',
}

export const POLICY_TYPE_ICONS: Record<PolicyType, string> = {
  backup: '💾',
  index_maintenance: '📊',
  integrity_check: '✓',
  custom_script: '📝',
}

export interface PolicySchema {
  required: string[]
  optional: string[]
  defaults: Record<string, unknown>
  valid_values?: Record<string, string[]>
}

export interface Policy {
  id: string
  name: string
  type: PolicyType
  description: string | null
  configuration: Record<string, unknown>
  version: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface PolicyVersion {
  id: string
  policy_id: string
  version: number
  configuration: Record<string, unknown>
  description: string | null
  created_at: string
}

export interface CreatePolicyInput {
  name: string
  type: PolicyType
  description?: string
  configuration: Record<string, unknown>
  is_active?: boolean
}

export interface UpdatePolicyInput {
  name?: string
  description?: string
  configuration?: Record<string, unknown>
  is_active?: boolean
}

export interface PolicyDeployment {
  id: string
  policy_id: string
  policy_version: number
  group_id: string
  deployed_at: string
  deployed_by: string | null
  group?: {
    name: string
    color: string | null
  }
  policy?: {
    name: string
    type: PolicyType
    is_active: boolean
  }
}

export interface DeployPolicyInput {
  group_ids: string[]
  deployed_by?: string
}

export const policyService = {
  /**
   * Get all policies with optional filters.
   */
  async getAll(options?: { type?: PolicyType; active?: boolean }): Promise<{ policies: Policy[]; total: number }> {
    const params = new URLSearchParams()
    if (options?.type) params.set('type', options.type)
    if (options?.active !== undefined) params.set('active', String(options.active))

    const query = params.toString()
    const url = query ? `/policies?${query}` : '/policies'

    const response = await apiClient.get(url)
    return response.data
  },

  /**
   * Get a single policy by ID.
   */
  async get(policyId: string): Promise<Policy> {
    const response = await apiClient.get(`/policies/${policyId}`)
    return response.data
  },

  /**
   * Create a new policy.
   */
  async create(input: CreatePolicyInput): Promise<Policy> {
    const response = await apiClient.post('/policies', input)
    return response.data
  },

  /**
   * Update a policy.
   */
  async update(policyId: string, input: UpdatePolicyInput): Promise<Policy> {
    const response = await apiClient.put(`/policies/${policyId}`, input)
    return response.data
  },

  /**
   * Delete a policy.
   */
  async delete(policyId: string): Promise<void> {
    await apiClient.delete(`/policies/${policyId}`)
  },

  /**
   * Get version history for a policy.
   */
  async getVersions(policyId: string): Promise<{ policy_id: string; current_version: number; versions: PolicyVersion[] }> {
    const response = await apiClient.get(`/policies/${policyId}/versions`)
    return response.data
  },

  /**
   * Get a specific version of a policy.
   */
  async getVersion(policyId: string, version: number): Promise<PolicyVersion> {
    const response = await apiClient.get(`/policies/${policyId}/versions/${version}`)
    return response.data
  },

  /**
   * Get all policy schemas.
   */
  async getSchemas(): Promise<{ policy_types: PolicyType[]; schemas: Record<PolicyType, PolicySchema> }> {
    const response = await apiClient.get('/policies/schemas')
    return response.data
  },

  /**
   * Get schema for a specific policy type.
   */
  async getSchema(policyType: PolicyType): Promise<{ type: PolicyType; schema: PolicySchema }> {
    const response = await apiClient.get(`/policies/schemas/${policyType}`)
    return response.data
  },

  /**
   * Deploy a policy to server groups.
   */
  async deploy(policyId: string, input: DeployPolicyInput): Promise<{ deployments: PolicyDeployment[]; total: number; warnings?: string[] }> {
    const response = await apiClient.post(`/policies/${policyId}/deploy`, input)
    return response.data
  },

  /**
   * Get all deployments for a policy.
   */
  async getDeployments(policyId: string): Promise<{ policy_id: string; deployments: PolicyDeployment[]; total: number }> {
    const response = await apiClient.get(`/policies/${policyId}/deployments`)
    return response.data
  },

  /**
   * Remove a policy deployment from a group.
   */
  async removeDeployment(policyId: string, groupId: string): Promise<void> {
    await apiClient.delete(`/policies/${policyId}/deployments/${groupId}`)
  },
}
