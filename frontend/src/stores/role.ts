import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { roleApi, type Role, type RoleCreateRequest } from '@/services/api/role'

export const useRoleStore = defineStore('role', () => {
  const builtinRoles = ref<Role[]>([])
  const customRoles = ref<Role[]>([])
  const currentRole = ref<Role | null>(null)
  const loading = ref(false)

  // 计算属性：所有角色
  const roles = computed(() => [...builtinRoles.value, ...customRoles.value])

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

  // 选择角色
  const selectRole = (role: Role) => {
    currentRole.value = role
  }

  // 设置当前角色（别名方法）
  const setCurrentRole = (role: Role) => {
    currentRole.value = role
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

