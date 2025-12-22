import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '@/views/ChatView.vue'
import RoleView from '@/views/RoleView.vue'
import SettingsView from '@/views/SettingsView.vue'
import VoiceChatView from '@/views/VoiceChatView.vue'
import LoginView from '@/views/LoginView.vue'
import RagView from '@/views/RagView.vue'
import { authApi } from '@/services/api/auth'

const routes = [
  {
    path: '/',
    redirect: '/chat'
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: {
      title: '登录',
      requiresAuth: false
    }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: ChatView,
    meta: {
      title: '文本对话',
      requiresAuth: true
    }
  },
  {
    path: '/voice',
    name: 'VoiceChat',
    component: VoiceChatView,
    meta: {
      title: '语音对话',
      requiresAuth: true
    }
  },
  {
    path: '/roles',
    name: 'Roles',
    component: RoleView,
    meta: {
      title: '角色管理',
      requiresAuth: true
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: SettingsView,
    meta: {
      title: '设置',
      requiresAuth: true
    }
  },
  {
    path: '/rag',
    name: 'RAG',
    component: RagView,
    meta: {
      title: '知识库查询',
      requiresAuth: true
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - Kinlin AI` : 'Kinlin AI'
  
  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('token')
    if (!token) {
      next('/login')
      return
    }
    
    // 验证Token
    const result = await authApi.verifyToken()
    if (!result.valid) {
      localStorage.removeItem('token')
      localStorage.removeItem('userId')
      next('/login')
      return
    }
  }
  
  // 如果已登录，访问登录页则跳转到首页
  if (to.path === '/login') {
    const token = localStorage.getItem('token')
    if (token) {
      const result = await authApi.verifyToken()
      if (result.valid) {
        next('/chat')
        return
      }
    }
  }
  
  next()
})

export default router

