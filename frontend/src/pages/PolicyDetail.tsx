import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Edit2, Trash2, Rocket, Settings, History, Users } from 'lucide-react'
import { Card, CardHeader, CardContent, Button, Spinner } from '../components/ui'
import { DeployPolicyModal } from '../components/policies'
import {
  policyService,
  POLICY_TYPE_LABELS,
  POLICY_TYPE_ICONS,
} from '../services/policyService'
import type { Policy, PolicyDeployment } from '../services/policyService'
import { toast } from '../components/ui/toastStore'

export const PolicyDetail = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [isDeployModalOpen, setIsDeployModalOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<'config' | 'deployments' | 'versions'>('config')

  const { data: policy, isLoading: policyLoading } = useQuery({
    queryKey: ['policy', id],
    queryFn: () => policyService.get(id!),
    enabled: !!id,
  })

  const { data: deploymentsData, isLoading: deploymentsLoading } = useQuery({
    queryKey: ['policy-deployments', id],
    queryFn: () => policyService.getDeployments(id!),
    enabled: !!id,
  })

  const { data: versionsData, isLoading: versionsLoading } = useQuery({
    queryKey: ['policy-versions', id],
    queryFn: () => policyService.getVersions(id!),
    enabled: !!id && activeTab === 'versions',
  })

  const deleteMutation = useMutation({
    mutationFn: () => policyService.delete(id!),
    onSuccess: () => {
      toast.success('Policy deleted')
      queryClient.invalidateQueries({ queryKey: ['policies'] })
      navigate('/policies')
    },
    onError: () => toast.error('Failed to delete policy'),
  })

  const removeDeploymentMutation = useMutation({
    mutationFn: (groupId: string) => policyService.removeDeployment(id!, groupId),
    onSuccess: () => {
      toast.success('Deployment removed')
      queryClient.invalidateQueries({ queryKey: ['policy-deployments', id] })
    },
    onError: () => toast.error('Failed to remove deployment'),
  })

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this policy?')) {
      deleteMutation.mutate()
    }
  }

  const handleRemoveDeployment = (groupId: string, groupName: string) => {
    if (window.confirm(`Remove deployment from "${groupName}"?`)) {
      removeDeploymentMutation.mutate(groupId)
    }
  }

  if (policyLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    )
  }

  if (!policy) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900">Policy not found</h2>
        <Link to="/policies" className="text-blue-600 hover:underline mt-2 inline-block">
          Back to Policies
        </Link>
      </div>
    )
  }

  const deployments = deploymentsData?.deployments ?? []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/policies" className="text-gray-400 hover:text-gray-600">
            <ArrowLeft className="h-6 w-6" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">{POLICY_TYPE_ICONS[policy.type]}</span>
              <h1 className="text-2xl font-bold text-gray-900">{policy.name}</h1>
              <span
                className={`px-2 py-0.5 text-xs rounded-full ${
                  policy.is_active
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {policy.is_active ? 'Active' : 'Draft'}
              </span>
            </div>
            <p className="text-gray-500 mt-1">
              {POLICY_TYPE_LABELS[policy.type]} • Version {policy.version}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => setIsDeployModalOpen(true)}>
            <Rocket className="h-4 w-4 mr-2" />
            Deploy
          </Button>
          <Button variant="secondary" onClick={() => navigate(`/policies/${id}/edit`)}>
            <Edit2 className="h-4 w-4 mr-2" />
            Edit
          </Button>
          <Button variant="danger" onClick={handleDelete} disabled={deleteMutation.isPending}>
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </Button>
        </div>
      </div>

      {/* Description */}
      {policy.description && (
        <Card>
          <CardContent className="py-4">
            <p className="text-gray-600">{policy.description}</p>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <div className="border-b">
        <nav className="flex gap-6">
          {[
            { id: 'config', label: 'Configuration', icon: Settings },
            { id: 'deployments', label: `Deployments (${deployments.length})`, icon: Users },
            { id: 'versions', label: 'Version History', icon: History },
          ].map(({ id: tabId, label, icon: Icon }) => (
            <button
              key={tabId}
              onClick={() => setActiveTab(tabId as typeof activeTab)}
              className={`flex items-center gap-2 py-3 border-b-2 -mb-px transition-colors ${
                activeTab === tabId
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'config' && <ConfigurationTab policy={policy} />}
      {activeTab === 'deployments' && (
        <DeploymentsTab
          deployments={deployments}
          loading={deploymentsLoading}
          onRemove={handleRemoveDeployment}
        />
      )}
      {activeTab === 'versions' && (
        <VersionsTab
          versions={versionsData?.versions ?? []}
          currentVersion={policy.version}
          loading={versionsLoading}
        />
      )}

      <DeployPolicyModal
        policy={policy}
        isOpen={isDeployModalOpen}
        onClose={() => setIsDeployModalOpen(false)}
      />
    </div>
  )
}

