import { apiClient, handleApiError } from './api'

export interface TestConnectionParams {
  hostname: string
  port: number
  instance_name?: string
  auth_type: 'sql' | 'windows'
  username?: string
  password?: string
}

export interface TestConnectionResult {
  success: boolean
  version?: string
  edition?: string
  product_version?: string
  has_view_server_state?: boolean
  is_supported_version?: boolean
  error?: string
  error_code?: string
}

export interface CreateServerInput {
  name: string
  hostname: string
  port: number
  instance_name?: string
  auth_type: 'sql' | 'windows'
  username?: string
  password?: string
  validate?: boolean
}

export interface ServerLabel {
  id: string
  name: string
  color: string
}

export interface Server {
  id: string
  name: string
  hostname: string
  port: number
  instance_name?: string
  auth_type: 'sql' | 'windows'
  username?: string
  status: string
  last_checked?: string
  created_at: string
  labels?: ServerLabel[]
}

export const serverService = {
  testConnection: async (params: TestConnectionParams): Promise<TestConnectionResult> => {
    try {
      const { data } = await apiClient.post<TestConnectionResult>(
        '/servers/test-connection',
        params
      )
      return data
    } catch (error) {
      return {
        success: false,
        error: handleApiError(error),
        error_code: 'REQUEST_FAILED',
      }
    }
  },

  create: async (input: CreateServerInput): Promise<Server> => {
    const { data } = await apiClient.post<Server>('/servers', {
      ...input,
      validate: true,
    })
    return data
  },

  getAll: async (): Promise<{ servers: Server[]; total: number }> => {
    const { data } = await apiClient.get<{ servers: Server[]; total: number }>('/servers')
    return data
  },

  getById: async (id: string): Promise<Server> => {
    const { data } = await apiClient.get<Server>(`/servers/${id}`)
    return data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/servers/${id}`)
  },
}
