<template>
  <div class="chat-view-container">
    <!-- Background Elements for Atmosphere -->
    <div class="ambient-glow top-left"></div>
    <div class="ambient-glow bottom-right"></div>

    <!-- Main Chat Content -->
    <main class="chat-stage">
      
      <!-- Top Right: Header Actions (Role & Settings) -->
      <div class="header-actions">
        <el-tooltip :content="t('role.title')" placement="bottom" effect="light">
          <div class="action-btn glass-btn" @click="showRoleDrawer = true">
             <el-avatar :size="32" :src="currentRole?.avatar" class="current-role-avatar">
               {{ currentRole?.name?.charAt(0) }}
             </el-avatar>
             <span class="role-name-label">{{ currentRole?.name || t('role.title') }}</span>
             <el-icon class="icon-right"><ArrowDown /></el-icon>
          </div>
        </el-tooltip>
        
        <el-tooltip :content="t('settings.title')" placement="bottom" effect="light">
          <div class="action-btn glass-btn icon-only">
             <el-icon><MoreFilled /></el-icon>
          </div>
        </el-tooltip>
      </div>

      <!-- Chat Messages Scroll Area -->
      <div class="messages-container" ref="messagesRef">
        <div v-if="chatStore.messages.length === 0" class="empty-state">
           <div class="hero-content">
             <div class="logo-mark">Kinlin AI</div>
             <h1 class="welcome-text">{{ $t('chat.noMessages') }}</h1>
             <p class="subtitle">{{ $t('chat.newChat') }}</p>
           </div>
        </div>

        <div v-else class="message-list">
          <div 
            v-for="msg in chatStore.messages" 
            :key="msg.id" 
            class="message-row"
            :class="msg.role"
          >
             <div class="message-content-wrapper">
                <MessageBubble 
                  :message="{
                    id: msg.id,
                    role: msg.role,
                    content: msg.content || '',
                    createdAt: msg.createdAt || (msg.timestamp ? new Date(msg.timestamp) : new Date()),
                    confidence: msg.confidence,
                    fileUrl: msg.fileUrl,
                    tokensUsed: msg.tokensUsed,
                    sources: msg.sources,
                    reasoningPath: msg.reasoningPath,
                    modelInfo: msg.modelInfo
                  }"
                />
             </div>
          </div>
        </div>
      </div>

      <!-- Bottom: Input Area (Floating) -->
      <div class="input-dock-wrapper">
        <!-- Quick Reply Templates -->
        <div v-if="currentTemplates.length > 0" class="templates-container">
          <div 
            v-for="template in currentTemplates" 
            :key="template"
            class="template-tag"
            @click="useTemplate(template)"
          >
            {{ template }}
          </div>
        </div>

        <!-- Recommendations -->
        <div v-if="recommendations.length > 0" class="recommendations-container">
          <div class="recommendations-label">💡 推荐问题</div>
          <div 
            v-for="rec in recommendations" 
            :key="rec"
            class="recommendation-tag"
            @click="useRecommendation(rec)"
          >
            {{ rec }}
          </div>
        </div>

        <div class="input-dock glass-panel">
          <!-- Textarea -->
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="1"
            :autosize="{ minRows: 1, maxRows: 6 }"
            resize="none"
            :placeholder="$t('chat.placeholder')"
            class="dock-input"
            @keydown.enter.prevent="sendMessage"
          />

          <!-- Dock Footer -->
          <div class="dock-footer">
             <div class="footer-left">
                <el-popover
                  placement="top-start"
                  :width="200"
                  trigger="click"
                  popper-class="tools-popover"
                >
                  <template #reference>
                    <div class="plus-trigger">
                      <el-icon><CirclePlus /></el-icon>
                    </div>
                  </template>
                  <div class="tools-grid">
                    <div class="tool-item" @click="isRecording ? stopVoiceInput() : startVoiceInput()">
                      <el-icon :class="{ 'is-recording': isRecording }"><Microphone /></el-icon>
                      <span>{{ isRecording ? $t('voice.stopRecording') : $t('voice.startRecording') }}</span>
                    </div>
                    <div class="tool-item" @click="handleControl('folder')">
                      <el-icon><Folder /></el-icon>
                      <span>{{ $t('rag.upload') }}</span>
                    </div>
                    <div class="tool-item" @click="handleControl('image')">
                      <el-icon><Picture /></el-icon>
                      <span>{{ $t('common.search') }}</span>
                    </div>
                  </div>
                </el-popover>
                
                <div class="word-count" :class="{ 'warning': inputText.length > 500 }">
                  {{ $t('chat.wordCount', { count: inputText.length }) }}
                  <span v-if="inputText.length > 500" class="hint"> ({{ $t('chat.wordCountHint') }})</span>
                  <el-button 
                    v-if="inputText.length > 500" 
                    link 
                    type="primary" 
                    size="small" 
                    @click="autoSegment"
                    class="segment-btn"
                  >
                    自动分段
                  </el-button>
                </div>
             </div>

             <div class="footer-right">
                <div class="emotion-pill">
                  <span class="label">Emotion</span>
                  <input v-model="emotionTag" placeholder="Auto" class="transparent-input" />
                </div>
                <button class="send-trigger" @click="sendMessage" :disabled="loading || (!inputText.trim() && !isRecording)">
                   <el-icon v-if="!loading"><ArrowUp /></el-icon>
                   <el-icon v-else class="is-loading"><Loading /></el-icon>
                </button>
             </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Role Selection Drawer (Minimalist) -->
    <el-drawer
      v-model="showRoleDrawer"
      direction="rtl"
      :size="320"
      :with-header="false"
      class="role-drawer"
    >
      <div class="drawer-content">
         <div class="drawer-header">
           <h2>Choose a Persona</h2>
           <el-button circle text @click="showRoleDrawer = false"><el-icon><Close /></el-icon></el-button>
         </div>
         
         <div class="role-grid">
            <div 
              v-for="role in roles" 
              :key="role.id"
              class="role-card-minimal"
              :class="{ 'active': roleStore.currentRole?.id === role.id || selectedRoleId === role.id }"
              @click="selectRole(role)"
            >
               <el-avatar :size="48" :src="role.avatar" class="role-avatar-lg">
                  {{ role.name.charAt(0) }}
               </el-avatar>
               <div class="role-info">
                  <div class="name">{{ role.name }}</div>
                  <div class="desc">{{ role.tag || 'AI Assistant' }}</div>
               </div>
               <div class="check-mark" v-if="roleStore.currentRole?.id === role.id || selectedRoleId === role.id">
                 <el-icon><Check /></el-icon>
               </div>
            </div>
         </div>
      </div>
    </el-drawer>

    <!-- File Manager Modal -->
    <FileManager
      v-model="showFileManager"
      @fileSelected="handleFileSelected"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ArrowUp, ArrowDown, Microphone, Folder, MoreFilled, 
  Close, Check, Loading, CirclePlus, Picture
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import MessageBubble from '@/components/MessageBubble.vue'
import FileManager from '@/components/FileManager.vue'
import { useRoleStore } from '@/stores/role'
import { useChatStore } from '@/stores/chat'
import { chatApi } from '@/services/api/chat'
import { recommendationApi } from '@/services/api/recommendation'

