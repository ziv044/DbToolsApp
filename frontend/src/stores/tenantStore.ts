import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Tenant {
  id: string
  name: string
  slug: string
  status: string
}

interface TenantState {
  currentTenant: string | null
  tenantData: Tenant | null
  setTenant: (slug: string, data?: Tenant) => void
  clearTenant: () => void
}

export const useTenantStore = create<TenantState>()(
  persist(
    (set) => ({
      currentTenant: null,
      tenantData: null,
      setTenant: (slug, data) => set({ currentTenant: slug, tenantData: data || null }),
      clearTenant: () => set({ currentTenant: null, tenantData: null }),
    }),
    { name: 'dbtools-tenant' }
  )
)
