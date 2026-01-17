import { apiClient } from './api'

export type DeploymentStatusType = 'not_deployed' | 'deployed' | 'outdated' | 'failed'

export interface DeploymentStatusResponse {
  status: DeploymentStatusType
  version?: string
  deployed_at?: string
  error?: string
}

export interface DeploymentResult {
  success: boolean
  version?: string
  deployed_at?: string
  error?: string
  error_step?: string
}

export interface PermissionCheckResult {
  can_deploy: boolean
  can_create_procedure: boolean
  can_create_table: boolean
  can_create_schema: boolean
  can_view_server_state: boolean
  missing_permissions: string[]
}

export const deploymentService = {
  getStatus: async (serverId: string): Promise<DeploymentStatusResponse> => {
    const { data } = await apiClient.get<DeploymentStatusResponse>(
      `/servers/${serverId}/deployment-status`
    )
    return data
  },

  deploy: async (serverId: string): Promise<DeploymentResult> => {
    const { data } = await apiClient.post<DeploymentResult>(
      `/servers/${serverId}/deploy`
    )
    return data
  },

  checkPermissions: async (serverId: string): Promise<PermissionCheckResult> => {
    const { data } = await apiClient.get<PermissionCheckResult>(
      `/servers/${serverId}/permissions`
    )
    return data
  },
}
