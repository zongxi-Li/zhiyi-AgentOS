import request from '@/utils/request'

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
  async sendVoiceMessage(voiceRequest: VoiceChatRequest): Promise<VoiceChatResponse> {
    const formData = new FormData()
    formData.append('audio', voiceRequest.audio)
    if (voiceRequest.roleId) {
      formData.append('roleId', voiceRequest.roleId)
    }
    if (voiceRequest.contextId) {
      formData.append('contextId', voiceRequest.contextId)
    }

    const response = await request.post<VoiceChatResponse>('/voice/chat', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  // 文本转语音
  async textToSpeech(
    text: string, 
    voice: string = 'default', 
    speed: number = 1.0, 
    pitch: number = 1.0
  ): Promise<Blob> {
    const response = await request.post(
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

