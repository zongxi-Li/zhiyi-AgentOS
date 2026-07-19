<!-- 知弈平台根布局组件 — 侧边栏导航（对话、职业工作台、ACG 引擎、RAG 知识库、联邦学习），含错误边界和沉浸/简洁模式 -->
<template>
  <ErrorBoundary>
    <div id="app">
      <el-container class="app-layout" :class="{ 'immersive-mode': isImmersive }">
        <!-- Sidebar Navigation -->
        <el-aside
          v-if="!isImmersive && !usesDrawerNavigation"
          :width="sidebarAsideWidth"
          class="app-sidebar"
          :class="{ collapsed: mainSidebarCompact, 'chat-panel-open': chatNavOpen, resizing: sidebarResizing || chatPanelResizing }"
        >
          <div class="primary-sidebar" :style="{ width: primarySidebarWidth }">
          <!-- Logo Section -->
          <div class="sidebar-header">
            <button class="sidebar-brand" type="button" aria-label="返回对话" @click="router.push('/chat')">
              <span class="logo-icon">
                <el-icon><Connection /></el-icon>
              </span>
              <span v-if="!mainSidebarCompact" class="logo-text">知弈</span>
            </button>
            <button
              class="sidebar-collapse-btn"
              type="button"
              :aria-label="chatNavOpen ? '关闭聊天面板' : (sidebarCollapsed ? '展开侧边栏' : '收起侧边栏')"
              :title="chatNavOpen ? '关闭聊天面板' : (sidebarCollapsed ? '展开侧边栏' : '收起侧边栏')"
              @click="toggleSidebar"
            >
              <el-icon><Expand v-if="mainSidebarCompact" /><Fold v-else /></el-icon>
            </button>
          </div>

          <!-- Main Navigation -->
          <div class="sidebar-nav" ref="sidebarNav">
            <el-menu
              :default-active="activeMenu"
              router
              class="sidebar-menu"
              :collapse="mainSidebarCompact"
              :collapse-transition="false"
              @wheel="handleSidebarWheel"
            >
              <div v-if="!mainSidebarCompact" class="menu-group-title">{{ $t('nav.main') }}</div>
              <div
                class="chat-nav-group"
                :class="{ active: route.path.startsWith('/chat'), open: chatNavOpen }"
              >
                <button
                  class="chat-nav-trigger"
                  type="button"
                  :aria-expanded="chatNavOpen"
                  aria-controls="chat-side-panel"
                  @click="handleChatNavToggle"
                >
                  <el-icon><ChatDotRound /></el-icon>
                  <span v-if="!mainSidebarCompact" class="chat-nav-label">{{ $t('nav.chat') }}</span>
                  <el-icon v-if="!mainSidebarCompact" class="chat-nav-chevron">
                    <ArrowDown v-if="chatNavOpen" />
                    <ArrowRight v-else />
                  </el-icon>
                </button>

              </div>
              <el-menu-item index="/agentos/legal/contract-review">
                <el-icon><DocumentChecked /></el-icon>
                <span>角色工作台</span>
              </el-menu-item>

              <el-menu-item index="/agentos/acg">
                <el-icon><Cpu /></el-icon>
                <span>ACG 动态群体智能引擎</span>
              </el-menu-item>

              <div v-if="!mainSidebarCompact" class="menu-group-title">{{ $t('nav.knowledge') }}</div>
              <el-menu-item index="/rag">
                <el-icon><Search /></el-icon>
                <span>{{ $t('nav.rag') }}</span>
              </el-menu-item>

              <div v-if="!mainSidebarCompact" class="menu-group-title">{{ $t('nav.system') }}</div>
              <el-menu-item index="/agentos-console">
                <el-icon><Monitor /></el-icon>
                <span>AgentOS 运维</span>
              </el-menu-item>
              <el-menu-item index="/roles">
                <el-icon><User /></el-icon>
                <span>{{ $t('nav.roles') }}</span>
              </el-menu-item>
              <el-menu-item index="/federated-learning">
                <el-icon><Connection /></el-icon>
                <span>联邦管理</span>
              </el-menu-item>
              <el-menu-item index="/federated-models">
                <el-icon><Cpu /></el-icon>
                <span>模型管理</span>
              </el-menu-item>
              <el-menu-item index="/settings">
                <el-icon><Setting /></el-icon>
                <span>{{ $t('nav.settings') }}</span>
              </el-menu-item>
            </el-menu>
          </div>

          <!-- User Profile / Bottom Section -->
          <div class="sidebar-footer">
            <div class="user-profile" @click="router.push('/user')">
              <el-avatar :size="32" class="user-avatar">U</el-avatar>
              <div v-if="!mainSidebarCompact" class="user-info">
                <span class="user-name">User</span>
                <span class="user-status">Online</span>
              </div>
            </div>
            <div v-if="!mainSidebarCompact" class="logout-section">
              <el-button 
                class="logout-btn" 
                type="danger" 
                size="small" 
                @click="handleLogout"
                :icon="SwitchButton"
              >
                退出登录
              </el-button>
            </div>
          </div>
          </div>

          <Transition name="chat-panel">
            <section
              v-if="chatNavOpen"
              id="chat-side-panel"
              class="chat-side-panel"
              :style="{ width: `${chatPanelWidth}px` }"
              aria-label="聊天项目"
            >
              <div class="chat-panel-header">
                <div class="chat-panel-switch" role="tablist" aria-label="工作模式">
                  <div class="agent-switch-entry" @mouseenter="ensureSidebarRoles">
                    <button
                      :class="{ active: workspaceMode === 'agent' }"
                      type="button"
                      role="tab"
                      :aria-selected="workspaceMode === 'agent'"
                      @click="selectWorkspaceMode('agent')"
                    >
                      Agent
                    </button>
                    <div class="agent-hover-menu role-switch-menu" role="menu" aria-label="切换 Agent 角色">
                      <div v-if="roleStore.loading" class="role-switch-status">正在加载角色…</div>
                      <button
                        v-for="role in sidebarRoles"
                        v-else
                        :key="role.id"
                        class="role-switch-item"
                        :class="{ active: roleStore.currentRole?.id === role.id }"
                        type="button"
                        role="menuitemradio"
                        :aria-checked="roleStore.currentRole?.id === role.id"
                        @click.stop="selectSidebarRole(role)"
                      >
                        <el-icon><User /></el-icon>
                        <span>{{ role.name }}</span>
                        <el-icon v-if="roleStore.currentRole?.id === role.id" class="role-switch-check"><Check /></el-icon>
                      </button>
                      <div v-if="!roleStore.loading && !sidebarRoles.length" class="role-switch-status">暂无可用角色</div>
                    </div>
                  </div>
                  <button
                    :class="{ active: workspaceMode === 'chat' }"
                    type="button"
                    role="tab"
                    :aria-selected="workspaceMode === 'chat'"
                    @click="selectWorkspaceMode('chat')"
                  >Chat</button>
                </div>
                <button class="chat-panel-close" type="button" aria-label="关闭聊天面板" title="关闭聊天面板" @click="closeChatPanel">
                  <el-icon><Close /></el-icon>
                </button>
              </div>

              <div class="chat-panel-content">
                <button class="chat-submenu-action new-chat-action" type="button" @click="startNewChat">
                  <el-icon><EditPen /></el-icon>
                  <span>新建对话</span>
                </button>

                <div class="chat-submenu-section-head">
                  <span>对话项目</span>
                  <span v-if="recentConversations.length" class="chat-project-count">{{ recentConversations.length }}</span>
                </div>

                <div v-if="conversationListLoading" class="chat-submenu-loading">正在加载…</div>
                <div v-else-if="recentConversations.length" class="chat-project-list">
                  <button
                    v-for="conversation in recentConversations"
                    :key="conversation.id"
                    class="chat-project-item"
                    :class="{ active: route.query.contextId === (conversation.contextId || conversation.id) }"
                    type="button"
                    :title="conversation.title || '未命名对话'"
                    @click="openConversation(conversation)"
                  >
                    <el-icon><ChatLineRound /></el-icon>
                    <span>{{ conversation.title || '未命名对话' }}</span>
                  </button>
                </div>
                <div v-else class="chat-submenu-empty">暂无历史对话</div>

                <button class="chat-submenu-action history-action" type="button" @click="router.push('/history')">
                  <el-icon><Clock /></el-icon>
                  <span>查看全部聊天历史</span>
                </button>
              </div>
              <div
                class="chat-panel-resizer"
                role="separator"
                aria-label="调整聊天子栏宽度"
                aria-orientation="vertical"
                :aria-valuemin="CHAT_PANEL_MIN_WIDTH"
                :aria-valuemax="CHAT_PANEL_MAX_WIDTH"
                :aria-valuenow="chatPanelWidth"
                tabindex="0"
                title="拖动调整宽度，双击恢复默认"
                @pointerdown="startChatPanelResize"
                @keydown="handleChatPanelResizeKeydown"
                @dblclick="resetChatPanelWidth"
              ></div>
            </section>
          </Transition>

          <div
            v-if="!sidebarCollapsed && !chatNavOpen"
            class="sidebar-resizer"
            role="separator"
            aria-label="调整侧边栏宽度"
            aria-orientation="vertical"
            :aria-valuemin="SIDEBAR_MIN_WIDTH"
            :aria-valuemax="SIDEBAR_MAX_WIDTH"
            :aria-valuenow="sidebarWidth"
            tabindex="0"
            title="拖动调整宽度，双击恢复默认"
            @pointerdown="startSidebarResize"
            @keydown="handleSidebarResizeKeydown"
            @dblclick="resetSidebarWidth"
          ></div>
        </el-aside>

        <button
          v-if="usesDrawerNavigation"
          class="simple-nav-toggle"
          type="button"
          aria-label="展开导航"
          @click="simpleNavOpen = true"
        >
          <el-icon><MenuIcon /></el-icon>
        </button>

        <el-drawer
          v-if="usesDrawerNavigation"
          v-model="simpleNavOpen"
          direction="ltr"
          :size="248"
          :with-header="false"
          class="simple-nav-drawer"
        >
          <div class="drawer-sidebar">
            <div class="sidebar-header drawer-header" @click="router.push('/chat'); simpleNavOpen = false">
              <div class="logo-icon">
                <el-icon><Connection /></el-icon>
              </div>
              <span class="logo-text">知弈</span>
            </div>

            <el-menu
              :default-active="activeMenu"
              router
              class="sidebar-menu drawer-menu"
              @select="simpleNavOpen = false"
            >
              <div class="menu-group-title">{{ $t('nav.main') }}</div>
              <el-menu-item index="/chat">
                <el-icon><ChatDotRound /></el-icon>
                <span>{{ $t('nav.chat') }}</span>
              </el-menu-item>
              <el-menu-item index="/agentos/legal/contract-review">
                <el-icon><DocumentChecked /></el-icon>
                <span>角色工作台</span>
              </el-menu-item>

              <el-menu-item index="/agentos/acg">
                <el-icon><Cpu /></el-icon>
                <span>ACG 动态群体智能引擎</span>
              </el-menu-item>

              <div class="menu-group-title">{{ $t('nav.knowledge') }}</div>
              <el-menu-item index="/rag">
                <el-icon><Search /></el-icon>
                <span>{{ $t('nav.rag') }}</span>
              </el-menu-item>
              <el-menu-item index="/history">
                <el-icon><Clock /></el-icon>
                <span>{{ $t('nav.history') }}</span>
              </el-menu-item>

              <div class="menu-group-title">{{ $t('nav.system') }}</div>
              <el-menu-item index="/agentos-console">
                <el-icon><Monitor /></el-icon>
                <span>AgentOS 运维</span>
              </el-menu-item>
              <el-menu-item index="/roles">
                <el-icon><User /></el-icon>
                <span>{{ $t('nav.roles') }}</span>
              </el-menu-item>
              <el-menu-item index="/federated-learning">
                <el-icon><Connection /></el-icon>
                <span>联邦管理</span>
              </el-menu-item>
              <el-menu-item index="/federated-models">
                <el-icon><Cpu /></el-icon>
                <span>模型管理</span>
              </el-menu-item>
              <el-menu-item index="/settings">
                <el-icon><Setting /></el-icon>
                <span>{{ $t('nav.settings') }}</span>
              </el-menu-item>
            </el-menu>

            <div class="sidebar-footer drawer-footer">
              <div class="user-profile" @click="router.push('/user'); simpleNavOpen = false">
                <el-avatar :size="32" class="user-avatar">U</el-avatar>
                <div class="user-info">
                  <span class="user-name">User</span>
                  <span class="user-status">Online</span>
                </div>
              </div>
              <el-button
                class="logout-btn"
                type="danger"
                size="small"
                @click="handleLogout"
                :icon="SwitchButton"
              >
                退出登录
              </el-button>
            </div>
          </div>
        </el-drawer>

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

          <el-main class="app-main" :class="{ 'route-scrollable': isRouteScrollable }">
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
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  ArrowDown, ArrowRight, ChatDotRound, ChatLineRound, Check, EditPen, User, Search,
  Clock, Setting, SwitchButton, Connection,
  Monitor, DocumentChecked, Cpu,
  Menu as MenuIcon, Fold, Expand, Close
} from '@element-plus/icons-vue'
import ErrorBoundary from '@/components/ErrorBoundary.vue'
import { authApi } from '@/services/api/auth'
import { conversationApi, type Conversation } from '@/services/api/conversation'
import { useChatStore } from '@/stores/chat'
import { useRoleStore } from '@/stores/role'
import type { Role } from '@/services/api/role'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()
const roleStore = useRoleStore()
const sidebarRoles = computed(() => roleStore.roles)
const globalError = ref('')
const simpleNavOpen = ref(false)
type WorkspaceMode = 'agent' | 'chat'
const WORKSPACE_MODE_KEY = 'layout.workspace_mode'
const workspaceMode = ref<WorkspaceMode>(localStorage.getItem(WORKSPACE_MODE_KEY) === 'agent' ? 'agent' : 'chat')
const CHAT_NAV_OPEN_KEY = 'layout.chat_nav_open'
const chatNavOpen = ref(route.path.startsWith('/chat') && localStorage.getItem(CHAT_NAV_OPEN_KEY) === '1')
const CHAT_PANEL_WIDTH_KEY = 'layout.chat_panel_width'
const CHAT_PANEL_DEFAULT_WIDTH = 300
const CHAT_PANEL_MIN_WIDTH = 220
const CHAT_PANEL_MAX_WIDTH = 420
const storedChatPanelWidth = Number(localStorage.getItem(CHAT_PANEL_WIDTH_KEY))
const chatPanelWidth = ref(
  Number.isFinite(storedChatPanelWidth) && storedChatPanelWidth >= CHAT_PANEL_MIN_WIDTH && storedChatPanelWidth <= CHAT_PANEL_MAX_WIDTH
    ? storedChatPanelWidth
    : CHAT_PANEL_DEFAULT_WIDTH
)
const chatPanelResizing = ref(false)
const recentConversations = ref<Conversation[]>([])
const conversationListLoading = ref(false)
const SIDEBAR_COLLAPSED_KEY = 'layout.sidebar_collapsed'
const SIDEBAR_WIDTH_KEY = 'layout.sidebar_width'
const SIDEBAR_DEFAULT_WIDTH = 248
const SIDEBAR_MIN_WIDTH = 220
const SIDEBAR_MAX_WIDTH = 360
const sidebarCollapsed = ref(localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === '1')
const storedSidebarWidth = Number(localStorage.getItem(SIDEBAR_WIDTH_KEY))
const sidebarWidth = ref(
  Number.isFinite(storedSidebarWidth) && storedSidebarWidth >= SIDEBAR_MIN_WIDTH && storedSidebarWidth <= SIDEBAR_MAX_WIDTH
    ? storedSidebarWidth
    : SIDEBAR_DEFAULT_WIDTH
)
const sidebarResizing = ref(false)
const mainSidebarCompact = computed(() => sidebarCollapsed.value || chatNavOpen.value)
const sidebarAsideWidth = computed(() => `${chatNavOpen.value ? 60 + chatPanelWidth.value : (sidebarCollapsed.value ? 60 : sidebarWidth.value)}px`)
const primarySidebarWidth = computed(() => `${mainSidebarCompact.value ? 60 : sidebarWidth.value}px`)
let sidebarResizeStartX = 0
let sidebarResizeStartWidth = SIDEBAR_DEFAULT_WIDTH
let chatPanelResizeStartX = 0
let chatPanelResizeStartWidth = CHAT_PANEL_DEFAULT_WIDTH
const mobileMediaQuery = window.matchMedia('(max-width: 760px)')
const isMobileViewport = ref(mobileMediaQuery.matches)

