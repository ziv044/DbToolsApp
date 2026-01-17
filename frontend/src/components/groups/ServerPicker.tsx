import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { serverService } from '../../services/serverService';
import { groupService } from '../../services/groupService';
import { Modal } from '../ui/Modal';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { toast } from '../ui/toastStore';

interface ServerPickerProps {
  groupId: string;
  existingServerIds: string[];
  onClose: () => void;
}

export default function ServerPicker({ groupId, existingServerIds, onClose }: ServerPickerProps) {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const { data, isLoading } = useQuery({
    queryKey: ['servers'],
    queryFn: serverService.getAll,
  });

  const addServersMutation = useMutation({
    mutationFn: (serverIds: string[]) => groupService.addServers(groupId, serverIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups', groupId] });
      queryClient.invalidateQueries({ queryKey: ['groups'] });
      toast.success(`${selectedIds.size} server(s) added to group`);
      onClose();
    },
    onError: () => {
      toast.error('Failed to add servers to group');
    },
  });

  const availableServers = useMemo(() => {
    if (!data?.servers) return [];
    return data.servers.filter(server => !existingServerIds.includes(server.id));
  }, [data?.servers, existingServerIds]);

  const filteredServers = useMemo(() => {
    if (!searchQuery) return availableServers;
    const query = searchQuery.toLowerCase();
    return availableServers.filter(
      server =>
        server.name.toLowerCase().includes(query) ||
        server.hostname.toLowerCase().includes(query)
    );
  }, [availableServers, searchQuery]);

  const toggleServer = (serverId: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(serverId)) {
      newSelected.delete(serverId);
    } else {
      newSelected.add(serverId);
    }
    setSelectedIds(newSelected);
  };

  const toggleAll = () => {
    if (selectedIds.size === filteredServers.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredServers.map(s => s.id)));
    }
  };

  const handleSubmit = () => {
    if (selectedIds.size === 0) return;
    addServersMutation.mutate(Array.from(selectedIds));
  };

  const statusVariants: Record<string, 'success' | 'error' | 'warning' | 'default'> = {
    online: 'success',
    offline: 'error',
    unknown: 'default',
  };

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title="Add Servers to Group"
      size="lg"
    >
      <div className="space-y-4">
        {/* Search */}
        <Input
          placeholder="Search servers..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />

        {/* Server List */}
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          </div>
        ) : availableServers.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            All servers are already in this group
          </div>
        ) : filteredServers.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No servers match your search
          </div>
        ) : (
          <div className="border rounded-lg divide-y max-h-96 overflow-y-auto">
            {/* Select All Header */}
            <div className="px-4 py-2 bg-gray-50 flex items-center gap-3">
              <input
                type="checkbox"
                checked={selectedIds.size === filteredServers.length && filteredServers.length > 0}
                onChange={toggleAll}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="text-sm text-gray-600">
                {selectedIds.size > 0 ? `${selectedIds.size} selected` : 'Select all'}
              </span>
            </div>

            {/* Server Rows */}
            {filteredServers.map((server) => (
              <label
                key={server.id}
                className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={selectedIds.has(server.id)}
                  onChange={() => toggleServer(server.id)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900">{server.name}</div>
                  <div className="text-sm text-gray-500">{server.hostname}</div>
                </div>
                <Badge variant={statusVariants[server.status] || 'default'}>
                  {server.status}
                </Badge>
              </label>
            ))}
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={selectedIds.size === 0 || addServersMutation.isPending}
          >
            {addServersMutation.isPending
              ? 'Adding...'
              : `Add ${selectedIds.size || ''} Server${selectedIds.size !== 1 ? 's' : ''}`}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
