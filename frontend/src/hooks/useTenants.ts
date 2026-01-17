import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import type { Tenant } from '../stores/tenantStore'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api'

interface TenantsResponse {
  tenants: Tenant[]
  total: number
}

export const useTenants = () => {
  return useQuery<TenantsResponse>({
    queryKey: ['tenants'],
    queryFn: async () => {
      const response = await axios.get<Tenant[]>(`${API_BASE_URL}/tenants`)
      // API returns array directly, wrap it in expected format
      const tenants = response.data
      return { tenants, total: tenants.length }
    },
  })
}
