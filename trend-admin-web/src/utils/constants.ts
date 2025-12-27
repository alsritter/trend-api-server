export const PLATFORM_OPTIONS = [
  { label: '小红书', value: 'xhs' },
  { label: '抖音', value: 'dy' },
  { label: '快手', value: 'ks' },
  { label: 'B站', value: 'bili' },
  { label: '微博', value: 'wb' },
  { label: '贴吧', value: 'tieba' },
  { label: '知乎', value: 'zhihu' },
];

export const CRAWLER_TYPE_OPTIONS = [
  { label: '搜索', value: 'search' },
  { label: '详情', value: 'detail' },
  { label: '创作者', value: 'creator' },
  { label: '首页推荐', value: 'homefeed' },
];

export const TASK_STATUS_MAP = {
  PENDING: { color: 'default', text: '待执行' },
  STARTED: { color: 'processing', text: '执行中' },
  PROGRESS: { color: 'processing', text: '进行中' },
  SUCCESS: { color: 'success', text: '已完成' },
  FAILURE: { color: 'error', text: '失败' },
  REVOKED: { color: 'warning', text: '已取消' },
} as const;

export const ACCOUNT_STATUS_MAP = {
  0: { color: 'success', text: '正常' },
  '-1': { color: 'error', text: '失效' },
} as const;