const { t } = useI18n()

const roleStore = useRoleStore()
const chatStore = useChatStore()

// State
const selectedRoleId = ref<string | null>(null)
const inputText = ref('')
const emotionTag = ref('')
const loading = ref(false)
const isSpeaking = ref(false)
const currentAudioUrl = ref('')
const currentStyle = ref('realistic')
const showRoleDrawer = ref(false)
const showFileManager = ref(false)
const isRecording = ref(false)
const messagesRef = ref<HTMLElement | null>(null)
const recommendations = ref<string[]>([])
const loadingRecommendations = ref(false)

// Computed
const roles = computed(() => roleStore.roles)
// 直接使用 roleStore 的 currentRole，确保显示一致
const currentRole = computed(() => roleStore.currentRole)

const currentTemplates = computed(() => {
  const roleName = currentRole.value?.name || ''
  if (roleName.includes('律师')) {
    return ['合同纠纷咨询', '劳动仲裁流程', '知识产权保护', '法律风险评估']
  } else if (roleName.includes('教师')) {
    return ['制定学习计划', '解题思路讲解', '考试重点预测', '口语对练']
  } else if (roleName.includes('程序员')) {
    return ['代码性能优化', 'Bug排除思路', '新功能实现方案', '技术架构咨询']
  } else if (roleName.includes('作家')) {
    return ['创意灵感激发', '文章润色建议', '情节构思设计', '诗歌散文创作']
  }
  return ['日常打招呼', '今日天气如何', '帮我安排日程', '写一段总结']
})

