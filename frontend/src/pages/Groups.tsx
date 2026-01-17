import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { groupService } from '../services/groupService';
import type { Group } from '../services/groupService';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { ConfirmDialog } from '../components/ui/Modal';
import { toast } from '../components/ui/toastStore';
import GroupFormModal from '../components/groups/GroupFormModal';

export function Groups() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingGroup, setEditingGroup] = useState<Group | null>(null);
  const [deletingGroup, setDeletingGroup] = useState<Group | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['groups'],
    queryFn: groupService.getAll,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => groupService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] });
      toast.success('Group deleted successfully');
      setDeletingGroup(null);
    },
    onError: () => {
      toast.error('Failed to delete group');
    },
  });

  const handleDelete = () => {
    if (deletingGroup) {
      deleteMutation.mutate(deletingGroup.id);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-600 p-4">
        Failed to load groups. Please try again.
      </div>
    );
  }

  const groups = data?.groups || [];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Server Groups</h1>
          <p className="text-gray-600 mt-1">Organize your servers into logical groups</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Create Group
        </Button>
      </div>

      {/* Groups List */}
      {groups.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="flex flex-col items-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No groups yet</h3>
            <p className="text-gray-500 mb-6 max-w-sm">
              Create groups to organize your servers. Groups help you apply policies and manage related servers together.
            </p>
            <Button onClick={() => setShowCreateModal(true)}>
              Create your first group
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {groups.map((group) => (
            <Card
              key={group.id}
              className="p-4 cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => navigate(`/groups/${group.id}`)}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  {group.color && (
                    <div
                      className="w-4 h-4 rounded-full flex-shrink-0"
                      style={{ backgroundColor: group.color }}
                    />
                  )}
                  <div>
                    <h3 className="font-semibold text-gray-900">{group.name}</h3>
                    {group.description && (
                      <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                        {group.description}
                      </p>
                    )}
                  </div>
                </div>
                <Badge variant="default">
                  {group.member_count} server{group.member_count !== 1 ? 's' : ''}
                </Badge>
              </div>
              <div className="flex items-center justify-end mt-4 pt-4 border-t border-gray-100 gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    setEditingGroup(group);
                  }}
                >
                  Edit
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    setDeletingGroup(group);
                  }}
                >
                  Delete
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      {(showCreateModal || editingGroup) && (
        <GroupFormModal
          group={editingGroup || undefined}
          onClose={() => {
            setShowCreateModal(false);
            setEditingGroup(null);
          }}
        />
      )}

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={!!deletingGroup}
        title="Delete Group"
        description={`Are you sure you want to delete "${deletingGroup?.name}"? Servers in this group will not be deleted, but any policies applied to this group will no longer affect them.`}
        confirmLabel="Delete"
        variant="danger"
        onConfirm={handleDelete}
        onClose={() => setDeletingGroup(null)}
      />
    </div>
  );
}
