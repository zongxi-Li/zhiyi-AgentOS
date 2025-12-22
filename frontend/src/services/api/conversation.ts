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

export interface Conversation {
  id: string
  userId: string
  roleId?: string
  contextId: string
  createdAt: string
  updatedAt: string
}

export const conversationApi = {
  // 获取用户的对话列表
  async getUserConversations(): Promise<Conversation[]> {
    const response = await api.get<Conversation[]>('/conversations')
    return response.data
  },

  // 获取对话详情
  async getConversation(contextId: string): Promise<Conversation> {
    const response = await api.get<Conversation>(`/conversations/${contextId}`)
    return response.data
  },

  // 删除对话
  async deleteConversation(conversationId: string): Promise<void> {
    await api.delete(`/conversations/${conversationId}`)
  }
}

