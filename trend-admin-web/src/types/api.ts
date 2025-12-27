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
