import { apiClient } from './client';
import type { PaginationResponse } from '@/types/api';

export const contentsApi = {
  // 获取笔记/视频列表
  getNotes: (
    platform: string,
    params: { keyword?: string; hotspot_id?: number; page?: number; page_size?: number }
  ) =>
    apiClient.get<any, PaginationResponse<any>>(
      `/api/v1/contents/${platform}/notes`,
      { params }
    ),

  // 获取评论列表
  getComments: (
    platform: string,
    params: { note_id?: string; page?: number; page_size?: number }
  ) =>
    apiClient.get<any, PaginationResponse<any>>(
      `/api/v1/contents/${platform}/comments`,
      { params }
    ),

  // 获取创作者信息
  getCreator: (platform: string, userId: string) =>
    apiClient.get<any, any>(`/api/v1/contents/${platform}/creators/${userId}`),
};