// Sidebar navigation state

// Sidebar scroll container reference
const sidebarNav = ref<HTMLElement | null>(null)

// Handle mouse-wheel scrolling inside sidebar
const handleSidebarWheel = (event: WheelEvent) => {
  if (!sidebarNav.value) return
  
  // Prevent page-level scrolling when pointer is on sidebar
  event.preventDefault()
  
  // Slow down scroll speed for smoother navigation
  const scrollAmount = event.deltaY * 0.5
  
  // Scroll only the sidebar container
  sidebarNav.value.scrollBy({
    top: scrollAmount,
    behavior: 'smooth'
  })
}

const loadRecentConversations = async () => {
  if (conversationListLoading.value) return

  try {
    conversationListLoading.value = true
    const userId = localStorage.getItem('userId') || undefined
    const conversations = await conversationApi.getUserConversations(userId)
    recentConversations.value = [...conversations]
      .sort((a, b) => new Date(b.updatedAt || b.createdAt).getTime() - new Date(a.updatedAt || a.createdAt).getTime())
      .slice(0, 5)
  } catch {
    recentConversations.value = []
  } finally {
    conversationListLoading.value = false
  }
}

const handleChatNavToggle = () => {
  chatNavOpen.value = !chatNavOpen.value
  localStorage.setItem(CHAT_NAV_OPEN_KEY, chatNavOpen.value ? '1' : '0')
  if (chatNavOpen.value) void loadRecentConversations()
  if (!route.path.startsWith('/chat')) {
    void router.push({ path: '/chat', query: { workspace: workspaceMode.value } })
  }
}

