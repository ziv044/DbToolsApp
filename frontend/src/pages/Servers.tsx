import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Server, RefreshCw } from 'lucide-react'
import { Card, CardHeader, CardContent, Button, Spinner } from '../components/ui'
import { AddServerModal, ServerList } from '../components/servers'
import { serverService } from '../services/serverService'
import { toast } from '../components/ui/toastStore'

export const Servers = () => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['servers'],
    queryFn: serverService.getAll,
    staleTime: 30_000,
  })

  const servers = data?.servers ?? []

  const handleBulkAction = async (ids: string[], action: string) => {
    if (action === 'delete') {
      if (!window.confirm(`Delete ${ids.length} server(s)?`)) return

      try {
        await Promise.all(ids.map((id) => serverService.delete(id)))
        toast.success(`Deleted ${ids.length} server(s)`)
        await queryClient.invalidateQueries({ queryKey: ['servers'] })
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
          <Button variant="secondary" onClick={() => refetch()} disabled={isFetching}>
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
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner size="lg" />
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
