import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000, // 语音处理可能需要更长时间
  headers: {
    'Content-Type': 'multipart/form-data'
  }
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

export interface VoiceChatRequest {
  audio: File
  roleId?: string
  contextId?: string
}

export interface VoiceChatResponse {
  text: string
  contextId: string
  confidence: number
  recognizedText?: string
}

export const voiceApi = {
  // 发送语音消息
  async sendVoiceMessage(request: VoiceChatRequest): Promise<VoiceChatResponse> {
    const formData = new FormData()
    formData.append('audio', request.audio)
    if (request.roleId) {
      formData.append('roleId', request.roleId)
    }
    if (request.contextId) {
      formData.append('contextId', request.contextId)
    }

    const response = await api.post<VoiceChatResponse>('/voice/chat', formData)
    return response.data
  },

  // 文本转语音
  async textToSpeech(
    text: string, 
    voice: string = 'default', 
    speed: number = 1.0, 
    pitch: number = 1.0
  ): Promise<Blob> {
    const response = await api.post(
      '/voice/tts',
      {
        text,
        voice,
        speed,
        pitch
      },
      {
        responseType: 'blob'
      }
    )
    return response.data
  }
}

