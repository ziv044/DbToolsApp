import { apiClient } from './api';

export interface Label {
  id: string;
  name: string;
  color: string;
  created_at: string;
  usage_count?: number;
}

export interface CreateLabelInput {
  name: string;
  color?: string;
}

export interface UpdateLabelInput {
  name?: string;
  color?: string;
}

export const labelService = {
  getAll: async (): Promise<{ labels: Label[]; total: number }> => {
    const { data } = await apiClient.get('/labels');
    return data;
  },

  getById: async (id: string): Promise<Label> => {
    const { data } = await apiClient.get(`/labels/${id}`);
    return data;
  },

  create: async (input: CreateLabelInput): Promise<Label> => {
    const { data } = await apiClient.post('/labels', input);
    return data;
  },

  update: async (id: string, input: UpdateLabelInput): Promise<Label> => {
    const { data } = await apiClient.put(`/labels/${id}`, input);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/labels/${id}`);
  },

  getServerLabels: async (serverId: string): Promise<{ labels: Label[]; total: number }> => {
    const { data } = await apiClient.get(`/servers/${serverId}/labels`);
    return data;
  },

  assignToServer: async (serverId: string, labels: string[]): Promise<{ labels: Label[]; total: number }> => {
    const { data } = await apiClient.post(`/servers/${serverId}/labels`, { labels });
    return data;
  },

  removeFromServer: async (serverId: string, labelId: string): Promise<void> => {
    await apiClient.delete(`/servers/${serverId}/labels/${labelId}`);
  },
};

export default labelService;
