import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatApi, type ChatRequest, type ChatResponse } from '@/services/api/chat'

export interface Message {
  id: number | string
  role: 'user' | 'assistant'
  content: string
  createdAt: Date
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const loading = ref(false)
  const contextId = ref<string | null>(null)
  const currentRoleId = ref<string | null>(null)

  const sendMessage = async (text: string, fileUrl?: string) => {
    if ((!text.trim() && !fileUrl) || loading.value) return

    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content: text || (fileUrl ? '[文件]' : ''),
      createdAt: new Date()
    }
    if (fileUrl) {
      (userMessage as any).fileUrl = fileUrl
    }
    messages.value.push(userMessage)

    loading.value = true
    try {
      const request: ChatRequest = {
        text: text || '',
        roleId: currentRoleId.value || undefined,
        contextId: contextId.value || undefined,
        fileUrl: fileUrl || undefined
      }

      const response = await chatApi.sendMessage(request)
      contextId.value = response.contextId

      const assistantMessage: Message = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.text,
        createdAt: new Date()
      }
      messages.value.push(assistantMessage)

      return response
    } finally {
      loading.value = false
    }
  }

  const clearHistory = async () => {
    if (contextId.value) {
      await chatApi.clearHistory(contextId.value)
    }
    messages.value = []
    contextId.value = null
  }

  const setRole = (roleId: string | null) => {
    currentRoleId.value = roleId
  }

  // 加载对话历史
  const loadHistory = async (targetContextId: string) => {
    if (!targetContextId) return

    loading.value = true
    try {
      const history = await chatApi.getHistory(targetContextId)
      
      // 将后端消息格式转换为前端格式
      messages.value = history.map((msg: any) => ({
        id: msg.id || Date.now() + Math.random(),
        role: msg.role?.toLowerCase() === 'user' ? 'user' : 'assistant',
        content: msg.content || '',
        createdAt: msg.createdAt ? new Date(msg.createdAt) : new Date(),
        fileUrl: msg.fileUrl
      }))
      
      contextId.value = targetContextId
    } catch (error: any) {
      console.error('加载对话历史失败:', error)
      messages.value = []
    } finally {
      loading.value = false
    }
  }

  // 设置上下文ID（用于从外部设置，如从对话列表选择）
  const setContextId = (id: string | null) => {
    contextId.value = id
    if (id) {
      loadHistory(id)
    } else {
      messages.value = []
    }
  }

  return {
    messages,
    loading,
    contextId,
    currentRoleId,
    sendMessage,
    clearHistory,
    setRole,
    loadHistory,
    setContextId
  }
})