// 加载推荐问题
// const loadRecommendations = async () => {
//   if (loadingRecommendations.value) return
  
//   try {
//     loadingRecommendations.value = true
//     const conversationHistory = chatStore.messages
//       .slice(-6) // 最近6条消息
//       .map(msg => msg.content)
//     const roleName = currentRole.value?.name
    
//     const result = await recommendationApi.getRecommendations(conversationHistory, roleName)
//     recommendations.value = result || []
//   } catch (error) {
//     console.error('加载推荐问题失败:', error)
//     recommendations.value = []
//   } finally {
//     loadingRecommendations.value = false
//   }
// }

// Methods
const useTemplate = (text: string) => {
  inputText.value = text
}

const useRecommendation = (text: string) => {
  inputText.value = text
  // 可选：自动发送
  // sendMessage()
}

const autoSegment = () => {
  if (inputText.value.length <= 500) return
  // Simple segmentation by punctuation or space
  const segments = inputText.value.match(/.{1,500}/g) || []
  inputText.value = segments.join('\n\n---\n\n')
  ElMessage.success(t('chat.autoSegment'))
}

const selectRole = async (role: any) => {
  if (chatStore.messages.length > 0) {
    try {
      const confirm = await ElMessageBox.confirm(
        t('role.deleteConfirm'),
        t('role.title'),
        {
          confirmButtonText: t('common.confirm'),
          cancelButtonText: t('common.cancel'),
          distinguishCancelAndClose: true,
          type: 'info'
        }
      )
      // If "保留" is clicked
      if (confirm === 'confirm') {
        // Keep context logic (if implemented in chatStore)
      }
    } catch (action) {
      if (action === 'cancel') {
        chatStore.clearMessages()
      } else {
        return // Closed without action
      }
    }
  }

  // 同步更新 selectedRoleId 和 roleStore.currentRole
  selectedRoleId.value = role.id
  await roleStore.setCurrentRole(role)
  showRoleDrawer.value = false // Auto close for smoother experience
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

const sendMessage = async () => {
  if (!inputText.value.trim() && !isRecording.value) return
  if (!selectedRoleId.value) {
    ElMessage.warning('Please select a role first')
    showRoleDrawer.value = true
    return
  }

  loading.value = true
  const userText = inputText.value
  inputText.value = '' // Optimistic clear

  try {
    // Add User Message
    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: userText,
      createdAt: new Date(),
      timestamp: Date.now()
    }
    chatStore.addMessage(userMessage)
    scrollToBottom()

    const response = await chatApi.sendMessage({
      roleId: selectedRoleId.value,
      message: userText,
      emotionTag: emotionTag.value,
      context: [] // Simplified
    })
    
    // Add AI Message
    if (response && response.text) {
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: response.text || '',
        createdAt: new Date(),
        timestamp: Date.now(),
        confidence: response.confidence,
        tokensUsed: response.tokensUsed,
        sources: response.sources,
        reasoningPath: response.reasoningPath,
        audioUrl: response.audioUrl
      }
      chatStore.addMessage(assistantMessage)
    } else {
      throw new Error('AI服务返回无效响应')
    }
    scrollToBottom()

    if (response.audioUrl) {
      currentAudioUrl.value = response.audioUrl
      isSpeaking.value = true
      // Mock stop
      setTimeout(() => isSpeaking.value = false, 5000)
    }

    // 加载推荐问题
    // await loadRecommendations()

  } catch (err: any) {
    ElMessage.error(err.message || 'Failed to send message')
    inputText.value = userText // Restore on error
  } finally {
    loading.value = false
  }
}

