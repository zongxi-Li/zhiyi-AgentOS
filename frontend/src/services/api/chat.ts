import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器：添加Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：处理401错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('userId')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export interface ChatRequest {
  text: string
  roleId?: string
  contextId?: string
  fileUrl?: string
}

export interface ChatResponse {
  text: string
  contextId: string
  confidence: number
  tokensUsed?: number
  animation?: any
}

export const chatApi = {
  // 发送文本消息
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await api.post<ChatResponse>('/chat/text', request)
    return response.data
  },

  // 获取对话历史
  async getHistory(contextId: string) {
    const response = await api.get(`/chat/history/${contextId}`)
    return response.data
  },

  // 清除对话历史
  async clearHistory(contextId: string) {
    await api.delete(`/chat/history/${contextId}`)
  }
}

