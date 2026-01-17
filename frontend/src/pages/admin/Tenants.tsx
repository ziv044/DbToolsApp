import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, RefreshCw } from 'lucide-react'
import { Button, Card, CardHeader, CardContent, Spinner, toast } from '../../components/ui'
import { TenantList, TenantForm } from '../../components/admin'
import { tenantService } from '../../services/tenantService'
import type { CreateTenantInput } from '../../services/tenantService'

export const AdminTenants = () => {
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [updatingSlug, setUpdatingSlug] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['admin-tenants'],
    queryFn: tenantService.getAll,
  })

  const createMutation = useMutation({
    mutationFn: (input: CreateTenantInput) => tenantService.create(input),
    onSuccess: (tenant) => {
      toast.success('Tenant created', `${tenant.name} has been created successfully.`)
      queryClient.invalidateQueries({ queryKey: ['admin-tenants'] })
      queryClient.invalidateQueries({ queryKey: ['tenants'] })
      setIsFormOpen(false)
    },
    onError: (err) => {
      const message = err instanceof Error ? err.message : 'Failed to create tenant'
      toast.error('Creation failed', message)
    },
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ slug, status }: { slug: string; status: 'active' | 'suspended' }) => {
      setUpdatingSlug(slug)
      return tenantService.update(slug, { status })
    },
    onSuccess: (tenant) => {
      toast.success('Status updated', `${tenant.name} has been ${tenant.status}.`)
      queryClient.invalidateQueries({ queryKey: ['admin-tenants'] })
      queryClient.invalidateQueries({ queryKey: ['tenants'] })
    },
    onError: (err) => {
      const message = err instanceof Error ? err.message : 'Failed to update status'
      toast.error('Update failed', message)
    },
    onSettled: () => {
      setUpdatingSlug(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (slug: string) => {
      setUpdatingSlug(slug)
      return tenantService.delete(slug)
    },
    onSuccess: () => {
      toast.success('Tenant deleted', 'The tenant has been deleted successfully.')
      queryClient.invalidateQueries({ queryKey: ['admin-tenants'] })
      queryClient.invalidateQueries({ queryKey: ['tenants'] })
    },
    onError: (err) => {
      const message = err instanceof Error ? err.message : 'Failed to delete tenant'
      toast.error('Deletion failed', message)
    },
    onSettled: () => {
      setUpdatingSlug(null)
    },
  })

  const handleSuspend = (slug: string) => {
    updateStatusMutation.mutate({ slug, status: 'suspended' })
  }

  const handleActivate = (slug: string) => {
    updateStatusMutation.mutate({ slug, status: 'active' })
  }

  const handleDelete = (slug: string) => {
    deleteMutation.mutate(slug)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Tenant Management</h1>
        <div className="flex items-center gap-3">
          <Button variant="secondary" onClick={() => refetch()} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={() => setIsFormOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Tenant
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Tenants</h2>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner size="lg" />
              <span className="ml-3 text-gray-500">Loading tenants...</span>
            </div>
          ) : isError ? (
            <div className="text-center py-12">
              <p className="text-red-600 mb-4">
                Error loading tenants: {error instanceof Error ? error.message : 'Unknown error'}
              </p>
              <Button variant="secondary" onClick={() => refetch()}>
                Try Again
              </Button>
            </div>
          ) : (
            <TenantList
              tenants={data?.tenants || []}
              onSuspend={handleSuspend}
              onActivate={handleActivate}
              onDelete={handleDelete}
              isUpdating={updatingSlug}
            />
          )}
        </CardContent>
      </Card>

      <TenantForm
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={createMutation.mutate}
        isLoading={createMutation.isPending}
      />
    </div>
  )
}