// Voice (Stub)
const startVoiceInput = () => { isRecording.value = true }
const stopVoiceInput = () => { isRecording.value = false }

const handleControl = (type: string) => {
  if (type === 'folder') showFileManager.value = true
}

const handleFileSelected = (file: any) => {
  ElMessage.success(`File selected: ${file.name}`)
}

// 监听 roleStore.currentRole 变化，同步 selectedRoleId
watch(() => roleStore.currentRole, (newRole) => {
  if (newRole) {
    selectedRoleId.value = newRole.id
  }
}, { immediate: true })

onMounted(async () => {
  await roleStore.loadRoles()
  // 如果有角色，设置第一个为当前角色，并同步 selectedRoleId
  if (roles.value.length > 0) {
    const firstRole = roles.value[0]
    // 如果 roleStore 中没有当前角色，则设置
    if (!roleStore.currentRole) {
      await roleStore.setCurrentRole(firstRole)
      selectedRoleId.value = firstRole.id
    } else {
      // 如果已有当前角色，同步 selectedRoleId
      selectedRoleId.value = roleStore.currentRole.id
    }
  }
  // 初始加载推荐问题
  // await loadRecommendations()
})
</script>

<style scoped>
/* --- Layout & Container --- */
.chat-view-container {
  height: 100%;
  width: 100%;
  position: relative;
  overflow: hidden;
  background-color: var(--bg-app);
  display: flex;
  flex-direction: column;
}

.chat-stage {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
}

/* Ambient Background */
.ambient-glow {
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.4;
  z-index: 0;
  pointer-events: none;
}
.top-left {
  top: -200px;
  left: -200px;
  background: radial-gradient(circle, var(--primary-fade) 0%, transparent 70%);
}
.bottom-right {
  bottom: -200px;
  right: -200px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.05) 0%, transparent 70%);
}

/* --- Digital Human Widget (Top-Left Floating) --- */
.digital-human-widget {
  position: absolute;
  top: 24px;
  left: 24px;
  width: 220px; /* Increased size */
  height: 300px;
  z-index: 5; /* 降低z-index，确保不遮挡消息 */
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.6);
  pointer-events: none; /* 允许点击穿透到消息区域 */
}

.digital-human-widget:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

/* Active state for speaking: Subtle glow border */
.digital-human-widget.is-speaking {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px var(--primary-fade), 0 8px 32px rgba(0, 0, 0, 0.1);
}

.dh-content {
  width: 100%;
  height: 100%;
  background: #000; /* Placeholder for video area */
}

.dh-controls-overlay {
  position: absolute;
  bottom: 12px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  pointer-events: none;
}

.digital-human-widget .dh-controls-overlay {
  pointer-events: auto; /* 控件区域可以交互 */
}

.status-indicator {
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  padding: 4px 10px;
  border-radius: 12px;
  color: white;
  font-size: 10px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  opacity: 0; /* Hidden by default */
  transition: opacity 0.3s;
}

.status-indicator.active {
  opacity: 1;
}

.pulse {
  width: 6px;
  height: 6px;
  background-color: #10b981;
  border-radius: 50%;
  animation: pulse-animation 1.5s infinite;
}

/* --- Header Actions (Top-Right Floating) --- */
.header-actions {
  position: absolute;
  top: 24px;
  right: 24px;
  z-index: 10;
  display: flex;
  gap: 12px;
}

.action-btn {
  height: 44px;
  padding: 0 12px 0 8px;
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-light);
  border-radius: 22px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-primary);
  font-family: inherit;
}

