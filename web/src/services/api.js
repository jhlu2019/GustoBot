import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// API 方法
export const sendMessage = async (data) => {
  return await apiClient.post('/chat/', data)
}

export const searchKnowledge = async (query, topK = 5) => {
  return await apiClient.post('/knowledge/search', {
    query,
    top_k: topK
  })
}

export const addRecipe = async (recipeData) => {
  return await apiClient.post('/knowledge/recipes', recipeData)
}

export const getSystemStatus = async () => {
  return await apiClient.get('/chat/status')
}

export const getKnowledgeStats = async () => {
  return await apiClient.get('/knowledge/stats')
}

export default apiClient
