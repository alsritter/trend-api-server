import { apiClient } from './client';
import type { SystemHealth, DatabaseStats } from '@/types/api';

export const systemApi = {
  // 获取系统健康状态
  getHealth: () =>
    apiClient.get<any, SystemHealth>('/api/v1/system/health'),

  // 获取数据库统计
  getDatabaseStats: () =>
    apiClient.get<any, DatabaseStats>('/api/v1/system/database/stats'),

  // 获取 Celery 统计
  getCeleryStats: () =>
    apiClient.get<any, any>('/api/v1/system/celery/stats'),
};
