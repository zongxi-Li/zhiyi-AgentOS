import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { roleApi, type Role, type RoleCreateRequest } from '@/services/api/role'
import { digitalHumanApi } from '@/services/api/digitalHuman'

export const useRoleStore = defineStore('role', () => {
  const builtinRoles = ref<Role[]>([])
  const customRoles = ref<Role[]>([])
  const currentRole = ref<Role | null>(null)
  const favorites = ref<string[]>([])
  const loading = ref(false)

  // 计算属性：所有角色
  const roles = computed(() => [...builtinRoles.value, ...customRoles.value])

  const favoriteRoles = computed(() => {
    return roles.value.filter(r => favorites.value.includes(r.id))
  })

  // 收藏/取消收藏
  const toggleFavorite = (roleId: string) => {
    const index = favorites.value.indexOf(roleId)
    if (index === -1) {
      favorites.value.push(roleId)
    } else {
      favorites.value.splice(index, 1)
    }
    // In a real app, save to localStorage or API
    localStorage.setItem('role_favorites', JSON.stringify(favorites.value))
  }

  // 加载收藏
  const loadFavorites = () => {
    const stored = localStorage.getItem('role_favorites')
    if (stored) favorites.value = JSON.parse(stored)
  }

  // 加载内置角色
  const loadBuiltinRoles = async () => {
    loading.value = true
    try {
      builtinRoles.value = await roleApi.getBuiltinRoles()
    } finally {
      loading.value = false
    }
  }

  // 加载自定义角色
  const loadCustomRoles = async () => {
    loading.value = true
    try {
      customRoles.value = await roleApi.getCustomRoles()
    } finally {
      loading.value = false
    }
  }

  // 加载所有角色
  const loadRoles = async () => {
    loading.value = true
    try {
      await Promise.all([
        loadBuiltinRoles(),
        loadCustomRoles()
      ])
    } finally {
      loading.value = false
    }
  }

  // 选择角色（同时尝试获取数字人图像作为头像）
  const selectRole = async (role: Role) => {
    currentRole.value = role
    // 尝试获取数字人图像，如果存在则更新角色头像
    try {
      const dhResponse = await digitalHumanApi.getDigitalHuman(role.id)
      if (dhResponse && dhResponse.success && dhResponse.data) {
        const avatarUrl = dhResponse.data.avatar || dhResponse.data.local_image_url
        if (avatarUrl && role.avatar !== avatarUrl) {
          // 更新当前角色的头像
          role.avatar = avatarUrl
          // 同时更新列表中的角色头像
          const roleInList = roles.value.find(r => r.id === role.id)
          if (roleInList) {
            roleInList.avatar = avatarUrl
          }
        }
      }
    } catch (e) {
      // 数字人不存在或获取失败，忽略错误
      console.debug('获取数字人图像失败:', e)
    }
  }

  // 设置当前角色（别名方法，同时尝试获取数字人图像）
  const setCurrentRole = async (role: Role) => {
    currentRole.value = role
    // 尝试获取数字人图像，如果存在则更新角色头像
    try {
      const dhResponse = await digitalHumanApi.getDigitalHuman(role.id)
      if (dhResponse && dhResponse.success && dhResponse.data) {
        const avatarUrl = dhResponse.data.avatar || dhResponse.data.local_image_url
        if (avatarUrl) {
          // 更新当前角色的头像
          role.avatar = avatarUrl
          // 同时更新列表中的角色头像
          const roleInList = roles.value.find(r => r.id === role.id)
          if (roleInList) {
            roleInList.avatar = avatarUrl
          }
        }
      }
    } catch (e) {
      // 数字人不存在或获取失败，忽略错误
      console.debug('获取数字人图像失败:', e)
    }
  }
  
  // 更新角色头像（用于数字人创建成功后）
  const updateRoleAvatar = (roleId: string, avatarUrl: string) => {
    const role = roles.value.find(r => r.id === roleId)
    if (role) {
      role.avatar = avatarUrl
    }
    if (currentRole.value && currentRole.value.id === roleId) {
      currentRole.value.avatar = avatarUrl
    }
  }

  // 添加角色（用于创建后添加到列表）
  const addRole = (role: Role) => {
    if (role.isBuiltin) {
      builtinRoles.value.push(role)
    } else {
      customRoles.value.push(role)
    }
  }

  // 创建自定义角色
  const createRole = async (request: RoleCreateRequest) => {
    loading.value = true
    try {
      const role = await roleApi.createRole(request)
      customRoles.value.push(role)
      return role
    } finally {
      loading.value = false
    }
  }

  // 更新角色
  const updateRole = async (roleId: string, request: RoleCreateRequest) => {
    loading.value = true
    try {
      const role = await roleApi.updateRole(roleId, request)
      const index = customRoles.value.findIndex(r => r.id === roleId)
      if (index !== -1) {
        customRoles.value[index] = role
      }
      if (currentRole.value?.id === roleId) {
        currentRole.value = role
      }
      return role
    } finally {
      loading.value = false
    }
  }

  // 删除角色
  const deleteRole = async (roleId: string) => {
    loading.value = true
    try {
      await roleApi.deleteRole(roleId)
      customRoles.value = customRoles.value.filter(r => r.id !== roleId)
      if (currentRole.value?.id === roleId) {
        currentRole.value = null
      }
    } finally {
      loading.value = false
    }
  }

  return {
    builtinRoles,
    customRoles,
    roles,
    currentRole,
    loading,
    favorites,
    favoriteRoles,
    toggleFavorite,
    loadFavorites,
    loadBuiltinRoles,
    loadCustomRoles,
    loadRoles,
    selectRole,
    setCurrentRole,
    addRole,
    createRole,
    updateRole,
    deleteRole
  }
})

