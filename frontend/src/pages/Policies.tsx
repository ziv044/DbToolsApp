import { useState, useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, RefreshCw, FileText, Filter } from 'lucide-react'
import { Card, CardHeader, CardContent, Button, Spinner, Badge, Input } from '../components/ui'
import { CreatePolicyModal } from '../components/policies/CreatePolicyModal'
import { policyService, POLICY_TYPE_LABELS, POLICY_TYPE_ICONS } from '../services/policyService'
import type { Policy, PolicyType } from '../services/policyService'
import { toast } from '../components/ui/toastStore'
import { useNavigate } from 'react-router-dom'

const POLICY_TYPES: PolicyType[] = ['backup', 'index_maintenance', 'integrity_check', 'custom_script']

export const Policies = () => {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState<PolicyType | ''>('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all')
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['policies'],
    queryFn: () => policyService.getAll(),
  })

  const policies = data?.policies ?? []

  // Filter policies
  const filteredPolicies = useMemo(() => {
    return policies.filter((policy) => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        const matchesName = policy.name.toLowerCase().includes(query)
        const matchesDesc = policy.description?.toLowerCase().includes(query) ?? false
        if (!matchesName && !matchesDesc) return false
      }

      // Type filter
      if (typeFilter && policy.type !== typeFilter) return false

      // Status filter
      if (statusFilter === 'active' && !policy.is_active) return false
      if (statusFilter === 'inactive' && policy.is_active) return false

      return true
    })
  }, [policies, searchQuery, typeFilter, statusFilter])

  const handleDelete = async (policy: Policy) => {
    if (!window.confirm(`Delete policy "${policy.name}"?`)) return

    try {
      await policyService.delete(policy.id)
      toast.success('Policy deleted')
      await queryClient.invalidateQueries({ queryKey: ['policies'] })
    } catch {
      toast.error('Failed to delete policy')
    }
  }

  const handleRowClick = (policyId: string) => {
    navigate(`/policies/${policyId}`)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Policies</h1>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={() => setIsCreateModalOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Policy
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <h2 className="text-lg font-semibold">Policy Library</h2>
            <div className="flex-1 flex flex-wrap gap-3">
              <div className="w-64">
                <Input
                  placeholder="Search policies..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value as PolicyType | '')}
                className="text-sm border rounded px-3 py-2 bg-white"
              >
                <option value="">All Types</option>
                {POLICY_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {POLICY_TYPE_LABELS[type]}
                  </option>
                ))}
              </select>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as 'all' | 'active' | 'inactive')}
                className="text-sm border rounded px-3 py-2 bg-white"
              >
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : policies.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No policies</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by creating a new policy.
              </p>
              <div className="mt-6">
                <Button onClick={() => setIsCreateModalOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Policy
                </Button>
              </div>
            </div>
          ) : filteredPolicies.length === 0 ? (
            <div className="text-center py-8">
              <Filter className="mx-auto h-8 w-8 text-gray-400" />
              <p className="mt-2 text-gray-500">No policies match your filters</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Version
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Updated
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredPolicies.map((policy) => (
                    <tr
                      key={policy.id}
                      className="hover:bg-gray-50 cursor-pointer"
                      onClick={() => handleRowClick(policy.id)}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <span className="text-xl mr-2">{POLICY_TYPE_ICONS[policy.type]}</span>
                          <div>
                            <div className="font-medium text-gray-900">{policy.name}</div>
                            {policy.description && (
                              <div className="text-sm text-gray-500 truncate max-w-xs">
                                {policy.description}
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {POLICY_TYPE_LABELS[policy.type]}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        v{policy.version}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge variant={policy.is_active ? 'success' : 'default'}>
                          {policy.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(policy.updated_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDelete(policy)
                          }}
                          className="text-red-600 hover:text-red-800"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <CreatePolicyModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
      />
    </div>
  )
}
