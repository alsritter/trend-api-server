// API 响应通用类型
export interface APIResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

// 分页响应
export interface PaginationResponse<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}

// 账号相关类型
export interface Account {
  id: number;
  account_name: string;
  platform_name: string;
  status: number;
  invalid_timestamp: number;
  create_time: string;
  update_time: string;
}

export interface AccountCreateRequest {
  account_name: string;
  platform_name: string;
  cookies: string;
}

export interface AccountUpdateRequest {
  account_name?: string;
  cookies?: string;
  status?: number;
}

// IP 代理相关类型
export interface ProxyConfig {
  enable_ip_proxy: boolean;
  ip_proxy_pool_count: number;
  ip_proxy_provider_name: string;
  kdl_config?: {
    kdl_secert_id: string;
    kdl_signature: string;
    kdl_user_name: string;
    kdl_user_pwd: string;
  } | null;
}

export interface ProxyConfigUpdateRequest {
  enable_ip_proxy?: boolean;
  ip_proxy_pool_count?: number;
  ip_proxy_provider_name?: string;
  kdl_secert_id?: string;
  kdl_signature?: string;
  kdl_user_name?: string;
  kdl_user_pwd?: string;
}

export interface ProxyIpInfo {
  ip: string;
  port: number;
  protocol: string;
  user?: string;
  password?: string;
  expired_time_ts: number;
  is_valid: boolean;
  ttl?: number;
}

export interface ProxyStats {
  total_ips: number;
  valid_ips: number;
  expired_ips: number;
  provider_name: string;
}

// 任务相关类型
export interface Task {
  task_id: string;
  platform: string;
  crawler_type: string;
  status: string;
  created_at: string;
}

export interface TaskCreateRequest {
  platform: string;
  crawler_type: string;
  keywords?: string;
  enable_checkpoint: boolean;
  checkpoint_id?: string;
  max_notes_count: number;
  enable_comments: boolean;
  enable_sub_comments: boolean;
  max_comments_count: number;
  
  // 平台特定的指定ID/URL列表
  xhs_note_url_list?: string[];
  xhs_creator_url_list?: string[];
  weibo_specified_id_list?: string[];
  weibo_creator_id_list?: string[];
  tieba_specified_id_list?: string[];
  tieba_name_list?: string[];
  tieba_creator_url_list?: string[];
  bili_creator_id_list?: string[];
  bili_specified_id_list?: string[];
  dy_specified_id_list?: string[];
  dy_creator_id_list?: string[];
  ks_specified_id_list?: string[];
  ks_creator_id_list?: string[];
  zhihu_creator_url_list?: string[];
  zhihu_specified_id_list?: string[];
}

export interface TaskProgress {
  current: number;
  total: number;
  percentage: number;
}

export interface TaskStatus {
  task_id: string;
  status: string;
  progress?: TaskProgress;
  result?: any;
  error?: string;
  started_at?: string;
  finished_at?: string;
}

// 系统健康检查类型
export interface SystemHealth {
  api_server: string;
  mysql: string;
  redis: string;
  celery: string;
}

// 数据库统计类型
export interface DatabaseStats {
  [platform: string]: {
    notes: number;
    comments: number;
    creators: number;
  };
}

// 笔记内容类型（通用字段）
export interface Note {
  id?: number;
  note_id: string;
  title?: string;
  desc?: string;
  content?: string;
  user_id?: string;
  nickname?: string;
  user_name?: string;
  avatar?: string;
  create_time?: string;
  update_time?: string;
  time?: number; // 笔记发布时间戳（数据库字段）
  last_update_time?: number; // 笔记最后更新时间戳（数据库字段）
  add_ts?: number;
  last_modify_ts?: number;

  // 热词关联字段
  hotspot_id?: number;
  hotspot_keyword?: string;

  // 小红书特定字段
  type?: string; // video 或 normal
  liked_count?: number;
  collected_count?: number;
  comment_count?: number;
  share_count?: number;
  image_list?: string;
  video_url?: string;

  // 抖音/快手特定字段
  video_play_count?: number;
  video_share_count?: number;
  aweme_id?: string;
  video_id?: string;

  // B站特定字段
  video_danmaku?: number;
  video_comment?: number;
  video_like_count?: number;
  video_collect?: number;
  bvid?: string;

  // 微博特定字段
  attitudes_count?: number;
  comments_count?: number;
  reposts_count?: number;
  mblogid?: string;

  // 贴吧特定字段
  total_replay_page?: number;
  view_count?: number;
  thread_id?: string;

