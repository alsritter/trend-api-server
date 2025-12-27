import { apiClient } from './client';
import type {
  ProxyConfig,
  ProxyConfigUpdateRequest,
  ProxyIpInfo,
  ProxyStats,
  PaginationResponse,
} from '@/types/api';

export const proxyApi = {
  // 获取代理配置
  getConfig: () =>
    apiClient.get<any, ProxyConfig>('/api/v1/proxy/config'),

  // 更新代理配置
  updateConfig: (data: ProxyConfigUpdateRequest) =>
    apiClient.put<any, { updated_fields: string[] }>('/api/v1/proxy/config', data),

  // 获取 IP 列表
  getIpList: (params: { page?: number; page_size?: number }) =>
    apiClient.get<any, PaginationResponse<ProxyIpInfo>>('/api/v1/proxy/ips', {
      params,
    }),

  // 验证 IP
  validateIp: (data: { ip: string; port: number; user?: string; password?: string }) =>
    apiClient.post<any, { is_valid: boolean; response_time?: number; error_message?: string }>(
      '/api/v1/proxy/validate',
      data
    ),

  // 清空 IP 池
  clearIps: () =>
    apiClient.delete<any, { cleared_count: number }>('/api/v1/proxy/ips'),

  // 获取统计信息
  getStats: () =>
    apiClient.get<any, ProxyStats>('/api/v1/proxy/stats'),
};