const ConfigurationTab = ({ policy }: { policy: Policy }) => {
  const configEntries = Object.entries(policy.configuration)

  return (
    <Card>
      <CardHeader>
        <h3 className="font-semibold">Configuration</h3>
      </CardHeader>
      <CardContent>
        {configEntries.length === 0 ? (
          <p className="text-gray-500">No configuration set</p>
        ) : (
          <dl className="grid grid-cols-2 gap-4">
            {configEntries.map(([key, value]) => (
              <div key={key} className="border-b pb-2">
                <dt className="text-sm text-gray-500">{formatLabel(key)}</dt>
                <dd className="font-medium">{formatValue(value)}</dd>
              </div>
            ))}
          </dl>
        )}
      </CardContent>
    </Card>
  )
}

const DeploymentsTab = ({
  deployments,
  loading,
  onRemove,
}: {
  deployments: PolicyDeployment[]
  loading: boolean
  onRemove: (groupId: string, groupName: string) => void
}) => {
  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    )
  }

  if (deployments.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <Users className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 font-medium text-gray-900">No deployments</h3>
          <p className="text-sm text-gray-500 mt-1">
            This policy hasn't been deployed to any server groups yet.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <h3 className="font-semibold">Deployed To</h3>
      </CardHeader>
      <CardContent>
        <div className="divide-y">
          {deployments.map((d) => (
            <div key={d.id} className="flex items-center justify-between py-3">
              <div className="flex items-center gap-3">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: d.group?.color || '#6B7280' }}
                />
                <div>
                  <p className="font-medium">{d.group?.name || 'Unknown Group'}</p>
                  <p className="text-sm text-gray-500">
                    Version {d.policy_version} • Deployed{' '}
                    {new Date(d.deployed_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onRemove(d.group_id, d.group?.name || 'this group')}
              >
                <Trash2 className="h-4 w-4 text-red-500" />
              </Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

const VersionsTab = ({
  versions,
  currentVersion,
  loading,
}: {
  versions: Array<{
    id: string
    version: number
    configuration: Record<string, unknown>
    description: string | null
    created_at: string
  }>
  currentVersion: number
  loading: boolean
}) => {
  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    )
  }

  if (versions.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <History className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 font-medium text-gray-900">No version history</h3>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <h3 className="font-semibold">Version History</h3>
      </CardHeader>
      <CardContent>
        <div className="divide-y">
          {versions.map((v) => (
            <div key={v.id} className="py-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-medium">Version {v.version}</span>
                  {v.version === currentVersion && (
                    <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded-full">
                      Current
                    </span>
                  )}
                </div>
                <span className="text-sm text-gray-500">
                  {new Date(v.created_at).toLocaleString()}
                </span>
              </div>
              {v.description && <p className="text-sm text-gray-500 mt-1">{v.description}</p>}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

function formatLabel(key: string): string {
  return key
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function formatValue(value: unknown): string {
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (value === null || value === undefined) return '-'
  return String(value)
}
