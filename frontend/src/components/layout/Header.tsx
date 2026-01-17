import { Database } from 'lucide-react'
import { Spinner } from '../ui'
import { useTenants } from '../../hooks/useTenants'
import { useTenantStore } from '../../stores/tenantStore'

export const Header = () => {
  const { data, isLoading, isError, error } = useTenants()
  const { currentTenant, setTenant } = useTenantStore()

  const handleTenantChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const slug = e.target.value
    if (slug) {
      const tenant = data?.tenants.find((t) => t.slug === slug)
      setTenant(slug, tenant)
    }
  }

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Database className="h-8 w-8 text-blue-600" />
          <h1 className="text-xl font-bold text-gray-900">DbTools</h1>
        </div>

        <div className="flex items-center space-x-4">
          <label htmlFor="tenant-select" className="text-sm font-medium text-gray-700">
            Tenant:
          </label>
          {isLoading ? (
            <div className="flex items-center space-x-2">
              <Spinner size="sm" />
              <span className="text-sm text-gray-500">Loading tenants...</span>
            </div>
          ) : isError ? (
            <div className="text-sm text-red-600">
              Error: {error instanceof Error ? error.message : 'Failed to load tenants'}
            </div>
          ) : (
            <select
              id="tenant-select"
              value={currentTenant || ''}
              onChange={handleTenantChange}
              className="block w-48 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="" disabled>
                Select a tenant
              </option>
              {data?.tenants.map((tenant) => (
                <option key={tenant.id} value={tenant.slug}>
                  {tenant.name}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>
    </header>
  )
}
