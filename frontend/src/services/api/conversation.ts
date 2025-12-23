import request from '@/utils/request'

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
  async getUserConversations(userId?: string): Promise<Conversation[]> {
    const headers: Record<string, string> = {}
    if (userId) {
      headers['X-User-Id'] = userId
    }
    const response = await request.get<Conversation[]>('/conversations', { headers })
    return response.data
  },

  // 获取对话详情
  async getConversation(contextId: string): Promise<Conversation> {
    const response = await request.get<Conversation>(`/conversations/${contextId}`)
    return response.data
  },

  // 删除对话
  async deleteConversation(conversationId: string): Promise<void> {
    await request.delete(`/conversations/${conversationId}`)
  }
}

