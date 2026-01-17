import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, Play, Square, HelpCircle } from 'lucide-react'
import { Card, CardHeader, CardContent, Button, Spinner, Badge } from '../components/ui'
import { serverService } from '../services/serverService'
import { collectionConfigService, type UpdateQueryConfigInput } from '../services/collectionConfigService'
import { useTenantStore } from '../stores/tenantStore'
import { toast } from '../components/ui/toastStore'

export const QueryCollectionConfig = () => {
  const { id: serverId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const currentTenant = useTenantStore((state) => state.currentTenant)

  // Form state
  const [interval, setInterval] = useState(30)
  const [minDuration, setMinDuration] = useState(0)
  const [filterDatabase, setFilterDatabase] = useState('')
  const [filterLogin, setFilterLogin] = useState('')
  const [filterUser, setFilterUser] = useState('')
  const [filterTextInclude, setFilterTextInclude] = useState('')
  const [filterTextExclude, setFilterTextExclude] = useState('')
  const [isDirty, setIsDirty] = useState(false)

  // Fetch server info
  const { data: server } = useQuery({
    queryKey: ['server', currentTenant, serverId],
    queryFn: () => serverService.getById(serverId!),
    enabled: !!currentTenant && !!serverId,
  })

  // Fetch current config
  const { data: config, isLoading } = useQuery({
    queryKey: ['collection-config', currentTenant, serverId],
    queryFn: () => collectionConfigService.getConfig(serverId!),
    enabled: !!currentTenant && !!serverId,
  })

  // Initialize form from config
  useEffect(() => {
    if (config) {
      setInterval(config.query_collection_interval)
      setMinDuration(config.query_min_duration_ms)
      setFilterDatabase(config.query_filter_database || '')
      setFilterLogin(config.query_filter_login || '')
      setFilterUser(config.query_filter_user || '')
      setFilterTextInclude(config.query_filter_text_include || '')
      setFilterTextExclude(config.query_filter_text_exclude || '')
      setIsDirty(false)
    }
  }, [config])

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: (input: UpdateQueryConfigInput) =>
      collectionConfigService.updateQueryConfig(serverId!, input),
    onSuccess: () => {
      toast.success('Configuration saved')
      setIsDirty(false)
      queryClient.invalidateQueries({ queryKey: ['collection-config', currentTenant, serverId] })
    },
    onError: () => toast.error('Failed to save configuration'),
  })

  // Start/Stop mutations
  const startMutation = useMutation({
    mutationFn: () => collectionConfigService.startQueryCollection(serverId!),
    onSuccess: () => {
      toast.success('Query collection started')
      queryClient.invalidateQueries({ queryKey: ['collection-config', currentTenant, serverId] })
    },
    onError: () => toast.error('Failed to start query collection'),
  })

  const stopMutation = useMutation({
    mutationFn: () => collectionConfigService.stopQueryCollection(serverId!),
    onSuccess: () => {
      toast.success('Query collection stopped')
      queryClient.invalidateQueries({ queryKey: ['collection-config', currentTenant, serverId] })
    },
    onError: () => toast.error('Failed to stop query collection'),
  })

  const handleSave = () => {
    saveMutation.mutate({
      query_collection_interval: interval,
      query_min_duration_ms: minDuration,
      query_filter_database: filterDatabase || null,
      query_filter_login: filterLogin || null,
      query_filter_user: filterUser || null,
      query_filter_text_include: filterTextInclude || null,
      query_filter_text_exclude: filterTextExclude || null,
    })
  }

  const handleFieldChange = <T,>(setter: React.Dispatch<React.SetStateAction<T>>, value: T) => {
    setter(value)
    setIsDirty(true)
  }

  if (!currentTenant) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Please select a tenant first.</p>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(`/servers/${serverId}`)}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Query Collection Config</h1>
            <p className="text-sm text-gray-500">{server?.name || 'Loading...'}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={config?.query_collection_enabled ? 'success' : 'default'}>
            {config?.query_collection_enabled ? 'Collecting' : 'Stopped'}
          </Badge>
          {config?.query_collection_enabled ? (
            <Button
              variant="secondary"
              onClick={() => stopMutation.mutate()}
              disabled={stopMutation.isPending}
            >
              <Square className="h-4 w-4 mr-2" />
              Stop Collection
            </Button>
          ) : (
            <Button
              variant="primary"
              onClick={() => startMutation.mutate()}
              disabled={startMutation.isPending}
            >
              <Play className="h-4 w-4 mr-2" />
              Start Collection
            </Button>
          )}
        </div>
      </div>

      {/* Settings Card */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Collection Settings</h2>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Interval */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Collection Interval (seconds)
              </label>
              <input
                type="number"
                min={10}
                max={300}
                value={interval}
                onChange={(e) => handleFieldChange(setInterval, Number(e.target.value))}
                className="w-32 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="mt-1 text-sm text-gray-500">How often to capture running queries (10-300 seconds)</p>
            </div>

            {/* Min Duration */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Minimum Duration (ms)
              </label>
              <input
                type="number"
                min={0}
                max={60000}
                value={minDuration}
                onChange={(e) => handleFieldChange(setMinDuration, Number(e.target.value))}
                className="w-32 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="mt-1 text-sm text-gray-500">Only capture queries running longer than this (0-60000 ms)</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filters Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Collection Filters</h2>
            <div className="flex items-center gap-1 text-sm text-gray-500">
              <HelpCircle className="h-4 w-4" />
              <span>Use SQL wildcards: % (any chars), _ (single char)</span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Database Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Database Name
              </label>
              <input
                type="text"
                value={filterDatabase}
                onChange={(e) => handleFieldChange(setFilterDatabase, e.target.value)}
                placeholder="e.g., %production%"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="mt-1 text-sm text-gray-500">Only capture queries from matching databases</p>
            </div>

            {/* Login Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Login Name
              </label>
              <input
                type="text"
                value={filterLogin}
                onChange={(e) => handleFieldChange(setFilterLogin, e.target.value)}
                placeholder="e.g., app_user%"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="mt-1 text-sm text-gray-500">Filter by SQL Server login name</p>
            </div>

            {/* User Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Windows User
              </label>
              <input
                type="text"
                value={filterUser}
                onChange={(e) => handleFieldChange(setFilterUser, e.target.value)}
                placeholder="e.g., %admin%"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="mt-1 text-sm text-gray-500">Filter by Windows NT user name</p>
            </div>

            {/* Query Text Include */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Query Text Include
              </label>
              <input
                type="text"
                value={filterTextInclude}
                onChange={(e) => handleFieldChange(setFilterTextInclude, e.target.value)}
                placeholder="e.g., %SELECT%"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="mt-1 text-sm text-gray-500">Only capture queries matching this pattern</p>
            </div>

            {/* Query Text Exclude */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Query Text Exclude
              </label>
              <input
                type="text"
                value={filterTextExclude}
                onChange={(e) => handleFieldChange(setFilterTextExclude, e.target.value)}
                placeholder="e.g., %sys.%"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="mt-1 text-sm text-gray-500">Exclude queries matching this pattern</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleSave}
          disabled={!isDirty || saveMutation.isPending}
        >
          <Save className="h-4 w-4 mr-2" />
          {saveMutation.isPending ? 'Saving...' : 'Save Configuration'}
        </Button>
      </div>
    </div>
  )
}