.action-btn.icon-only {
  width: 44px;
  justify-content: center;
  padding: 0;
}

.action-btn:hover {
  background: #ffffff;
  border-color: var(--primary-color);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
  transform: translateY(-1px);
}

.current-role-avatar {
  flex-shrink: 0;
  border: 2px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.role-name-label {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
  letter-spacing: -0.01em;
  white-space: nowrap;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.icon-right {
  font-size: 14px;
  color: var(--text-secondary);
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.action-btn:hover .icon-right {
  color: var(--primary-color);
  transform: translateY(1px);
}

/* --- Messages Container --- */
.messages-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 24px 8% 200px; /* 进一步减少左右padding，拓宽对话窗口 */
  display: flex;
  flex-direction: column;
  z-index: 1;
  scroll-behavior: smooth;
  min-height: 0; /* 确保可以滚动 */
}

/* Empty State */
.empty-state {
  margin: auto;
  text-align: center;
  opacity: 0.8;
  max-width: 400px;
}

.logo-mark {
  font-family: var(--font-serif);
  font-size: 14px;
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 24px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.welcome-text {
  font-size: 32px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 12px;
  font-family: var(--font-serif);
}

.subtitle {
  font-size: 16px;
  color: var(--text-secondary);
}

/* --- Message List --- */
.message-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 1200px; /* 进一步拓宽消息列表最大宽度 */
  margin: 0 auto;
  width: 100%;
}

/* --- Input Dock (Floating Bottom) --- */
.input-dock-wrapper {
  position: absolute; /* 改为absolute，相对于chat-stage定位 */
  bottom: 0;
  left: 0;
  right: 0;
  padding: 24px 32px 32px; /* 调整padding */
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  pointer-events: none; /* Let clicks pass through area */
  z-index: 20;
  background: linear-gradient(to top, var(--bg-app) 60%, transparent);
  max-width: 100%;
}

.templates-container {
  pointer-events: auto;
  display: flex;
  gap: 10px;
  overflow-x: auto;
  max-width: 1400px; /* 拓宽模板容器以匹配输入框 */
  width: 100%;
  padding: 6px 4px;
  scrollbar-width: none;
  scroll-behavior: smooth;
}

.templates-container::-webkit-scrollbar {
  display: none;
}

.template-tag {
  flex-shrink: 0;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 16px;
  font-size: 13px;
  color: var(--text-regular);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 500;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.template-tag:hover {
  background: white;
  border-color: var(--primary-color);
  color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);
}

.recommendations-container {
  pointer-events: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 1400px; /* 拓宽推荐问题容器以匹配输入框 */
  width: 100%;
  padding: 6px 4px;
}

.recommendations-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 4px;
}

.recommendation-tag {
  flex-shrink: 0;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 16px;
  font-size: 13px;
  color: var(--text-regular);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 500;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.recommendation-tag:hover {
  background: white;
  border-color: var(--primary-color);
  color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);
}

.input-dock {
  pointer-events: auto;
  width: 100%;
  max-width: 1400px; /* 进一步拓宽输入框最大宽度 */
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(24px) saturate(180%);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.08),
    0 2px 8px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.input-dock:focus-within {
  box-shadow: 
    0 12px 48px rgba(79, 70, 229, 0.12),
    0 4px 16px rgba(79, 70, 229, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.95);
  border-color: rgba(79, 70, 229, 0.2);
  transform: translateY(-2px);
}

.dock-input :deep(.el-textarea__inner) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 10px 0;
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-primary);
  font-family: var(--font-sans);
  resize: none;
  min-height: 24px !important;
}

.dock-input :deep(.el-textarea__inner)::placeholder {
  color: var(--text-disabled);
  opacity: 0.6;
}

.dock-input :deep(.el-textarea__inner):focus {
  outline: none;
}

.dock-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 2px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  padding-top: 10px;
  min-height: 40px;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.plus-trigger {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 20px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 10px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.plus-trigger:hover {
  color: var(--primary-color);
  background: rgba(79, 70, 229, 0.08);
  transform: scale(1.05);
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  padding: 8px;
}

.tool-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 12px;
  border-radius: var(--radius-md);
  transition: all 0.2s;
}

