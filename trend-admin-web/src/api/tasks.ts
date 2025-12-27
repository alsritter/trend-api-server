import { apiClient } from './client';
import type {
  Task,
  TaskCreateRequest,
  TaskStatus,
  PaginationResponse,
} from '@/types/api';

export const tasksApi = {
  // 创建任务
  create: (data: TaskCreateRequest) =>
    apiClient.post<any, { task_id: string; status: string; created_at: string }>(
      '/api/v1/tasks',
      data
    ),

  // 获取任务状态
  getStatus: (taskId: string) =>
    apiClient.get<any, TaskStatus>(`/api/v1/tasks/${taskId}`),

  // 停止任务
  stop: (taskId: string) =>
    apiClient.post<any, { task_id: string; message: string }>(
      `/api/v1/tasks/${taskId}/stop`
    ),

  // 获取任务列表 (注意: API 可能未实现)
  list: (params?: { page?: number; page_size?: number }) =>
    apiClient.get<any, PaginationResponse<Task>>('/api/v1/tasks', {
      params,
    }),
};
