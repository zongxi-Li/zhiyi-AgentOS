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

export interface Role {
  id: string
  name: string
  description: string
  roleType: 'BUILTIN' | 'CUSTOM'
  systemPrompt?: string
  dialogueStyle?: any
  personality?: any
  avatarConfig?: any
}

export interface RoleCreateRequest {
  name: string
  description?: string
  systemPrompt: string
  dialogueStyle?: any
  personality?: any
  avatarConfig?: any
}

export const roleApi = {
  // 获取内置角色列表
  async getBuiltinRoles(): Promise<Role[]> {
    const response = await api.get<Role[]>('/roles/builtin')
    return response.data
  },

  // 获取自定义角色列表
  async getCustomRoles(): Promise<Role[]> {
    const response = await api.get<Role[]>('/roles/custom')
    return response.data
  },

  // 获取角色详情
  async getRole(roleId: string): Promise<Role> {
    const response = await api.get<Role>(`/roles/${roleId}`)
    return response.data
  },

  // 创建自定义角色
  async createRole(request: RoleCreateRequest): Promise<Role> {
    const response = await api.post<Role>('/roles/custom', request)
    return response.data
  },

  // 更新角色
  async updateRole(roleId: string, request: RoleCreateRequest): Promise<Role> {
    const response = await api.put<Role>(`/roles/${roleId}`, request)
    return response.data
  },

  // 删除角色
  async deleteRole(roleId: string): Promise<void> {
    await api.delete(`/roles/${roleId}`)
  }
}

