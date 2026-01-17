import axios from 'axios'
import { useTenantStore } from '../stores/tenantStore'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api',
})

apiClient.interceptors.request.use((config) => {
  const tenant = useTenantStore.getState().currentTenant
  if (tenant) {
    config.headers['X-Tenant-Slug'] = tenant
  }
  return config
})

export interface ApiError {
  error: {
    code: string
    message: string
  }
}

export const handleApiError = (error: unknown): string => {
  if (axios.isAxiosError(error) && error.response?.data?.error) {
    return error.response.data.error.message
  }
  return 'An unexpected error occurred'
}