const closeChatPanel = () => {
  chatNavOpen.value = false
  localStorage.setItem(CHAT_NAV_OPEN_KEY, '0')
}

const startNewChat = async () => {
  chatStore.clearMessages()
  await router.push({ path: '/chat', query: { workspace: workspaceMode.value } })
}

const openConversation = async (conversation: Conversation) => {
  const contextId = conversation.contextId || conversation.id
  await router.push({ path: '/chat', query: { contextId, workspace: workspaceMode.value } })
}

const handleHistoryRefresh = () => {
  if (chatNavOpen.value) void loadRecentConversations()
}

watch(
  () => route.path,
  path => {
    if (path.startsWith('/chat') || !chatNavOpen.value) return
    closeChatPanel()
  }
)

const selectWorkspaceMode = (mode: WorkspaceMode) => {
  workspaceMode.value = mode
  localStorage.setItem(WORKSPACE_MODE_KEY, mode)
  chatNavOpen.value = true
  localStorage.setItem(CHAT_NAV_OPEN_KEY, '1')
  window.dispatchEvent(new CustomEvent('workspace-mode-change', { detail: { mode } }))
  void router.replace({
    path: '/chat',
    query: { ...route.query, workspace: mode }
  })
}

const ensureSidebarRoles = () => {
  if (!roleStore.roles.length) void roleStore.loadRoles()
}

