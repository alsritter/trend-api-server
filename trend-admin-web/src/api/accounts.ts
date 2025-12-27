import { apiClient } from './client';
import type {
  Account,
  AccountCreateRequest,
  AccountUpdateRequest,
  PaginationResponse,
} from '@/types/api';

export const accountsApi = {
  // 获取账号列表
  list: (params: {
    platform?: string;
    status?: number;
    page?: number;
    page_size?: number;
  }) =>
    apiClient.get<any, PaginationResponse<Account>>('/api/v1/accounts', {
      params,
    }),

  // 获取单个账号
  get: (id: number) =>
    apiClient.get<any, Account>(`/api/v1/accounts/${id}`),

  // 创建账号
  create: (data: AccountCreateRequest) =>
    apiClient.post<any, Account>('/api/v1/accounts', data),

  // 更新账号
  update: (id: number, data: AccountUpdateRequest) =>
    apiClient.put<any, { account_id: number }>(`/api/v1/accounts/${id}`, data),

  // 删除账号
  delete: (id: number) =>
    apiClient.delete<any, { account_id: number }>(`/api/v1/accounts/${id}`),
};
