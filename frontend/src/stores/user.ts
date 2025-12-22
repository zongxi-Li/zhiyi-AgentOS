import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export interface User {
  id: string
  username: string
  email?: string
  createdAt?: Date
}

export const useUserStore = defineStore('user', () => {
  const currentUser = ref<User | null>(null)
  const loading = ref(false)

  const loadCurrentUser = async () => {
    loading.value = true
    try {
      const userId = localStorage.getItem('userId')
      if (userId) {
        const response = await axios.get(`/api/users/${userId}`)
        currentUser.value = response.data
      }
    } catch (error) {
      console.error('加载用户信息失败', error)
    } finally {
      loading.value = false
    }
  }

  const setCurrentUser = (user: User | null) => {
    currentUser.value = user
    if (user) {
      localStorage.setItem('userId', user.id)
    } else {
      localStorage.removeItem('userId')
    }
  }

  return {
    currentUser,
    loading,
    loadCurrentUser,
    setCurrentUser
  }
})