const selectSidebarRole = async (role: Role) => {
  await roleStore.setCurrentRole(role)
  selectWorkspaceMode('agent')
}

// Immersive mode: only keep login page immersive
const isImmersive = computed(() => {
  const path = route.path
  return path.startsWith('/login')
})

const usesDrawerNavigation = computed(() => {
  return !isImmersive.value && isMobileViewport.value
})

const toggleSidebar = () => {
  if (chatNavOpen.value) {
    closeChatPanel()
    return
  }
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem(SIDEBAR_COLLAPSED_KEY, sidebarCollapsed.value ? '1' : '0')
}

const clampSidebarWidth = (width: number) => {
  return Math.min(SIDEBAR_MAX_WIDTH, Math.max(SIDEBAR_MIN_WIDTH, Math.round(width)))
}

const persistSidebarWidth = () => {
  localStorage.setItem(SIDEBAR_WIDTH_KEY, String(sidebarWidth.value))
}

const handleSidebarResizeMove = (event: PointerEvent) => {
  if (!sidebarResizing.value) return
  sidebarWidth.value = clampSidebarWidth(sidebarResizeStartWidth + event.clientX - sidebarResizeStartX)
}

const stopSidebarResize = () => {
  if (!sidebarResizing.value) return
  sidebarResizing.value = false
  persistSidebarWidth()
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  window.removeEventListener('pointermove', handleSidebarResizeMove)
  window.removeEventListener('pointerup', stopSidebarResize)
  window.removeEventListener('pointercancel', stopSidebarResize)
}

const startSidebarResize = (event: PointerEvent) => {
  if (event.button !== 0) return
  event.preventDefault()
  sidebarResizeStartX = event.clientX
  sidebarResizeStartWidth = sidebarWidth.value
  sidebarResizing.value = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  window.addEventListener('pointermove', handleSidebarResizeMove)
  window.addEventListener('pointerup', stopSidebarResize)
  window.addEventListener('pointercancel', stopSidebarResize)
}

const resetSidebarWidth = () => {
  sidebarWidth.value = SIDEBAR_DEFAULT_WIDTH
  persistSidebarWidth()
}

const handleSidebarResizeKeydown = (event: KeyboardEvent) => {
  const increments: Record<string, number> = {
    ArrowLeft: -8,
    ArrowRight: 8
  }

  if (event.key === 'Home') {
    sidebarWidth.value = SIDEBAR_MIN_WIDTH
  } else if (event.key === 'End') {
    sidebarWidth.value = SIDEBAR_MAX_WIDTH
  } else if (increments[event.key]) {
    sidebarWidth.value = clampSidebarWidth(sidebarWidth.value + increments[event.key])
  } else {
    return
  }

  event.preventDefault()
  persistSidebarWidth()
}

const clampChatPanelWidth = (width: number) => {
  return Math.min(CHAT_PANEL_MAX_WIDTH, Math.max(CHAT_PANEL_MIN_WIDTH, Math.round(width)))
}

const persistChatPanelWidth = () => {
  localStorage.setItem(CHAT_PANEL_WIDTH_KEY, String(chatPanelWidth.value))
}

const handleChatPanelResizeMove = (event: PointerEvent) => {
  if (!chatPanelResizing.value) return
  chatPanelWidth.value = clampChatPanelWidth(chatPanelResizeStartWidth + event.clientX - chatPanelResizeStartX)
}

