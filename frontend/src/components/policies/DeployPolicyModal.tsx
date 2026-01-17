import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { X, Check, Rocket } from 'lucide-react'
import { Button, Spinner } from '../ui'
import { policyService } from '../../services/policyService'
import type { Policy } from '../../services/policyService'
import { groupService } from '../../services/groupService'
import { toast } from '../ui/toastStore'

interface DeployPolicyModalProps {
  policy: Policy
  isOpen: boolean
  onClose: () => void
}

export const DeployPolicyModal = ({ policy, isOpen, onClose }: DeployPolicyModalProps) => {
  const [selectedGroupIds, setSelectedGroupIds] = useState<string[]>([])
  const queryClient = useQueryClient()

  const { data: groupsData, isLoading: groupsLoading } = useQuery({
    queryKey: ['groups'],
    queryFn: groupService.getAll,
    enabled: isOpen,
  })

  const { data: deploymentsData } = useQuery({
    queryKey: ['policy-deployments', policy.id],
    queryFn: () => policyService.getDeployments(policy.id),
    enabled: isOpen,
  })

  const deployMutation = useMutation({
    mutationFn: () =>
      policyService.deploy(policy.id, {
        group_ids: selectedGroupIds,
      }),
    onSuccess: (data) => {
      const count = data.deployments?.length ?? 0
      toast.success(`Policy deployed to ${count} group(s)`)
      queryClient.invalidateQueries({ queryKey: ['policy-deployments', policy.id] })
      queryClient.invalidateQueries({ queryKey: ['policies'] })
      handleClose()
    },
    onError: () => {
      toast.error('Failed to deploy policy')
    },
  })

  const handleClose = () => {
    setSelectedGroupIds([])
    onClose()
  }

  const handleToggleGroup = (groupId: string) => {
    setSelectedGroupIds((prev) =>
      prev.includes(groupId) ? prev.filter((id) => id !== groupId) : [...prev, groupId]
    )
  }

  const handleSelectAll = () => {
    const allGroupIds = groups.map((g) => g.id)
    setSelectedGroupIds(allGroupIds)
  }

  const handleDeselectAll = () => {
    setSelectedGroupIds([])
  }

  const handleDeploy = () => {
    if (selectedGroupIds.length === 0) {
      toast.error('Please select at least one group')
      return
    }
    deployMutation.mutate()
  }

  if (!isOpen) return null

  const groups = groupsData?.groups ?? []
  const existingDeployments = new Set(deploymentsData?.deployments?.map((d) => d.group_id) ?? [])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={handleClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <div>
            <h2 className="text-xl font-semibold">Deploy Policy</h2>
            <p className="text-sm text-gray-500">
              {policy.name} (v{policy.version})
            </p>
          </div>
          <button onClick={handleClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(80vh-140px)]">
          {groupsLoading ? (
            <div className="flex justify-center py-8">
              <Spinner />
            </div>
          ) : groups.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500">No server groups available.</p>
              <p className="text-sm text-gray-400 mt-1">Create a server group first.</p>
            </div>
          ) : (
            <>
              {/* Selection controls */}
              <div className="flex justify-between items-center mb-4">
                <span className="text-sm text-gray-500">
                  {selectedGroupIds.length} of {groups.length} selected
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={handleSelectAll}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    Select all
                  </button>
                  <span className="text-gray-300">|</span>
                  <button
                    onClick={handleDeselectAll}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    Clear
                  </button>
                </div>
              </div>

              {/* Group list */}
              <div className="space-y-2">
                {groups.map((group) => {
                  const isSelected = selectedGroupIds.includes(group.id)
                  const isDeployed = existingDeployments.has(group.id)

                  return (
                    <label
                      key={group.id}
                      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                        isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => handleToggleGroup(group.id)}
                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <div
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{ backgroundColor: group.color || '#6B7280' }}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{group.name}</p>
                        {group.description && (
                          <p className="text-sm text-gray-500 truncate">{group.description}</p>
                        )}
                      </div>
                      {isDeployed && (
                        <span className="flex-shrink-0 flex items-center gap-1 text-xs text-green-600">
                          <Check className="h-3 w-3" />
                          Deployed
                        </span>
                      )}
                    </label>
                  )
                })}
              </div>

              {/* Info note */}
              <p className="text-xs text-gray-400 mt-4">
                Deploying to a group that already has this policy will update it to the latest
                version.
              </p>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-6 py-4 border-t bg-gray-50">
          <Button variant="ghost" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            onClick={handleDeploy}
            disabled={selectedGroupIds.length === 0 || deployMutation.isPending}
          >
            {deployMutation.isPending ? (
              <Spinner size="sm" className="mr-2" />
            ) : (
              <Rocket className="h-4 w-4 mr-2" />
            )}
            Deploy to {selectedGroupIds.length} Group{selectedGroupIds.length !== 1 ? 's' : ''}
          </Button>
        </div>
      </div>
    </div>
  )
}
