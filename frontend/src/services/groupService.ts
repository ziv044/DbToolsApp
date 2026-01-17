import { apiClient } from './api';

export interface Group {
  id: string;
  name: string;
  description: string | null;
  color: string | null;
  member_count: number;
  created_at: string;
  updated_at: string | null;
}

export interface GroupDetail extends Group {
  servers: GroupServer[];
}

export interface GroupServer {
  id: string;
  name: string;
  hostname: string;
  status: string;
  added_at: string;
}

export interface CreateGroupInput {
  name: string;
  description?: string;
  color?: string;
}

export interface UpdateGroupInput {
  name?: string;
  description?: string;
  color?: string;
}

export const groupService = {
  getAll: async (): Promise<{ groups: Group[]; total: number }> => {
    const { data } = await apiClient.get('/groups');
    return data;
  },

  getById: async (id: string): Promise<GroupDetail> => {
    const { data } = await apiClient.get(`/groups/${id}`);
    return data;
  },

  create: async (input: CreateGroupInput): Promise<Group> => {
    const { data } = await apiClient.post('/groups', input);
    return data;
  },

  update: async (id: string, input: UpdateGroupInput): Promise<Group> => {
    const { data } = await apiClient.put(`/groups/${id}`, input);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/groups/${id}`);
  },

  addServers: async (groupId: string, serverIds: string[]): Promise<void> => {
    await apiClient.post(`/groups/${groupId}/servers`, { server_ids: serverIds });
  },

  removeServer: async (groupId: string, serverId: string): Promise<void> => {
    await apiClient.delete(`/groups/${groupId}/servers/${serverId}`);
  },
};

export default groupService;
