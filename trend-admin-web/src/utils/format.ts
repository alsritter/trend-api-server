import dayjs from 'dayjs';

/**
 * 格式化日期时间
 */
export const formatDateTime = (date: string | number): string => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss');
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
