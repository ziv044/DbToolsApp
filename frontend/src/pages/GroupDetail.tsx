import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { groupService } from '../services/groupService';
import type { Group } from '../services/groupService';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { ConfirmDialog } from '../components/ui/Modal';
import { toast } from '../components/ui/toastStore';
import GroupFormModal from '../components/groups/GroupFormModal';
import ServerPicker from '../components/groups/ServerPicker';

export function GroupDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showEditModal, setShowEditModal] = useState(false);
  const [showServerPicker, setShowServerPicker] = useState(false);
  const [removingServerId, setRemovingServerId] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const { data: group, isLoading, error } = useQuery({
    queryKey: ['groups', id],
    queryFn: () => groupService.getById(id!),
    enabled: !!id,
  });

  const removeServerMutation = useMutation({
    mutationFn: (serverId: string) => groupService.removeServer(id!, serverId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups', id] });
      queryClient.invalidateQueries({ queryKey: ['groups'] });
      toast.success('Server removed from group');
      setRemovingServerId(null);
    },
    onError: () => {
      toast.error('Failed to remove server');
    },
  });

  const deleteGroupMutation = useMutation({
    mutationFn: () => groupService.delete(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] });
      toast.success('Group deleted');
      navigate('/groups');
    },
    onError: () => {
      toast.error('Failed to delete group');
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !group) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Group not found</h2>
        <p className="text-gray-600 mb-4">The group you're looking for doesn't exist.</p>
        <Button onClick={() => navigate('/groups')}>Back to Groups</Button>
      </div>
    );
  }

  const statusVariants: Record<string, 'success' | 'error' | 'warning' | 'default'> = {
    online: 'success',
    offline: 'error',
    unknown: 'default',
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center text-sm text-gray-500">
        <Link to="/groups" className="hover:text-gray-700">Groups</Link>
        <svg className="w-4 h-4 mx-2" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
        </svg>
        <span className="text-gray-900">{group.name}</span>
      </nav>

      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          {group.color && (
            <div
              className="w-8 h-8 rounded-lg"
              style={{ backgroundColor: group.color }}
            />
          )}
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{group.name}</h1>
            {group.description && (
              <p className="text-gray-600 mt-1">{group.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={() => setShowEditModal(true)}>
            Edit
          </Button>
          <Button variant="danger" onClick={() => setShowDeleteConfirm(true)}>
            Delete
          </Button>
        </div>
      </div>

      {/* Server List */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Servers ({group.servers?.length || 0})
          </h2>
          <Button onClick={() => setShowServerPicker(true)}>
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Servers
          </Button>
        </div>

        {group.servers && group.servers.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Server
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Host
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Added
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {group.servers.map((server) => (
                  <tr key={server.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <Link
                        to={`/servers/${server.id}`}
                        className="font-medium text-blue-600 hover:text-blue-800"
                      >
                        {server.name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {server.hostname}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={statusVariants[server.status] || 'default'}>
                        {server.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-sm">
                      {new Date(server.added_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setRemovingServerId(server.id)}
                      >
                        <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8">
            <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
              </svg>
            </div>
            <p className="text-gray-500 mb-4">No servers in this group yet</p>
            <Button onClick={() => setShowServerPicker(true)}>
              Add Servers
            </Button>
          </div>
        )}
      </Card>

      {/* Edit Modal */}
      {showEditModal && (
        <GroupFormModal
          group={group as unknown as Group}
          onClose={() => setShowEditModal(false)}
        />
      )}

      {/* Server Picker Modal */}
      {showServerPicker && (
        <ServerPicker
          groupId={id!}
          existingServerIds={group.servers?.map(s => s.id) || []}
          onClose={() => setShowServerPicker(false)}
        />
      )}

      {/* Remove Server Confirmation */}
      <ConfirmDialog
        isOpen={!!removingServerId}
        title="Remove Server"
        description="Are you sure you want to remove this server from the group? The server will not be deleted."
        confirmLabel="Remove"
        variant="warning"
        onConfirm={() => {
          if (removingServerId) {
            removeServerMutation.mutate(removingServerId);
          }
        }}
        onClose={() => setRemovingServerId(null)}
      />

      {/* Delete Group Confirmation */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title="Delete Group"
        description={`Are you sure you want to delete "${group.name}"? Servers in this group will not be deleted, but any policies applied to this group will no longer affect them.`}
        confirmLabel="Delete"
        variant="danger"
        onConfirm={() => deleteGroupMutation.mutate()}
        onClose={() => setShowDeleteConfirm(false)}
      />
    </div>
  );
}
