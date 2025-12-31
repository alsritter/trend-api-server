import { apiClient } from './client';
import type {
  AddHotspotKeywordRequest,
  AddHotspotKeywordResponse,
  CheckHotspotRequest,
  CheckHotspotResponse,
  AddBusinessReportRequest,
  AddBusinessReportResponse,
  AddToPushQueueRequest,
  AddToPushQueueResponse,
  GetPendingPushResponse,
  ListHotspotsRequest,
  ListHotspotsResponse,
  DeleteHotspotResponse,
  GetClusterHotspotsResponse,
  LinkHotspotRequest,
  LinkHotspotResponse,
  HotspotDetail,
  // 聚簇管理
  ListClustersResponse,
  MergeClustersRequest,
  MergeClustersResponse,
  SplitClusterRequest,
  SplitClusterResponse,
  UpdateClusterRequest,
  UpdateClusterResponse,
  DeleteClusterResponse,
  RemoveHotspotFromClusterRequest,
  RemoveHotspotFromClusterResponse,
} from '@/types/api';

const BASE_PATH = '/api/v1/hotspots';

export const hotspotsApi = {
  // ==================== 核心业务接口 ====================

  /**
   * 新增词的接口 - 根据AI分析结果添加热词
   */
  addKeyword: async (data: AddHotspotKeywordRequest): Promise<AddHotspotKeywordResponse> => {
    return apiClient.post(`${BASE_PATH}/add-keyword`, data);
  },

  /**
   * 检查热词是否已存在
   */
  checkExists: async (data: CheckHotspotRequest): Promise<CheckHotspotResponse> => {
    return apiClient.post(`${BASE_PATH}/check-exists`, data);
  },

  /**
   * 添加商业报告
   */
  addBusinessReport: async (
    data: AddBusinessReportRequest
  ): Promise<AddBusinessReportResponse> => {
    return apiClient.post(`${BASE_PATH}/business-report`, data);
  },

  /**
   * 添加到推送队列
   */
  addToPushQueue: async (data: AddToPushQueueRequest): Promise<AddToPushQueueResponse> => {
    return apiClient.post(`${BASE_PATH}/push-queue`, data);
  },

  /**
   * 获取待推送的报告
   */
  getPendingPush: async (limit: number = 10): Promise<GetPendingPushResponse> => {
    return apiClient.get(`${BASE_PATH}/push-queue/pending`, { params: { limit } });
  },

  // ==================== 前端管理接口 ====================

  /**
   * 列出热点（分页、过滤、搜索）
   */
  list: async (params: ListHotspotsRequest = {}): Promise<ListHotspotsResponse> => {
    return apiClient.get(`${BASE_PATH}/list`, { params });
  },

  /**
   * 获取热点详情
   */
  get: async (hotspotId: number): Promise<HotspotDetail> => {
    return apiClient.get(`${BASE_PATH}/${hotspotId}`);
  },

  /**
   * 获取同簇的所有热点
   */
  getClusterHotspots: async (clusterId: number): Promise<GetClusterHotspotsResponse> => {
    return apiClient.get(`${BASE_PATH}/cluster/${clusterId}/hotspots`);
  },

  /**
   * 删除热点
   */
  delete: async (hotspotId: number): Promise<DeleteHotspotResponse> => {
    return apiClient.delete(`${BASE_PATH}/${hotspotId}`);
  },

  /**
   * 关联热点 - 复用已有热点的分析信息创建新热点
   */
  link: async (data: LinkHotspotRequest): Promise<LinkHotspotResponse> => {
    return apiClient.post(`${BASE_PATH}/link`, data);
  },

  // ==================== 聚簇管理接口 ====================

  /**
   * 列出所有聚簇
   */
  listClusters: async (): Promise<ListClustersResponse> => {
    return apiClient.get(`${BASE_PATH}/clusters`);
  },

  /**
   * 合并多个聚簇
   */
  mergeClusters: async (data: MergeClustersRequest): Promise<MergeClustersResponse> => {
    return apiClient.post(`${BASE_PATH}/clusters/merge`, data);
  },

  /**
   * 拆分聚簇
   */
  splitCluster: async (clusterId: number, data: SplitClusterRequest): Promise<SplitClusterResponse> => {
    return apiClient.post(`${BASE_PATH}/clusters/${clusterId}/split`, data);
  },

  /**
   * 更新聚簇信息
   */
  updateCluster: async (clusterId: number, data: UpdateClusterRequest): Promise<UpdateClusterResponse> => {
    return apiClient.patch(`${BASE_PATH}/clusters/${clusterId}`, data);
  },

  /**
   * 删除聚簇
   */
  deleteCluster: async (clusterId: number): Promise<DeleteClusterResponse> => {
    return apiClient.delete(`${BASE_PATH}/clusters/${clusterId}`);
  },

  /**
   * 从聚簇中移除单个热点
   */
  removeHotspotFromCluster: async (
    clusterId: number,
    data: RemoveHotspotFromClusterRequest
  ): Promise<RemoveHotspotFromClusterResponse> => {
    return apiClient.post(`${BASE_PATH}/clusters/${clusterId}/remove-hotspot`, data);
  },
};
