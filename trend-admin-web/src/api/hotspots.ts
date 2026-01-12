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
  LinkHotspotRequest,
  LinkHotspotResponse,
  HotspotDetail,
  GetClusterHotspotsResponse,
  UpdateHotspotStatusRequest,
  UpdateHotspotStatusResponse,
  UpdateHotspotStatusAndSetRepresentativeRequest,
  UpdateHotspotStatusAndSetRepresentativeResponse,
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

  /**
   * 获取聚簇下的所有热点
   */
  getClusterHotspots: async (clusterId: number): Promise<GetClusterHotspotsResponse> => {
    return apiClient.get(`${BASE_PATH}/cluster/${clusterId}/hotspots`);
  },

  /**
   * 更新热点状态
   */
  updateStatus: async (
    hotspotId: number,
    data: UpdateHotspotStatusRequest
  ): Promise<UpdateHotspotStatusResponse> => {
    return apiClient.patch(`${BASE_PATH}/${hotspotId}/status`, data);
  },

  /**
   * 更新热点状态并设置为聚簇代表
   */
  updateStatusAndSetRepresentative: async (
    hotspotId: number,
    data: UpdateHotspotStatusAndSetRepresentativeRequest
  ): Promise<UpdateHotspotStatusAndSetRepresentativeResponse> => {
    return apiClient.patch(`${BASE_PATH}/${hotspotId}/status-and-representative`, data);
  },
};
