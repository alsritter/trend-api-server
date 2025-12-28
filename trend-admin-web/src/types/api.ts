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
  expired_time_ts: number;
  is_valid: boolean;
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
  add_ts?: number;
  last_modify_ts?: number;
  
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