.tool-item:hover {
  background: var(--bg-app);
  color: var(--primary-color);
}

.tool-item .el-icon {
  font-size: 24px;
}

.tool-item .el-icon.is-recording {
  color: var(--danger);
  animation: pulse-animation 1s infinite;
}

.word-count {
  font-size: 13px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 400;
  letter-spacing: -0.01em;
}

.word-count.warning {
  color: #f59e0b;
  font-weight: 500;
}

.word-count .hint {
  font-weight: 500;
  opacity: 0.8;
}

.segment-btn {
  font-size: 12px;
  padding: 0;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.emotion-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.04);
  padding: 6px 12px;
  border-radius: 10px;
  font-size: 12px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.emotion-pill:hover {
  background: rgba(0, 0, 0, 0.06);
  border-color: rgba(79, 70, 229, 0.2);
}

.emotion-pill .label {
  font-weight: 500;
  color: var(--text-regular);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.7;
}

.emotion-pill .transparent-input {
  background: transparent;
  border: none;
  outline: none;
  font-size: 12px;
  color: var(--text-primary);
  font-weight: 500;
  width: 60px;
  padding: 0;
}

.emotion-pill .transparent-input::placeholder {
  color: var(--text-disabled);
  opacity: 0.6;
}

.send-trigger {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--primary-color) 0%, #6366f1 100%);
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 
    0 4px 12px rgba(79, 70, 229, 0.25),
    0 2px 4px rgba(79, 70, 229, 0.15);
  position: relative;
  overflow: hidden;
}

.send-trigger::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2) 0%, transparent 100%);
  opacity: 0;
  transition: opacity 0.2s;
}

.send-trigger:hover:not(:disabled)::before {
  opacity: 1;
}

.send-trigger:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.05);
  background: linear-gradient(135deg, var(--primary-hover) 0%, #818cf8 100%);
  box-shadow: 
    0 6px 20px rgba(79, 70, 229, 0.35),
    0 4px 8px rgba(79, 70, 229, 0.2);
}

.send-trigger:active:not(:disabled) {
  transform: translateY(0) scale(0.98);
}

.send-trigger:disabled {
  background: var(--text-disabled);
  cursor: not-allowed;
  box-shadow: none;
  opacity: 0.5;
}

.send-trigger .el-icon {
  font-size: 18px;
  font-weight: 600;
}

/* --- Drawer Styles --- */
.drawer-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-app);
}

.drawer-header {
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.drawer-header h2 {
  font-family: var(--font-serif);
  font-size: 20px;
}

.role-grid {
  flex: 1;
  overflow-y: auto;
  padding: 0 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.role-card-minimal {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #fff;
  border: 1px solid var(--border-light);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.role-card-minimal:hover {
  border-color: var(--primary-color);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.role-card-minimal.active {
  border-color: var(--primary-color);
  background: var(--primary-fade);
}

.role-info {
  flex: 1;
}

.role-info .name {
  font-weight: 600;
  font-size: 15px;
  color: var(--text-primary);
}

.role-info .desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.check-mark {
  color: var(--primary-color);
}

/* Animation */
@keyframes pulse-animation {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.5); opacity: 0.5; }
  100% { transform: scale(1); opacity: 1; }
}

.role-fade-enter-active, .role-fade-leave-active {
  transition: opacity 0.5s ease, filter 0.5s ease;
}
.role-fade-enter-from, .role-fade-leave-to {
  opacity: 0;
  filter: blur(10px);
}

@media (max-width: 1024px) {
  .messages-container {
    padding: 120px 16px 200px; /* 调整底部padding以匹配输入框高度 */
  }
  .message-list {
    max-width: 100%; /* 小屏幕上使用全宽 */
  }
  .input-dock {
    max-width: 100%;
  }
  .templates-container,
  .recommendations-container {
    max-width: 100%;
  }
}
</style>