  // 知乎特定字段
  content_type?: string;
  voteup_count?: number;
  content_id?: string;
  question_id?: string;
}

// 评论类型（通用字段）
export interface Comment {
  id?: number;
  comment_id: string;
  note_id: string;
  content: string;
  user_id?: string;
  nickname?: string;
  user_name?: string;
  avatar?: string;
  like_count?: number;
  liked_count?: number;
  sub_comment_count?: number;
  create_time?: string;
  update_time?: string;
  add_ts?: number;
  last_modify_ts?: number;
  parent_comment_id?: string;
  
  // 平台特定字段
  ip_location?: string;
  pictures?: string;
}

// 向量相关类型
export interface VectorAddRequest {
  text: string;
  collection_id: string;
  metadata?: Record<string, any>;
}

export interface VectorAddResponse {
  success: boolean;
  vector_id: number;
  message: string;
}

export interface VectorSearchRequest {
  query_text: string;
  collection_id?: string;
  top_k?: number;
  threshold?: number;
}

export interface VectorSearchResult {
  id: number;
  collection_id: string;
  content?: string;
  metadata?: Record<string, any>;
  similarity: number;
  createtime: string;
}

export interface VectorSearchResponse {
  success: boolean;
  results: VectorSearchResult[];
  count: number;
}

export interface VectorDeleteResponse {
  success: boolean;
  message: string;
}

export interface VectorInfo {
  id: number;
  content?: string;
  metadata?: Record<string, any>;
  createtime: string;
}

export interface CollectionInfo {
  collection_id: string;
  count: number;
  vectors: VectorInfo[];
}

export interface ListCollectionsResponse {
  success: boolean;
  collections: CollectionInfo[];
}

// ==================== 热点管理相关类型 ====================

// 热点状态枚举
export type HotspotStatus =
  | 'pending_validation'  // 等待持续性验证
  | 'validated'           // 已验证有持续性
  | 'rejected'            // 已过滤（无商业价值）
  | 'crawling'            // 爬虫进行中
  | 'crawled'             // 爬取完成
  | 'analyzing'           // 商业分析中
  | 'analyzed'            // 分析完成
  | 'archived';           // 已归档

// 优先级枚举
export type Priority = 'high' | 'medium' | 'low';

// 推送状态枚举
export type PushStatus = 'pending' | 'sent' | 'failed';

// 平台信息
export interface PlatformInfo {
  platform: string;
  rank: number;
  heat_score?: number;
  seen_at: string;
}

// 推理详情
export interface ReasoningDetail {
  keep: string[];
  risk: string[];
}

// AI 热词分析结果
export interface KeywordAnalysis {
  id: string;
  title: string;
  confidence: number;
  primaryCategory: string;
  tags: string[];
  reasoning: ReasoningDetail;
  opportunities: string[];
  isRemove: boolean;
}

// 热点详情
export interface HotspotDetail {
  id: number;
  keyword: string;
  normalized_keyword: string;
  embedding_model?: string;
  cluster_id?: number;
  first_seen_at: string;
  last_seen_at: string;
  appearance_count: number;
  platforms: PlatformInfo[];
  status: HotspotStatus;
  last_crawled_at?: string;
  crawl_count: number;
  crawl_started_at?: string;
  crawl_failed_count: number;
  is_filtered: boolean;
  filter_reason?: string;
  filtered_at?: string;
  created_at: string;
  updated_at: string;
}

// 相似热点
export interface SimilarHotspot {
  id: number;
  keyword: string;
  normalized_keyword: string;
  status: HotspotStatus;
  first_seen_at: string;
  last_seen_at: string;
  appearance_count: number;
  similarity: number;
  cluster_id?: number;
}

// 虚拟产品分析
export interface VirtualProductAnalysis {
  opportunities: string[];
  feasibility_score: number;
}

// 实体产品分析
export interface PhysicalProductAnalysis {
  opportunities: string[];
  feasibility_score: number;
}

// 商业报告内容
export interface BusinessReportContent {
  summary: string;
  virtual_products: VirtualProductAnalysis;
  physical_products: PhysicalProductAnalysis;
  target_audience: string[];
  market_size: string;
  recommendations: string[];
}

// 商业报告信息
export interface BusinessReportInfo {
  id: number;
  hotspot_id: number;
  report: BusinessReportContent;
  score: number;
  priority: Priority;
  product_types?: string[];
  analyzed_at: string;
  created_at: string;
}