const stopChatPanelResize = () => {
  if (!chatPanelResizing.value) return
  chatPanelResizing.value = false
  persistChatPanelWidth()
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  window.removeEventListener('pointermove', handleChatPanelResizeMove)
  window.removeEventListener('pointerup', stopChatPanelResize)
  window.removeEventListener('pointercancel', stopChatPanelResize)
}

const startChatPanelResize = (event: PointerEvent) => {
  if (event.button !== 0) return
  event.preventDefault()
  chatPanelResizeStartX = event.clientX
  chatPanelResizeStartWidth = chatPanelWidth.value
  chatPanelResizing.value = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  window.addEventListener('pointermove', handleChatPanelResizeMove)
  window.addEventListener('pointerup', stopChatPanelResize)
  window.addEventListener('pointercancel', stopChatPanelResize)
}

const resetChatPanelWidth = () => {
  chatPanelWidth.value = CHAT_PANEL_DEFAULT_WIDTH
  persistChatPanelWidth()
}

const handleChatPanelResizeKeydown = (event: KeyboardEvent) => {
  const step = event.shiftKey ? 24 : 8

  if (event.key === 'Home') {
    chatPanelWidth.value = CHAT_PANEL_MIN_WIDTH
  } else if (event.key === 'End') {
    chatPanelWidth.value = CHAT_PANEL_MAX_WIDTH
  } else if (event.key === 'ArrowLeft') {
    chatPanelWidth.value = clampChatPanelWidth(chatPanelWidth.value - step)
  } else if (event.key === 'ArrowRight') {
    chatPanelWidth.value = clampChatPanelWidth(chatPanelWidth.value + step)
  } else {
    return
  }

  event.preventDefault()
  persistChatPanelWidth()
}

const handleViewportChange = (event: MediaQueryListEvent) => {
  isMobileViewport.value = event.matches
  if (!event.matches) simpleNavOpen.value = false
}

const isRouteScrollable = computed(() => {
  const path = route.path
  return (
    path.startsWith('/federated-learning') ||
    path.startsWith('/federated-models') ||
    path.startsWith('/agentos-console') ||
    path.startsWith('/agentos/legal/contract-review') ||
    path.startsWith('/agentos/acg') ||
    path.startsWith('/rag') ||
    path.startsWith('/voice-chat')
  )
})

const activeMenu = computed(() => {
  const path = route.path
  if (path === '/chat' || path.startsWith('/chat')) return '/chat'
  if (path.startsWith('/agentos-console')) return '/agentos-console'
  if (path.startsWith('/agentos/legal/contract-review')) return '/agentos/legal/contract-review'
  if (path.startsWith('/agentos/acg')) return '/agentos/acg'
  if (path === '/roles' || path.startsWith('/roles')) return '/roles'
  if (path === '/rag' || path.startsWith('/rag')) return '/rag'
  if (path === '/settings' || path.startsWith('/settings')) return '/settings'
  if (path.startsWith('/history')) return '/history'
  if (path.startsWith('/federated-models')) return '/federated-models'
  if (path.startsWith('/federated-learning')) return '/federated-learning'
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

// Logout with confirmation dialog
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要退出登录吗？退出后将需要重新登录。',
      '确认退出',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        customClass: 'logout-confirm'
      }
    )

    const result = await authApi.logout()
    if (result.success) {
      ElMessage.success(result.message || '退出登录成功')
      router.push('/login')
    } else {
      ElMessage.error(result.message || '退出登录失败')
    }
  } catch (error) {
    if (error === 'cancel') return
    console.error('退出登录失败:', error)
    ElMessage.error('退出登录失败，请重试')
  }
}

onMounted(() => {
  window.addEventListener('global-error', handleGlobalError as EventListener)
  window.addEventListener('history-refresh', handleHistoryRefresh)
  mobileMediaQuery.addEventListener('change', handleViewportChange)
  if (chatNavOpen.value) void loadRecentConversations()
})

onUnmounted(() => {
  stopSidebarResize()
  stopChatPanelResize()
  window.removeEventListener('global-error', handleGlobalError as EventListener)
  window.removeEventListener('history-refresh', handleHistoryRefresh)
  mobileMediaQuery.removeEventListener('change', handleViewportChange)
})
</script>

<style scoped>
.app-layout {
  height: 100%;
  width: 100%;
  background: var(--app-layout-bg);
  overflow: hidden;
  display: flex;
}

/* Sidebar Styles */
.app-sidebar {
  position: relative;
  background-color: transparent;
  border-right: 1px solid var(--border-light);
  backdrop-filter: blur(18px);
  display: flex;
  flex-direction: row;
  overflow: hidden;
  transition: width 0.22s var(--ease-out);
}

.primary-sidebar {
  position: relative;
  z-index: 2;
  flex: 0 0 auto;
  height: 100%;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--sidebar-bg);
  transition: width 0.22s var(--ease-out);
}

.app-sidebar.chat-panel-open .primary-sidebar {
  border-right: 1px solid var(--sidebar-border);
}

.app-sidebar.resizing {
  transition: none;
}

.app-sidebar.resizing .primary-sidebar {
  transition: none;
}

.sidebar-resizer {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 12;
  width: 8px;
  cursor: col-resize;
  touch-action: none;
  outline: none;
}

.sidebar-resizer::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 2px;
  background: var(--primary-color);
  opacity: 0;
  transform: scaleY(0.96);
  transition: opacity 0.16s ease, transform 0.16s ease;
}

.sidebar-resizer:hover::after,
.sidebar-resizer:focus-visible::after,
.app-sidebar.resizing .sidebar-resizer::after {
  opacity: 0.8;
  transform: scaleY(1);
}

.sidebar-header {
  flex-shrink: 0;
  height: 54px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 10px;
  gap: 6px;
  border-bottom: 1px solid var(--sidebar-border);
}

