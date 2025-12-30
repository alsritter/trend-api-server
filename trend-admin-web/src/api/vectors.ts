import { apiClient } from './client';
import type {
  VectorAddRequest,
  VectorAddResponse,
  VectorSearchRequest,
  VectorSearchResponse,
  VectorDeleteResponse,
  ListCollectionsResponse,
  VectorInfo,
} from '@/types/api';

export const vectorsApi = {
  // 添加向量
  add: (data: VectorAddRequest) =>
    apiClient.post<any, VectorAddResponse>('/api/v1/vectors/add', data),

  // 搜索向量
  search: (data: VectorSearchRequest) =>
    apiClient.post<any, VectorSearchResponse>('/api/v1/vectors/search', data),

  // 删除向量
  delete: (vectorId: number) =>
    apiClient.delete<any, VectorDeleteResponse>(`/api/v1/vectors/delete/${vectorId}`),

  // 删除集合
  deleteCollection: (collectionId: string) =>
    apiClient.delete<any, VectorDeleteResponse>(`/api/v1/vectors/collection/${collectionId}`),

  // 获取向量详情
  get: (vectorId: number) =>
    apiClient.get<any, { success: boolean; data: VectorInfo }>(`/api/v1/vectors/get/${vectorId}`),

  // 列出所有集合
  listCollections: () =>
    apiClient.get<any, ListCollectionsResponse>('/api/v1/vectors/collections'),
};
