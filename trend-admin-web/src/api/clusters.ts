import { apiClient } from './client';
import type {
  ListClustersResponse,
  CreateClusterRequest,
  CreateClusterResponse,
  MergeClustersRequest,
  MergeClustersResponse,
  SplitClusterRequest,
  SplitClusterResponse,
  UpdateClusterRequest,
  UpdateClusterResponse,
  DeleteClusterResponse,
  RemoveHotspotFromClusterRequest,
  RemoveHotspotFromClusterResponse,
  ClusterInfo,
  GetClusterHotspotsResponse,
} from '@/types/api';

const BASE_PATH = '/api/v1/clusters';

export const clustersApi = {
  /**
   * 创建新聚簇
   */
  create: async (data: CreateClusterRequest): Promise<CreateClusterResponse> => {
    return apiClient.post(BASE_PATH, data);
  },

  /**
   * 列出所有聚簇
   */
  list: async (params?: {
    status?: string;
    platforms?: string;
    start_time?: string;
    end_time?: string;
  }): Promise<ListClustersResponse> => {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status', params.status);
    if (params?.platforms) queryParams.append('platforms', params.platforms);
    if (params?.start_time) queryParams.append('start_time', params.start_time);
    if (params?.end_time) queryParams.append('end_time', params.end_time);
    
    const url = queryParams.toString() ? `${BASE_PATH}?${queryParams}` : BASE_PATH;
    return apiClient.get(url);
  },

  /**
   * 获取聚簇详情
   */
  get: async (clusterId: number): Promise<ClusterInfo> => {
    return apiClient.get(`${BASE_PATH}/${clusterId}`);
  },

  /**
   * 获取聚簇下的所有热点
   */
  getHotspots: async (clusterId: number): Promise<GetClusterHotspotsResponse> => {
    return apiClient.get(`/api/v1/hotspots/cluster/${clusterId}/hotspots`);
  },

  /**
   * 合并多个聚簇
   */
  merge: async (data: MergeClustersRequest): Promise<MergeClustersResponse> => {
    return apiClient.post(`${BASE_PATH}/merge`, data);
  },

  /**
   * 拆分聚簇
   */
  split: async (clusterId: number, data: SplitClusterRequest): Promise<SplitClusterResponse> => {
    return apiClient.post(`${BASE_PATH}/${clusterId}/split`, data);
  },

  /**
   * 更新聚簇信息
   */
  update: async (clusterId: number, data: UpdateClusterRequest): Promise<UpdateClusterResponse> => {
    return apiClient.patch(`${BASE_PATH}/${clusterId}`, data);
  },

  /**
   * 删除聚簇
   */
  delete: async (clusterId: number): Promise<DeleteClusterResponse> => {
    return apiClient.delete(`${BASE_PATH}/${clusterId}`);
  },

  /**
   * 从聚簇中移除单个热点
   */
  removeHotspot: async (
    clusterId: number,
    data: RemoveHotspotFromClusterRequest
  ): Promise<RemoveHotspotFromClusterResponse> => {
    return apiClient.post(`${BASE_PATH}/${clusterId}/remove-hotspot`, data);
  },
};
