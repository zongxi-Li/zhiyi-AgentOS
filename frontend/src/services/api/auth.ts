import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  token: string
  userId: string
  username: string
  message: string
}

export const authApi = {
  // 登录
  async login(request: LoginRequest): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/auth/login', request)
    return response.data
  },

  // 注册
  async register(request: LoginRequest): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/auth/register', request)
    return response.data
  },

  // 验证Token
  async verifyToken(): Promise<{ valid: boolean; userId?: string; username?: string }> {
    const token = localStorage.getItem('token')
    if (!token) {
      return { valid: false }
    }

    try {
      const response = await api.get('/auth/verify', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      return response.data
    } catch {
      return { valid: false }
    }
  }
}

