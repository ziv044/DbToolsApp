import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import {
  ChevronRight,
  ArrowLeft,
  Plug,
  Pencil,
  Trash2,
  Server,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Rocket,
  RefreshCw,
} from 'lucide-react'
import { Card, CardHeader, CardContent, Button, Spinner, Badge } from '../components/ui'
import { ConfirmDialog } from '../components/ui/Modal'
import { serverService } from '../services/serverService'
import type { TestConnectionResult } from '../services/serverService'
import { deploymentService } from '../services/deploymentService'
import type { DeploymentStatusType } from '../services/deploymentService'
import { LabelInput } from '../components/servers/LabelInput'
import { toast } from '../components/ui/toastStore'

const statusVariants: Record<string, 'success' | 'error' | 'warning' | 'default'> = {
  online: 'success',
  offline: 'error',
  warning: 'warning',
  unknown: 'default',
  monitored: 'success',
}

const deploymentStatusVariants: Record<DeploymentStatusType, 'success' | 'error' | 'warning' | 'default'> = {
  deployed: 'success',
  outdated: 'warning',
  not_deployed: 'default',
  failed: 'error',
}

const deploymentStatusLabels: Record<DeploymentStatusType, string> = {
  deployed: 'Deployed',
  outdated: 'Update Available',
  not_deployed: 'Not Deployed',
  failed: 'Failed',
}