.sidebar-brand,
.sidebar-collapse-btn {
  display: inline-flex;
  align-items: center;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  cursor: pointer;
}

.sidebar-brand {
  min-width: 0;
  gap: 10px;
  padding: 0;
}

.sidebar-collapse-btn {
  flex: 0 0 auto;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 9px;
  color: var(--text-secondary);
  font-size: 17px;
  transition: background-color 0.16s ease, color 0.16s ease;
}

.sidebar-collapse-btn:hover {
  background: var(--primary-fade);
  color: var(--primary-color);
}

.sidebar-brand:focus-visible,
.sidebar-collapse-btn:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}

.app-sidebar.collapsed .sidebar-header {
  justify-content: center;
  padding: 0;
}

.app-sidebar.collapsed .sidebar-brand {
  display: none;
}

.logo-icon {
  width: 34px;
  height: 34px;
  background: var(--primary-fade);
  border: none;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-color);
  font-weight: bold;
  font-size: 18px;
}

.logo-text {
  font-family: var(--font-serif);
  font-size: 19px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0;
}

.sidebar-nav {
  flex: 1;
  min-height: 0;
  padding: 18px 8px 12px;
  overflow-y: auto;
  overflow-x: hidden;
  scroll-behavior: smooth;
}

.app-sidebar.collapsed .sidebar-nav {
  padding: 8px 6px 10px;
}

.workspace-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 3px;
  margin: 0 4px 8px;
  padding: 3px;
  border: 1px solid var(--border-light);
  border-radius: 9px;
  background: var(--bg-input);
}

.workspace-switch-btn {
  width: 100%;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 0 9px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: var(--text-secondary);
  font: inherit;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.16s ease, color 0.16s ease, box-shadow 0.16s ease;
}

.workspace-switch-btn:hover {
  color: var(--text-primary);
}

.workspace-switch-btn.active {
  background: var(--bg-card);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
}

.workspace-switch-btn:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: -2px;
}

.workspace-switch-btn .el-icon {
  font-size: 12px;
}

.agent-switch-entry {
  position: relative;
  min-width: 0;
}

.agent-hover-menu {
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 30;
  width: 142px;
  padding-top: 6px;
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transform: translateY(-4px) scale(0.98);
  transform-origin: top left;
  transition: opacity 0.14s ease, transform 0.16s var(--ease-out), visibility 0s linear 0.16s;
}

.agent-hover-menu.role-switch-menu {
  width: 176px;
  padding: 6px;
  border: 1px solid var(--border-light);
  border-radius: 10px;
  background: var(--bg-card);
  box-shadow: var(--shadow-md);
}

.agent-switch-entry:hover .agent-hover-menu,
.agent-switch-entry:focus-within .agent-hover-menu {
  opacity: 1;
  visibility: visible;
  pointer-events: auto;
  transform: translateY(0) scale(1);
  transition-delay: 0s;
}

.agent-hover-menu > button {
  width: 100%;
  height: 34px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 10px;
  border: 1px solid var(--border-light);
  border-radius: 9px;
  background: var(--bg-card);
  box-shadow: var(--shadow-md);
  color: var(--text-secondary);
  font: inherit;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: color 0.16s ease, background-color 0.16s ease;
}

.agent-hover-menu.role-switch-menu > button {
  height: 32px;
  padding: 0 8px;
  border: 0;
  border-radius: 7px;
  box-shadow: none;
  background: transparent;
  font-weight: 500;
}

.agent-hover-menu.role-switch-menu > button.active {
  color: var(--primary-color);
  background: var(--primary-fade);
}

.role-switch-item span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.role-switch-check {
  flex: 0 0 auto;
  margin-left: auto;
  color: var(--primary-color);
}

.role-switch-status {
  padding: 8px;
  color: var(--text-disabled);
  font-size: 11px;
  text-align: center;
}

.agent-hover-menu > button:hover {
  color: var(--primary-color);
  background: var(--bg-panel);
}

.agent-hover-menu > button:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: -2px;
}

.agent-hover-arrow {
  margin-left: auto;
  color: var(--text-disabled);
  font-size: 11px;
}

.chat-side-panel {
  position: relative;
  z-index: 1;
  flex: 0 0 auto;
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--sidebar-bg);
  box-shadow: 10px 0 24px rgba(16, 18, 33, 0.04);
}

.chat-panel-resizer {
  position: absolute;
  z-index: 4;
  top: 0;
  right: -3px;
  bottom: 0;
  width: 7px;
  cursor: col-resize;
  touch-action: none;
  outline: none;
}

.chat-panel-resizer::after {
  content: '';
  position: absolute;
  top: 0;
  right: 3px;
  bottom: 0;
  width: 1px;
  background: transparent;
  transition: background-color 0.16s ease, box-shadow 0.16s ease;
}

.chat-panel-resizer:hover::after,
.chat-panel-resizer:focus-visible::after,
.app-sidebar.resizing .chat-panel-resizer::after {
  background: var(--primary-color);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--primary-color) 18%, transparent);
}

.chat-panel-header {
  flex: 0 0 54px;
  min-width: 160px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 8px;
  border-bottom: 1px solid var(--sidebar-border);
}

.chat-panel-switch {
  min-width: 0;
  flex: 1;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 2px;
  padding: 3px;
  border: 1px solid var(--border-light);
  border-radius: 9px;
  background: var(--bg-input);
}

.chat-panel-switch > button,
.chat-panel-switch > .agent-switch-entry > button {
  width: 100%;
  height: 27px;
  padding: 0 6px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  font: inherit;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.16s ease, background-color 0.16s ease, box-shadow 0.16s ease;
}

.chat-panel-switch > button:hover,
.chat-panel-switch > .agent-switch-entry > button:hover {
  color: var(--text-primary);
}

.chat-panel-switch > button.active,
.chat-panel-switch > .agent-switch-entry > button.active {
  color: var(--text-primary);
  background: var(--bg-card);
  box-shadow: var(--shadow-sm);
}

