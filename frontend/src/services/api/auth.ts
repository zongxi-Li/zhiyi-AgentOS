import request from '@/utils/request'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  token?: string
  userId?: string | number
  username?: string
  message?: string
  success?: boolean
}

export const authApi = {
  // 登录
  async login(loginRequest: LoginRequest): Promise<LoginResponse & { success?: boolean }> {
    const response = await request.post<LoginResponse & { success?: boolean }>('/auth/login', loginRequest)
    return response.data
  },

  // 注册
  async register(registerRequest: LoginRequest): Promise<LoginResponse & { success?: boolean }> {
    const response = await request.post<LoginResponse & { success?: boolean }>('/auth/register', registerRequest)
    return response.data
  },

  // 验证Token
  async verifyToken(): Promise<{ valid: boolean; userId?: string; username?: string }> {
    const token = localStorage.getItem('token')
    if (!token) {
      return { valid: false }
    }

    try {
      const response = await request.get<{ valid: boolean; userId?: string; username?: string }>('/auth/verify')
      return response.data
    } catch {
      return { valid: false }
    }
  }
}

