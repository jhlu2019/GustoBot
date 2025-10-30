import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

class ChatService {
  static async sendMessage(payload) {
    try {
      const response = await api.post('/api/v1/chat/chat', payload);
      return response;
    } catch (error) {
      throw new Error(error.response?.data?.detail || '发送消息失败');
    }
  }

  static async sendStreamMessage(payload, onChunk) {
    try {
      const params = new URLSearchParams({
        message: payload.message,
        session_id: payload.session_id || '',
        user_id: payload.user_id || 'web_user',
        file_path: payload.file_path || '',
        image_path: payload.image_path || ''
      });

      const response = await fetch(`${API_BASE_URL}/api/v1/chat/chat/stream?${params}`, {
        method: 'GET',
        headers: {
          'Accept': 'text/event-stream',
        },
      });

      if (!response.ok) {
        throw new Error('Stream request failed');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              onChunk(data);
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      throw new Error('流式请求失败');
    }
  }

  static async getChatHistory(sessionId) {
    try {
      const response = await api.get(`/api/v1/chat/history/${sessionId}`);
      return response;
    } catch (error) {
      throw new Error('获取历史记录失败');
    }
  }

  static async clearSession(sessionId) {
    try {
      const response = await api.delete(`/api/v1/chat/session/${sessionId}`);
      return response;
    } catch (error) {
      throw new Error('清空会话失败');
    }
  }

  static async getRouteInfo() {
    try {
      const response = await api.get('/api/v1/chat/routes');
      return response;
    } catch (error) {
      throw new Error('获取路由信息失败');
    }
  }

  static async uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/upload/upload/file`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000,
      });
      return response.data;
    } catch (error) {
      throw new Error('文件上传失败');
    }
  }

  static async uploadImage(file) {
    const formData = new FormData();
    formData.append('image', file);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/upload/upload/image`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000,
      });
      return response.data;
    } catch (error) {
      throw new Error('图片上传失败');
    }
  }
}

export default ChatService;