.chat-panel-switch > button:focus-visible,
.chat-panel-switch > .agent-switch-entry > button:focus-visible,
.chat-panel-close:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: -2px;
}

.chat-panel-close {
  flex: 0 0 28px;
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: var(--text-disabled);
  cursor: pointer;
  transition: color 0.16s ease, background-color 0.16s ease;
}

.chat-panel-close:hover {
  color: var(--text-primary);
  background: var(--bg-panel);
}

.chat-panel-content {
  min-width: 160px;
  flex: 1;
  min-height: 0;
  padding: 10px 8px 16px;
  overflow: auto;
}

.chat-panel-enter-active {
  transition: opacity 0.18s ease 0.04s, transform 0.22s var(--ease-out);
}

.chat-panel-leave-active {
  transition: opacity 0.14s ease, transform 0.18s ease;
}

.chat-panel-enter-from,
.chat-panel-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}

.chat-panel-enter-to,
.chat-panel-leave-from {
  opacity: 1;
  transform: translateX(0);
}

/* Sidebar menu scrolling */
.sidebar-nav::-webkit-scrollbar {
  width: 4px;
}

.sidebar-nav::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-nav::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb);
  border-radius: 999px;
}

.sidebar-nav::-webkit-scrollbar-thumb:hover {
  background: var(--scrollbar-thumb-hover);
}

.menu-group-title {
  padding: 14px 16px 6px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-disabled);
  letter-spacing: 0;
  text-transform: none;
}

.sidebar-menu {
  --el-menu-item-font-size: 13px;
  border: none;
  background: transparent;
}

.sidebar-menu.el-menu--collapse {
  width: 100%;
}

.chat-nav-group {
  position: relative;
  margin-bottom: 2px;
}

.chat-nav-trigger,
.chat-submenu-action,
.chat-project-item {
  width: 100%;
  border: 0;
  background: transparent;
  color: var(--text-secondary);
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.chat-nav-trigger {
  position: relative;
  height: 44px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 14px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 450;
  letter-spacing: -0.01em;
  transition: var(--transition);
}

.chat-nav-trigger > .el-icon:first-child {
  flex: 0 0 auto;
  font-size: 18px;
}

.chat-nav-label {
  min-width: 0;
  flex: 1;
}

.chat-nav-chevron {
  flex: 0 0 auto;
  margin-left: auto;
  font-size: 13px;
  color: var(--text-disabled);
}

.chat-nav-trigger:hover {
  background: var(--primary-fade);
  color: var(--text-primary);
}

.chat-nav-group.active > .chat-nav-trigger {
  background: var(--primary-fade);
  color: var(--primary-color);
  font-weight: 500;
}

.chat-nav-group.active > .chat-nav-trigger::before {
  content: '';
  position: absolute;
  top: 6px;
  bottom: 6px;
  left: 0;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--primary-color);
}

.app-sidebar.collapsed .chat-nav-trigger {
  justify-content: center;
  padding: 0;
}

.chat-submenu-action,
.chat-project-item {
  min-height: 32px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 9px;
  border-radius: 7px;
  font-size: 12px;
  transition: background-color 0.16s ease, color 0.16s ease;
}

.chat-submenu-action:hover,
.chat-project-item:hover,
.chat-project-item.active {
  background: var(--bg-panel);
  color: var(--text-primary);
}

.chat-nav-trigger:focus-visible,
.chat-submenu-action:focus-visible,
.chat-project-item:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: -2px;
}

.new-chat-action {
  min-height: 38px;
  margin-bottom: 8px;
  padding: 0 10px;
  border: 1px solid var(--border-light);
  background: color-mix(in srgb, var(--bg-card) 84%, transparent);
  color: var(--text-primary);
  font-weight: 650;
  box-shadow: var(--shadow-sm);
}

.new-chat-action:hover {
  border-color: var(--primary-line);
  background: var(--bg-card);
  color: var(--primary-color);
}

.chat-submenu-section-head {
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 5px 8px 6px;
  color: var(--text-disabled);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.035em;
}

.chat-project-count {
  min-width: 16px;
  height: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  border-radius: 999px;
  background: var(--bg-panel);
  color: var(--text-disabled);
  font-size: 10px;
}

.chat-project-item .el-icon,
.chat-submenu-action .el-icon {
  flex: 0 0 auto;
  font-size: 13px;
}

.chat-project-list {
  position: relative;
  display: grid;
  gap: 2px;
  padding: 2px 0 4px 6px;
}

.chat-project-list::before {
  content: '';
  position: absolute;
  top: 7px;
  bottom: 9px;
  left: 1px;
  width: 1px;
  background: var(--border-light);
}

.chat-project-item {
  position: relative;
  min-height: 34px;
  padding: 6px 8px;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 450;
}

.chat-project-item::before {
  content: '';
  position: absolute;
  top: 50%;
  left: -6px;
  width: 5px;
  height: 5px;
  border: 1px solid var(--border-light);
  border-radius: 50%;
  background: var(--bg-card);
  transform: translate(-50%, -50%);
}

.chat-project-item span,
.chat-submenu-action span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-project-item.active {
  color: var(--primary-color);
  background: var(--primary-fade);
  font-size: 13px;
  font-weight: 650;
}

.chat-project-item.active::before {
  width: 7px;
  height: 7px;
  border-color: var(--primary-color);
  background: var(--primary-color);
  box-shadow: 0 0 0 3px var(--primary-fade);
}

.chat-submenu-loading,
.chat-submenu-empty {
  padding: 8px 9px;
  color: var(--text-disabled);
  font-size: 11px;
}

.history-action {
  min-height: 36px;
  margin-top: 7px;
  padding: 8px 9px 4px;
  border-top: 1px solid var(--border-light);
  border-radius: 0;
  color: var(--text-muted);
  font-size: 11px;
}

