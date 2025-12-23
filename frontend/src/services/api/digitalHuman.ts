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

// 响应拦截器：处理错误
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // 如果响应中有数据，返回数据；否则返回错误信息
    if (error.response && error.response.data) {
      return Promise.reject(error.response.data)
    }
    return Promise.reject(error)
  }
)

export interface DigitalHumanRequest {
  roleId: string
  personality?: string
  profession?: string
  style?: string
}

export interface DigitalHumanResponse {
  success: boolean
  data?: any
  message?: string
}

export const digitalHumanApi = {
  /**
   * 创建数字人
   */
  async createDigitalHuman(request: DigitalHumanRequest): Promise<DigitalHumanResponse> {
    const response = await api.post<DigitalHumanResponse>('/digital-human/create', request)
    return response.data
  },

  /**
   * 更新数字人动画
   */
  async updateAnimation(
    roleId: string,
    text: string,
    audioFile: File
  ): Promise<DigitalHumanResponse> {
    const formData = new FormData()
    formData.append('roleId', roleId)
    formData.append('text', text)
    formData.append('audio', audioFile)

    const response = await api.post<DigitalHumanResponse>(
      '/digital-human/animation',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
    return response.data
  },

  /**
   * 切换数字人风格
   */
  async switchStyle(roleId: string, newStyle: string): Promise<DigitalHumanResponse> {
    const response = await api.post<DigitalHumanResponse>('/digital-human/style', null, {
      params: {
        roleId,
        newStyle
      }
    })
    return response.data
  }
}

