import dayjs from 'dayjs';

/**
 * 格式化日期时间
 * 支持秒级和毫秒级时间戳
 */
export const formatDateTime = (date: string | number): string => {
  if (!date) return '-';
  const timestamp = typeof date === 'string' ? parseInt(date, 10) : date;
  // 如果是秒级时间戳（10位数字），转换为毫秒
  const ms = timestamp.toString().length === 10 ? timestamp * 1000 : timestamp;
  return dayjs(ms).format('YYYY-MM-DD HH:mm:ss');
};

/**
 * 格式化日期
 */
export const formatDate = (date: string | number): string => {
  return dayjs(date).format('YYYY-MM-DD');
};

/**
 * 计算倒计时
 */
export const formatCountdown = (timestamp: number): string => {
  const now = Math.floor(Date.now() / 1000);
  const diff = timestamp - now;

  if (diff <= 0) {
    return '已过期';
  }

  const hours = Math.floor(diff / 3600);
  const minutes = Math.floor((diff % 3600) / 60);
  const seconds = diff % 60;

  if (hours > 0) {
    return `${hours}小时${minutes}分`;
  } else if (minutes > 0) {
    return `${minutes}分${seconds}秒`;
  } else {
    return `${seconds}秒`;
  }
};

/**
 * 格式化数字（添加千分位）
 */
export const formatNumber = (num: number): string => {
  return num.toLocaleString('zh-CN');
};

/**
 * 根据平台获取内容ID
 * 不同平台的内容ID字段名不同
 */
export const getContentId = (platform: string, note: any): string => {
  const contentIdFields: Record<string, string> = {
    'dy': 'aweme_id',      // 抖音
    'bili': 'video_id',    // B站
    'ks': 'video_id',      // 快手
    'zhihu': 'content_id', // 知乎
    'xhs': 'note_id',      // 小红书
    'wb': 'note_id',       // 微博
    'tieba': 'note_id',    // 贴吧
  };

  const fieldName = contentIdFields[platform] || 'note_id';
  return note[fieldName] || note.note_id || '';
};