.app-sidebar.collapsed .sidebar-menu :deep(.el-menu-item) {
  justify-content: center;
  height: 44px;
  padding: 0 !important;
}

.app-sidebar.collapsed .sidebar-menu :deep(.el-menu-item .el-icon) {
  margin: 0;
  font-size: 18px;
}

/* 覆盖 Element Plus 默认激活态：去掉右侧指示条，改左侧橙色条 */
.sidebar-menu :deep(.el-menu-item) {
  height: 44px;
  margin: 0 0 2px;
  padding: 0 14px !important;
  gap: 10px;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 450;
  letter-spacing: -0.01em;
  transition: var(--transition);
  position: relative;
}

.sidebar-menu :deep(.el-menu-item .el-icon) {
  flex: 0 0 18px;
  width: 18px;
  margin-right: 0;
  font-size: 18px;
}

.sidebar-menu :deep(.el-menu-item > span) {
  font-size: 13px !important;
  line-height: 1.35;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background-color: rgba(217, 119, 87, 0.06);
  color: var(--text-primary);
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background-color: rgba(217, 119, 87, 0.08);
  color: var(--primary-color);
  font-weight: 500;
}

.sidebar-menu :deep(.el-menu-item.is-active::before) {
  content: '';
  position: absolute;
  left: 0;
  top: 6px;
  bottom: 6px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--primary-color);
}

.sidebar-digital-human {
  padding: 16px;
  border-top: 1px solid var(--border-light);
  border-bottom: 1px solid var(--border-light);
  height: 320px; /* Keep a stable user card height */
  min-height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.02);
  overflow: hidden; /* Prevent overflow artifacts */
}

.sidebar-digital-human :deep(.digital-human-container) {
  width: 100%;
  height: 100%;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar-digital-human :deep(.digital-human-canvas) {
  width: 100% !important;
  height: 100% !important;
  display: block;
}

.sidebar-footer {
  flex-shrink: 0;
  padding: 14px;
  margin-top: auto;
  border-top: 1px solid var(--sidebar-border);
}

.app-sidebar.collapsed .sidebar-footer {
  padding: 8px 6px;
}

.app-sidebar.collapsed .user-profile {
  justify-content: center;
  gap: 0;
  padding: 8px 0;
}

@media (prefers-reduced-motion: reduce) {
  .app-sidebar,
  .primary-sidebar,
  .chat-side-panel {
    transition-duration: 0.01ms !important;
  }
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: var(--radius-md);
  cursor: pointer;
  border: 1px solid transparent;
  transition: var(--transition);
}

.user-profile:hover {
  background-color: var(--bg-card);
  border-color: var(--border-light);
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

/* Footer layout */
.logout-section {
  margin-top: 10px;
  padding: 0;
}

.logout-btn {
  width: 100%;
  background: var(--bg-card) !important;
  border: 1px solid rgba(178, 74, 74, 0.22) !important;
  border-radius: 8px;
  color: var(--danger) !important;
  font-weight: 500;
  transition: var(--transition);
  box-shadow: none;
}

.logout-btn:hover {
  background: rgba(178, 74, 74, 0.08) !important;
  transform: translateY(-1px);
  box-shadow: none;
}

.logout-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(239, 68, 68, 0.3);
}

.logout-btn:deep(.el-icon) {
  font-size: 14px;
}

.simple-nav-toggle {
  position: fixed;
  top: 9px;
  left: 12px;
  z-index: 2100;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 36px;
  padding: 0;
  border: 1px solid var(--primary-line);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  color: var(--primary-color);
  font: inherit;
  font-size: 15px;
  font-weight: 650;
  cursor: pointer;
  box-shadow: 0 10px 22px rgba(24, 39, 35, 0.08);
  backdrop-filter: blur(14px);
  transition: border-color 0.18s ease, background-color 0.18s ease, transform 0.18s ease;
}

.simple-nav-toggle:hover {
  border-color: var(--border-focus);
  background: #fff;
  transform: translateY(-1px);
}

.simple-nav-toggle:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}

.simple-nav-drawer :deep(.el-drawer__body),
:global(.simple-nav-drawer .el-drawer__body) {
  padding: 0;
  background: var(--drawer-bg);
}

.drawer-sidebar {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--app-layout-bg);
}

.drawer-header {
  flex-shrink: 0;
}

.drawer-menu {
  flex: 1;
  min-height: 0;
  padding: 14px 8px 10px;
  overflow-y: auto;
}

.drawer-menu::-webkit-scrollbar {
  width: 4px;
}

.drawer-menu::-webkit-scrollbar-track {
  background: transparent;
}

.drawer-menu::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb);
  border-radius: 999px;
}

.drawer-footer {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* Main Content Styles */
.main-container {
  flex: 1;
  min-width: 0;
  background-color: transparent;
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.app-main {
  flex: 1;
  min-height: 0;
  padding: 0;
  overflow: hidden;
  width: 100%;
  position: relative;
}

.app-main.route-scrollable {
  overflow-y: auto;
  overflow-x: hidden;
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
  transition: opacity 0.18s var(--ease-out), transform 0.18s var(--ease-out);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

/* Immersive Mode Overrides */
.immersive-mode .main-container {
  background-color: #0f1115;
}

.immersive-mode .app-main {
  overflow-y: auto;
}

/* Responsive optimization */
.app-main::-webkit-scrollbar {
  width: 6px;
}

.app-main::-webkit-scrollbar-track {
  background: transparent;
}

.app-main::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.1);
  border-radius: 10px;
}

.app-main::-webkit-scrollbar-thumb:hover {
  background: rgba(99, 102, 241, 0.2);
}

@media (max-width: 620px) {
  .simple-nav-toggle {
    top: 9px;
    left: 10px;
    width: 34px;
  }
}
</style>