// 推送队列项
export interface PushQueueItem {
  id: number;
  hotspot_id: number;
  report_id: number;
  priority: Priority;
  score: number;
  status: PushStatus;
  channels: string[];
  scheduled_at?: string;
  sent_at?: string;
  retry_count: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
  keyword?: string;
  report?: BusinessReportContent;
}

// ========== 请求/响应类型 ==========

// 添加热词请求
export interface AddHotspotKeywordRequest {
  analysis: KeywordAnalysis;
  platform_data?: {
    date?: string;
    name?: string;
    rank?: string | number;
    type?: string;
    viewnum?: string;
    url?: string;
    icon?: string;
    word_cover?: any;
    word_type?: string;
  };
}

export interface AddHotspotKeywordResponse {
  success: boolean;
  hotspot_id?: number;
  message: string;
  action: string; // created/rejected/updated
}

// 检查热词请求
export interface CheckHotspotRequest {
  keyword: string;
}

export interface CheckHotspotResponse {
  exists: boolean;
  action: string; // skip/update/ask_llm/create
  hotspot_id?: number;
  similar_hotspots: SimilarHotspot[];
  message: string;
}

// 添加商业报告请求
export interface AddBusinessReportRequest {
  hotspot_id: number;
  report: BusinessReportContent;
  score: number;
  priority: Priority;
  product_types: string[];
}

export interface AddBusinessReportResponse {
  success: boolean;
  report_id: number;
  message: string;
}

// 添加到推送队列请求
export interface AddToPushQueueRequest {
  hotspot_id: number;
  report_id: number;
  channels: string[];
}

export interface AddToPushQueueResponse {
  success: boolean;
  push_id: number;
  message: string;
}

// 获取待推送项响应
export interface GetPendingPushResponse {
  success: boolean;
  items: PushQueueItem[];
  count: number;
}

// 列出热点请求
export interface ListHotspotsRequest {
  page?: number;
  page_size?: number;
  status?: HotspotStatus;
  keyword?: string;
  similarity_search?: string;
  similarity_threshold?: number;
}

export interface ListHotspotsResponse {
  success: boolean;
  total: number;
  page: number;
  page_size: number;
  items: HotspotDetail[];
}

export interface DeleteHotspotResponse {
  success: boolean;
  message: string;
}

// 获取同簇热点响应
export interface GetClusterHotspotsResponse {
  success: boolean;
  cluster_id: number;
  items: HotspotDetail[];
  count: number;
}

// 关联热点请求
export interface LinkHotspotRequest {
  keyword: string;
  hotspot_id: number;
}

export interface LinkHotspotResponse {
  success: boolean;
  hotspot_id: number;
  cluster_id?: number;
  message: string;
}

// ==================== 聚簇管理相关类型 ====================

// 平台统计信息
export interface PlatformStat {
  platform: string;
  count: number;
}

// 聚簇信息
export interface ClusterInfo {
  id: number;
  cluster_name: string;
  member_count: number;
  keywords: string[];
  created_at: string;
  updated_at: string;
  statuses: string[];
  last_hotspot_update: string;
  platforms: PlatformStat[];
}

// 列出聚簇响应
export interface ListClustersResponse {
  success: boolean;
  items: ClusterInfo[];
  count: number;
}

// 创建聚簇请求
export interface CreateClusterRequest {
  cluster_name: string;
  hotspot_ids?: number[];
}

// 创建聚簇响应
export interface CreateClusterResponse {
  success: boolean;
  cluster_id: number;
  message: string;
}

// 合并聚簇请求
export interface MergeClustersRequest {
  source_cluster_ids: number[];
  target_cluster_name?: string;
}

// 合并聚簇响应
export interface MergeClustersResponse {
  success: boolean;
  cluster_id: number;
  message: string;
}

// 拆分聚簇请求
export interface SplitClusterRequest {
  hotspot_ids: number[];
  new_cluster_name?: string;
}

// 拆分聚簇响应
export interface SplitClusterResponse {
  success: boolean;
  new_cluster_id?: number;
  message: string;
}

// 更新聚簇请求
export interface UpdateClusterRequest {
  cluster_name: string;
}

// 更新聚簇响应
export interface UpdateClusterResponse {
  success: boolean;
  message: string;
}

// 删除聚簇响应
export interface DeleteClusterResponse {
  success: boolean;
  message: string;
}

// 从聚簇中移除热点请求
export interface RemoveHotspotFromClusterRequest {
  hotspot_id: number;
}

// 从聚簇中移除热点响应
export interface RemoveHotspotFromClusterResponse {
  success: boolean;
  message: string;
}