export const ServerDetail = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [isTesting, setIsTesting] = useState(false)
  const [testResult, setTestResult] = useState<TestConnectionResult | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const {
    data: server,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['servers', id],
    queryFn: () => serverService.getById(id!),
    enabled: !!id,
  })

  const {
    data: deploymentStatus,
    isLoading: isLoadingDeployment,
    refetch: refetchDeploymentStatus,
  } = useQuery({
    queryKey: ['deployment-status', id],
    queryFn: () => deploymentService.getStatus(id!),
    enabled: !!id && !!server,
  })

  const deployMutation = useMutation({
    mutationFn: () => deploymentService.deploy(id!),
    onSuccess: (result) => {
      if (result.success) {
        toast.success('Deployment successful', `Version ${result.version} deployed`)
        refetchDeploymentStatus()
        queryClient.invalidateQueries({ queryKey: ['servers', id] })
      } else {
        toast.error('Deployment failed', result.error || 'Unknown error')
      }
    },
    onError: () => {
      toast.error('Deployment failed', 'An unexpected error occurred')
    },
  })

  const handleTestConnection = async () => {
    if (!server) return

    setIsTesting(true)
    setTestResult(null)

    const result = await serverService.testConnection({
      hostname: server.hostname,
      port: server.port,
      instance_name: server.instance_name || undefined,
      auth_type: server.auth_type,
      username: server.username || undefined,
      password: '', // Note: Password not returned from API, would need re-entry
    })

    setTestResult(result)
    setIsTesting(false)

    if (result.success) {
      toast.success('Connection successful')
    } else {
      toast.error('Connection failed', result.error)
    }
  }

  const handleDelete = async () => {
    if (!server) return

    setIsDeleting(true)
    try {
      await serverService.delete(server.id)
      toast.success(`Server "${server.name}" deleted`)
      await queryClient.invalidateQueries({ queryKey: ['servers'] })
      navigate('/servers')
    } catch {
      toast.error('Failed to delete server')
    } finally {
      setIsDeleting(false)
      setShowDeleteConfirm(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    )
  }

  if (error || !server) {
    return (
      <div className="text-center py-12">
        <Server className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-lg font-medium text-gray-900">Server not found</h3>
        <p className="mt-1 text-sm text-gray-500">The server you're looking for doesn't exist.</p>
        <div className="mt-6">
          <Link to="/servers">
            <Button variant="secondary">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Servers
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  const connectionDisplay = server.instance_name
    ? `${server.hostname}\\${server.instance_name}`
    : server.port === 1433
      ? server.hostname
      : `${server.hostname},${server.port}`

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center text-sm text-gray-500">
        <Link to="/servers" className="hover:text-gray-700">
          Servers
        </Link>
        <ChevronRight className="h-4 w-4 mx-2" />
        <span className="text-gray-900">{server.name}</span>
      </nav>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-gray-100 rounded-lg">
            <Server className="h-8 w-8 text-gray-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{server.name}</h1>
            <p className="text-sm text-gray-500">{connectionDisplay}</p>
          </div>
          <Badge variant={statusVariants[server.status] ?? 'default'}>{server.status}</Badge>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={handleTestConnection} disabled={isTesting}>
            {isTesting ? <Spinner size="sm" /> : <Plug className="h-4 w-4 mr-2" />}
            Test Connection
          </Button>
          <Button variant="secondary" onClick={() => navigate(`/servers/${server.id}/edit`)}>
            <Pencil className="h-4 w-4 mr-2" />
            Edit
          </Button>
          <Button variant="danger" onClick={() => setShowDeleteConfirm(true)}>
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </Button>
        </div>
      </div>

      {/* Test Result */}
      {testResult && (
        <div
          className={`p-4 rounded-lg ${testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}
        >
          <div className="flex items-center gap-2">
            {testResult.success ? (
              <>
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span className="font-medium text-green-800">Connection successful</span>
              </>
            ) : (
              <>
                <XCircle className="h-5 w-5 text-red-500" />
                <span className="font-medium text-red-800">Connection failed</span>
              </>
            )}
          </div>
          {testResult.success ? (
            <div className="mt-2 text-sm text-green-700">
              <p>
                <strong>Edition:</strong> {testResult.edition}
              </p>
              <p>
                <strong>Version:</strong> {testResult.product_version}
              </p>
              {!testResult.is_supported_version && (
                <div className="flex items-center gap-2 text-yellow-700 mt-2">
                  <AlertTriangle className="h-4 w-4" />
                  <span>SQL Server 2016 or later is recommended</span>
                </div>
              )}
              {!testResult.has_view_server_state && (
                <div className="flex items-center gap-2 text-yellow-700 mt-2">
                  <AlertTriangle className="h-4 w-4" />
                  <span>VIEW SERVER STATE permission not granted</span>
                </div>
              )}
            </div>
          ) : (
            <p className="mt-2 text-sm text-red-700">{testResult.error}</p>
          )}
        </div>
      )}

      {/* Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Connection Info */}
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Connection Information</h2>
          </CardHeader>
          <CardContent>
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500">Host</dt>
                <dd className="text-sm font-medium text-gray-900">{server.hostname}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500">Port</dt>
                <dd className="text-sm font-medium text-gray-900">{server.port}</dd>
              </div>
              {server.instance_name && (
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">Instance</dt>
                  <dd className="text-sm font-medium text-gray-900">{server.instance_name}</dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500">Authentication</dt>
                <dd className="text-sm font-medium text-gray-900">
                  {server.auth_type === 'windows' ? 'Windows' : 'SQL Server'}
                </dd>
              </div>
              {server.username && (
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">Username</dt>
                  <dd className="text-sm font-medium text-gray-900">{server.username}</dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500">Added</dt>
                <dd className="text-sm font-medium text-gray-900">
                  {new Date(server.created_at).toLocaleDateString()}
                </dd>
              </div>
            </dl>
          </CardContent>
        </Card>

        {/* Groups (Placeholder) */}
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Groups</h2>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500">No groups assigned</p>
            <p className="text-xs text-gray-400 mt-2">
              Server groups will be available in a future update.
            </p>
          </CardContent>
        </Card>

        {/* Labels */}
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Labels</h2>
          </CardHeader>
          <CardContent>
            <LabelInput
              serverId={server.id}
              existingLabels={server.labels || []}
            />
          </CardContent>
        </Card>

        {/* Deployment Status */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Monitoring Deployment</h2>
              {deploymentStatus && (
                <Badge variant={deploymentStatusVariants[deploymentStatus.status]}>
                  {deploymentStatusLabels[deploymentStatus.status]}
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {isLoadingDeployment ? (
              <div className="flex items-center justify-center py-4">
                <Spinner size="sm" />
              </div>
            ) : deploymentStatus ? (
              <div className="space-y-4">
                {deploymentStatus.status === 'deployed' && (
                  <div className="text-sm text-gray-600">
                    <div className="flex items-center gap-2 text-green-600 mb-2">
                      <CheckCircle className="h-4 w-4" />
                      <span>Monitoring objects deployed</span>
                    </div>
                    <dl className="space-y-1">
                      <div className="flex justify-between">
                        <dt className="text-gray-500">Version</dt>
                        <dd className="font-medium">{deploymentStatus.version}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-500">Deployed</dt>
                        <dd className="font-medium">
                          {deploymentStatus.deployed_at
                            ? new Date(deploymentStatus.deployed_at).toLocaleString()
                            : 'Unknown'}
                        </dd>
                      </div>
                    </dl>
                  </div>
                )}

                {deploymentStatus.status === 'outdated' && (
                  <div className="text-sm">
                    <div className="flex items-center gap-2 text-yellow-600 mb-2">
                      <RefreshCw className="h-4 w-4" />
                      <span>Update available</span>
                    </div>
                    <p className="text-gray-500 mb-3">
                      Current version: {deploymentStatus.version}. A newer version is available.
                    </p>
                    <Button
                      onClick={() => deployMutation.mutate()}
                      disabled={deployMutation.isPending}
                      className="w-full"
                    >
                      {deployMutation.isPending ? (
                        <Spinner size="sm" />
                      ) : (
                        <>
                          <RefreshCw className="h-4 w-4 mr-2" />
                          Update Monitoring
                        </>
                      )}
                    </Button>
                  </div>
                )}

                {deploymentStatus.status === 'not_deployed' && (
                  <div className="text-sm">
                    <p className="text-gray-500 mb-3">
                      Deploy monitoring objects to enable data collection from this server.
                    </p>
                    <Button
                      onClick={() => deployMutation.mutate()}
                      disabled={deployMutation.isPending}
                      className="w-full"
                    >
                      {deployMutation.isPending ? (
                        <Spinner size="sm" />
                      ) : (
                        <>
                          <Rocket className="h-4 w-4 mr-2" />
                          Deploy Monitoring
                        </>
                      )}
                    </Button>
                  </div>
                )}

                {deploymentStatus.status === 'failed' && (
                  <div className="text-sm">
                    <div className="flex items-center gap-2 text-red-600 mb-2">
                      <XCircle className="h-4 w-4" />
                      <span>Deployment check failed</span>
                    </div>
                    <p className="text-gray-500 mb-3">
                      {deploymentStatus.error || 'Unable to check deployment status'}
                    </p>
                    <Button
                      variant="secondary"
                      onClick={() => refetchDeploymentStatus()}
                      className="w-full"
                    >
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Retry
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-500">Unable to check deployment status</p>
            )}
          </CardContent>
        </Card>

        {/* Activity (Placeholder) */}
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Recent Activity</h2>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <div className="p-1.5 bg-green-100 rounded-full">
                  <CheckCircle className="h-3 w-3 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-900">Server added</p>
                  <p className="text-xs text-gray-500 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {new Date(server.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={handleDelete}
        title="Delete Server"
        description={`Are you sure you want to delete "${server.name}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
        isLoading={isDeleting}
      />
    </div>
  )
}
