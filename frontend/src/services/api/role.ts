import request from '@/utils/request'

export interface Role {
  id: string
  name: string
  description: string
  roleType: 'BUILTIN' | 'CUSTOM'
  systemPrompt?: string
  dialogueStyle?: any
  personality?: any
  avatarConfig?: any
  avatar?: string  // 角色头像URL（可能来自数字人图像）
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
    const response = await request.get<Role[]>('/roles/builtin')
    return response.data
  },

  // 获取自定义角色列表
  async getCustomRoles(): Promise<Role[]> {
    const response = await request.get<Role[]>('/roles/custom')
    return response.data
  },

  // 获取角色详情
  async getRole(roleId: string): Promise<Role> {
    const response = await request.get<Role>(`/roles/${roleId}`)
    return response.data
  },

  // 创建自定义角色
  async createRole(roleRequest: RoleCreateRequest): Promise<Role> {
    const response = await request.post<Role>('/roles/custom', roleRequest)
    return response.data
  },

  // 更新角色
  async updateRole(roleId: string, roleRequest: RoleCreateRequest): Promise<Role> {
    const response = await request.put<Role>(`/roles/${roleId}`, roleRequest)
    return response.data
  },

  // 删除角色
  async deleteRole(roleId: string): Promise<void> {
    await request.delete(`/roles/${roleId}`)
  }
}

