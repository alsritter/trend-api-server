import axios from 'axios';
import { message } from 'antd';

const isDev = import.meta.env.DEV;
const baseURL = isDev ? 'http://localhost:8000' : '';

// 创建 axios 实例
export const apiClient = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    const { code, message: msg, data } = response.data;

    // API 返回的 code 不为 0 时，视为业务错误
    if (code !== 0) {
      message.error(msg || '请求失败');
      return Promise.reject(new Error(msg || '请求失败'));
    }

    return data;
  },
  (error) => {
    // 网络错误或服务器错误
    if (error.response) {
      const status = error.response.status;
      if (status === 404) {
        message.error('请求的资源不存在');
      } else if (status === 500) {
        message.error('服务器错误');
      } else {
        message.error(error.response.data?.detail || '请求失败');
      }
    } else if (error.request) {
      message.error('网络连接失败，请检查网络');
    } else {
      message.error(error.message || '请求失败');
    }

    return Promise.reject(error);
  }
);
