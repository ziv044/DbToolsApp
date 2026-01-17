import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api'

export interface Tenant {
  id: string
  name: string
  slug: string
  status: 'active' | 'suspended'
  created_at: string
  updated_at: string
  settings: Record<string, unknown>
}

export interface TenantsResponse {
  tenants: Tenant[]
  total: number
}

export interface CreateTenantInput {
  name: string
  slug: string
}

export interface UpdateTenantInput {
  name?: string
  status?: 'active' | 'suspended'
  settings?: Record<string, unknown>
}

export const tenantService = {
  getAll: async (): Promise<TenantsResponse> => {
    const { data } = await axios.get<Tenant[]>(`${API_BASE_URL}/tenants`)
    // API returns array directly, wrap it in expected format
    return { tenants: data, total: data.length }
  },

  getBySlug: async (slug: string): Promise<Tenant> => {
    const { data } = await axios.get<Tenant>(`${API_BASE_URL}/tenants/${slug}`)
    return data
  },

  create: async (input: CreateTenantInput): Promise<Tenant> => {
    const { data } = await axios.post<Tenant>(`${API_BASE_URL}/tenants`, input)
    return data
  },

  update: async (slug: string, input: UpdateTenantInput): Promise<Tenant> => {
    const { data } = await axios.patch<Tenant>(`${API_BASE_URL}/tenants/${slug}`, input)
    return data
  },

  delete: async (slug: string): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/tenants/${slug}`)
  },
}

// Slug validation and generation utilities
const SLUG_REGEX = /^[a-z0-9][a-z0-9-]{1,48}[a-z0-9]$/

export const validateSlug = (slug: string): boolean => {
  return SLUG_REGEX.test(slug)
}

export const generateSlug = (name: string): string => {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 50)
}
