<template>
  <ErrorBoundary>
    <div id="app">
      <el-container class="app-layout" :class="{ 'immersive-mode': isImmersive }">
        <!-- Sidebar Navigation -->
        <el-aside width="260px" class="app-sidebar" v-if="!isImmersive">
          <!-- Logo Section -->
          <div class="sidebar-header" @click="router.push('/chat')">
            <div class="logo-icon">K</div>
            <span class="logo-text">Kinlin AI</span>
          </div>

          <!-- Main Navigation -->
          <div class="sidebar-nav">
            <el-menu
              :default-active="activeMenu"
              router
              class="sidebar-menu"
            >
              <div class="menu-group-title">MAIN</div>
              <el-menu-item index="/chat">
                <el-icon><ChatDotRound /></el-icon>
                <span>对话</span>
              </el-menu-item>
              <el-menu-item index="/digital-human">
                <el-icon><UserFilled /></el-icon>
                <span>数字人</span>
              </el-menu-item>
              <el-menu-item index="/voice">
                <el-icon><Microphone /></el-icon>
                <span>语音交互</span>
              </el-menu-item>

              <div class="menu-group-title">KNOWLEDGE</div>
              <el-menu-item index="/rag">
                <el-icon><Search /></el-icon>
                <span>知识库</span>
              </el-menu-item>
              <el-menu-item index="/history">
                <el-icon><Clock /></el-icon>
                <span>历史记录</span>
              </el-menu-item>

              <div class="menu-group-title">SYSTEM</div>
              <el-menu-item index="/roles">
                <el-icon><User /></el-icon>
                <span>角色管理</span>
              </el-menu-item>
              <el-menu-item index="/settings">
                <el-icon><Setting /></el-icon>
                <span>设置</span>
              </el-menu-item>
            </el-menu>
          </div>

          <!-- User Profile / Bottom Section -->
          <div class="sidebar-footer">
            <div class="user-profile" @click="router.push('/user')">
              <el-avatar :size="32" class="user-avatar">U</el-avatar>
              <div class="user-info">
                <span class="user-name">User</span>
                <span class="user-status">Online</span>
              </div>
            </div>
          </div>
        </el-aside>

        <!-- Main Content Area -->
        <el-container class="main-container">
          <!-- Global Error Banner (Floating) -->
          <transition name="fade">
            <div v-if="globalError" class="global-error-banner">
              <el-alert
                :title="globalError"
                type="error"
                show-icon
                @close="clearGlobalError"
              />
            </div>
          </transition>

          <el-main class="app-main">
            <router-view v-slot="{ Component }">
              <transition name="fade" mode="out-in">
                <component :is="Component" />
              </transition>
            </router-view>
          </el-main>
        </el-container>
      </el-container>
    </div>
  </ErrorBoundary>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  ChatDotRound, User, UserFilled, Microphone, Search, 
  Clock, Setting
} from '@element-plus/icons-vue'
import ErrorBoundary from '@/components/ErrorBoundary.vue'

const route = useRoute()
const router = useRouter()
const globalError = ref('')

// 判断是否为沉浸式模式（如语音交互界面）
const isImmersive = computed(() => {
  return route.path.startsWith('/voice')
})

const activeMenu = computed(() => {
  const path = route.path
  if (path === '/chat' || path.startsWith('/chat')) return '/chat'
  if (path === '/digital-human' || path.startsWith('/digital-human')) return '/digital-human'
  if (path === '/voice' || path.startsWith('/voice')) return '/voice'
  if (path === '/roles' || path.startsWith('/roles')) return '/roles'
  if (path === '/rag' || path.startsWith('/rag')) return '/rag'
  if (path === '/settings' || path.startsWith('/settings')) return '/settings'
  if (path.startsWith('/history')) return '/history'
  if (path.startsWith('/user')) return '/settings' // User goes to settings
  return path
})

const clearGlobalError = () => {
  globalError.value = ''
}

const handleGlobalError = (event: CustomEvent) => {
  const detail = event.detail
  if (detail.clear) {
    globalError.value = ''
    return
  }
  
  if (detail.message) {
    globalError.value = detail.message
    const duration = detail.duration || 5000
    setTimeout(() => {
      clearGlobalError()
    }, duration)
  }
}

onMounted(() => {
  window.addEventListener('global-error', handleGlobalError as EventListener)
})

onUnmounted(() => {
  window.removeEventListener('global-error', handleGlobalError as EventListener)
})
</script>

<style scoped>
.app-layout {
  height: 100vh;
  width: 100vw;
  background-color: var(--bg-app);
}

/* Sidebar Styles */
.app-sidebar {
  background-color: var(--bg-sidebar);
  border-right: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
}

.sidebar-header {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  cursor: pointer;
  gap: 12px;
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-active));
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-family: var(--font-serif);
  font-size: 18px;
  box-shadow: 0 2px 10px rgba(99, 102, 241, 0.3);
}

.logo-text {
  font-family: var(--font-serif);
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 8px;
  overflow-y: auto;
}

.menu-group-title {
  padding: 12px 16px 8px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-disabled);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.sidebar-menu {
  border: none;
  background: transparent;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border-light);
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color 0.2s;
}

.user-profile:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.user-avatar {
  background-color: var(--primary-color);
  color: white;
  font-weight: 600;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.user-status {
  font-size: 12px;
  color: var(--success);
}

/* Main Content Styles */
.main-container {
  background-color: var(--bg-app);
  position: relative;
  display: flex;
  flex-direction: column;
}

.app-main {
  padding: 0;
  overflow: hidden;
  height: 100%;
}

.global-error-banner {
  position: absolute;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2000;
  min-width: 300px;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Immersive Mode Overrides */
.immersive-mode .main-container {
  background-color: #0f1115; /* Match VoiceChatView background */
}
</style>
