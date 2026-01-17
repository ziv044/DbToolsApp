import { useState, useEffect, useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Server, RefreshCw } from 'lucide-react'
import { Card, CardHeader, CardContent, Button, Spinner } from '../components/ui'
import { AddServerModal, ServerList } from '../components/servers'
import { serverService } from '../services/serverService'
import type { Server as ServerType } from '../services/serverService'
import { healthService } from '../services/healthService'
import { toast } from '../components/ui/toastStore'
import { useTenantStore } from '../stores/tenantStore'

export const Servers = () => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [isTabVisible, setIsTabVisible] = useState(!document.hidden)
  const queryClient = useQueryClient()
  const currentTenant = useTenantStore((state) => state.currentTenant)

  // Handle visibility change - pause polling when tab is hidden
  useEffect(() => {
    const handleVisibilityChange = () => {
      const visible = !document.hidden
      setIsTabVisible(visible)
<<<<<<< HEAD
      if (visible && currentTenant) {
        queryClient.invalidateQueries({ queryKey: ['servers', currentTenant] })
        queryClient.invalidateQueries({ queryKey: ['servers-health', currentTenant] })
=======
      if (visible) {
        queryClient.invalidateQueries({ queryKey: ['servers'] })
        queryClient.invalidateQueries({ queryKey: ['servers-health'] })
>>>>>>> 85076bd4595ec67f3055bb0e27bd18f0c8db67ed
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
<<<<<<< HEAD
  }, [queryClient, currentTenant])

  const { data, isLoading, refetch, isFetching, error } = useQuery({
    queryKey: ['servers', currentTenant],
    queryFn: async () => {
      console.log('[Servers] Fetching for tenant:', currentTenant)
      const result = await serverService.getAll()
      console.log('[Servers] Result:', result)
      return result
    },
=======
  }, [queryClient])

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['servers'],
    queryFn: serverService.getAll,
>>>>>>> 85076bd4595ec67f3055bb0e27bd18f0c8db67ed
    staleTime: 30_000,
    enabled: !!currentTenant,
  })

<<<<<<< HEAD
  // Debug: log state changes
  console.log('[Servers] Render state:', { currentTenant, isLoading, hasData: !!data, serverCount: data?.servers?.length, error })

  // Also fetch health data for real-time status
  const { data: healthData } = useQuery({
    queryKey: ['servers-health', currentTenant],
=======
  // Also fetch health data for real-time status
  const { data: healthData } = useQuery({
    queryKey: ['servers-health'],
>>>>>>> 85076bd4595ec67f3055bb0e27bd18f0c8db67ed
    queryFn: healthService.getAllHealth,
    refetchInterval: isTabVisible ? 30_000 : false,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
<<<<<<< HEAD
    enabled: !!currentTenant,
=======
>>>>>>> 85076bd4595ec67f3055bb0e27bd18f0c8db67ed
  })

  // Merge server data with health status
  const servers: ServerType[] = useMemo(() => {
    const baseServers = data?.servers ?? []
    if (!healthData?.servers) return baseServers

    const healthMap = new Map(healthData.servers.map((h) => [h.server_id, h]))

    return baseServers.map((server) => {
      const health = healthMap.get(server.id)
      if (health) {
        return {
          ...server,
          status: health.status as ServerType['status'],
        }
      }
      return server
    })
  }, [data?.servers, healthData?.servers])

  const handleBulkAction = async (ids: string[], action: string) => {
    if (action === 'delete') {
      if (!window.confirm(`Delete ${ids.length} server(s)?`)) return

      try {
        await Promise.all(ids.map((id) => serverService.delete(id)))
        toast.success(`Deleted ${ids.length} server(s)`)
        await queryClient.invalidateQueries({ queryKey: ['servers', currentTenant] })
      } catch {
        toast.error('Failed to delete servers')
      }
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Servers</h1>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            onClick={() => {
              refetch()
<<<<<<< HEAD
              queryClient.invalidateQueries({ queryKey: ['servers-health', currentTenant] })
=======
              queryClient.invalidateQueries({ queryKey: ['servers-health'] })
>>>>>>> 85076bd4595ec67f3055bb0e27bd18f0c8db67ed
            }}
            disabled={isFetching}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={() => setIsAddModalOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add Server
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">SQL Server Connections</h2>
        </CardHeader>
        <CardContent>
          {!currentTenant ? (
            <div className="text-center py-12">
              <Server className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No tenant selected</h3>
              <p className="mt-1 text-sm text-gray-500">
                Please select a tenant from the dropdown above.
              </p>
            </div>
          ) : isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <Server className="mx-auto h-12 w-12 text-red-400" />
              <h3 className="mt-2 text-sm font-medium text-red-900">Error loading servers</h3>
              <p className="mt-1 text-sm text-red-500">
                {error instanceof Error ? error.message : 'Failed to fetch servers'}
              </p>
              <div className="mt-4">
                <Button variant="secondary" onClick={() => refetch()}>
                  Try Again
                </Button>
              </div>
            </div>
          ) : servers.length === 0 ? (
            <div className="text-center py-12">
              <Server className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No servers</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by adding a SQL Server instance.
              </p>
              <div className="mt-6">
                <Button onClick={() => setIsAddModalOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Server
                </Button>
              </div>
            </div>
          ) : (
            <ServerList servers={servers} onBulkAction={handleBulkAction} />
          )}
        </CardContent>
      </Card>

      <AddServerModal isOpen={isAddModalOpen} onClose={() => setIsAddModalOpen(false)} />
    </div>
  )
}
