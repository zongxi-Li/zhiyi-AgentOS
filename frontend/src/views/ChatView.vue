<template>
  <div class="chat-view-container">
    <!-- Background Elements for Atmosphere -->
    <div class="ambient-glow top-left"></div>
    <div class="ambient-glow bottom-right"></div>

    <!-- Main Chat Content -->
    <main class="chat-stage">
      
      <!-- Top Left: Digital Human Widget -->
      <div class="digital-human-widget glass-card" :class="{ 'is-speaking': isSpeaking }">
        <div class="dh-content">
           <DigitalHuman
             :role-id="selectedRoleId"
             :is-speaking="isSpeaking"
             :audio-url="currentAudioUrl"
             :style="currentStyle"
           />
        </div>
        <!-- Minimal Controls Overlay -->
        <div class="dh-controls-overlay">
           <div class="status-indicator" :class="{ active: isSpeaking }">
             <span class="pulse"></span>
             {{ isSpeaking ? 'Speaking' : 'Listening' }}
           </div>
        </div>
      </div>

      <!-- Top Right: Header Actions (Role & Settings) -->
      <div class="header-actions">
        <el-tooltip content="切换角色" placement="bottom" effect="light">
          <div class="action-btn glass-btn" @click="showRoleDrawer = true">
             <el-avatar :size="32" :src="currentRole?.avatar" class="current-role-avatar">
               {{ currentRole?.name?.charAt(0) }}
             </el-avatar>
             <span class="role-name-label">{{ currentRole?.name || '选择角色' }}</span>
             <el-icon class="icon-right"><ArrowDown /></el-icon>
          </div>
        </el-tooltip>
        
        <el-tooltip content="更多设置" placement="bottom" effect="light">
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
             <h1 class="welcome-text">How can I help you today?</h1>
             <p class="subtitle">Select a role to start an immersive conversation.</p>
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
                  :content="msg.content" 
                  :role="msg.role"
                  :timestamp="msg.timestamp"
                />
             </div>
          </div>
        </div>
      </div>

      <!-- Bottom: Input Area (Floating) -->
      <div class="input-dock-wrapper">
        <div class="input-dock glass-panel">
          <!-- Emotion & Tools -->
          <div class="dock-header">
             <div class="emotion-pill">
               <span class="label">Emotion</span>
               <input v-model="emotionTag" placeholder="Auto" class="transparent-input" />
             </div>
             <div class="tools">
                <el-button link class="tool-btn" @click="handleControl('folder')">
                  <el-icon><Folder /></el-icon>
                </el-button>
             </div>
          </div>

          <!-- Textarea -->
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="1"
            :autosize="{ minRows: 1, maxRows: 6 }"
            resize="none"
            placeholder="Type a message..."
            class="dock-input"
            @keydown.enter.prevent="sendMessage"
          />

          <!-- Action Button -->
          <div class="dock-footer">
             <div class="voice-trigger" :class="{ 'is-recording': isRecording }" @click="isRecording ? stopVoiceInput() : startVoiceInput()">
                <el-icon><Microphone /></el-icon>
             </div>
             <button class="send-trigger" @click="sendMessage" :disabled="loading || (!inputText.trim() && !isRecording)">
                <el-icon v-if="!loading"><ArrowUp /></el-icon>
                <el-icon v-else class="is-loading"><Loading /></el-icon>
             </button>
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
              :class="{ 'active': selectedRoleId === role.id }"
              @click="selectRole(role)"
            >
               <el-avatar :size="48" :src="role.avatar" class="role-avatar-lg">
                  {{ role.name.charAt(0) }}
               </el-avatar>
               <div class="role-info">
                  <div class="name">{{ role.name }}</div>
                  <div class="desc">{{ role.tag || 'AI Assistant' }}</div>
               </div>
               <div class="check-mark" v-if="selectedRoleId === role.id">
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
import { ref, computed, onMounted, nextTick } from 'vue'
import {
  ArrowUp, ArrowDown, Microphone, Folder, MoreFilled, 
  Close, Check, Loading
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import DigitalHuman from '@/components/DigitalHuman.vue'
import MessageBubble from '@/components/MessageBubble.vue'
import FileManager from '@/components/FileManager.vue'
import { useRoleStore } from '@/stores/role'
import { useChatStore } from '@/stores/chat'
import { chatApi } from '@/services/api/chat'

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

// Computed
const roles = computed(() => roleStore.roles)
const currentRole = computed(() => {
  if (!selectedRoleId.value) return null
  return roles.value.find(r => r.id === selectedRoleId.value)
})

// Methods
const selectRole = (role: any) => {
  selectedRoleId.value = role.id
  roleStore.setCurrentRole(role)
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
    chatStore.addMessage({
      id: Date.now().toString(),
      role: 'user',
      content: userText,
      timestamp: Date.now()
    })
    scrollToBottom()

    const response = await chatApi.sendMessage({
      roleId: selectedRoleId.value,
      message: userText,
      emotionTag: emotionTag.value,
      context: [] // Simplified
    })
    
    // Add AI Message
    chatStore.addMessage({
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: response.text,
      timestamp: Date.now(),
      audioUrl: response.audioUrl
    })
    scrollToBottom()

    if (response.audioUrl) {
      currentAudioUrl.value = response.audioUrl
      isSpeaking.value = true
      // Mock stop
      setTimeout(() => isSpeaking.value = false, 5000)
    }

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

onMounted(async () => {
  await roleStore.loadRoles()
  if (roles.value.length > 0) selectedRoleId.value = roles.value[0].id
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
  z-index: 10;
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.6);
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
  height: 48px;
  padding: 0 8px 0 8px; /* Avatar padding */
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid white;
  border-radius: 24px; /* Pill shape */
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-primary);
}

.action-btn.icon-only {
  width: 48px;
  justify-content: center;
  padding: 0;
}

.action-btn:hover {
  background: white;
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.role-name-label {
  font-weight: 600;
  font-size: 14px;
  margin-right: 4px;
}

.icon-right {
  font-size: 12px;
  color: var(--text-secondary);
  margin-right: 8px;
}

/* --- Messages Container --- */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 100px 20% 160px; /* Top padding for widget, bottom for input */
  display: flex;
  flex-direction: column;
  z-index: 1;
  scroll-behavior: smooth;
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
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

/* --- Input Dock (Floating Bottom) --- */
.input-dock-wrapper {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 32px;
  display: flex;
  justify-content: center;
  pointer-events: none; /* Let clicks pass through area */
  z-index: 20;
  background: linear-gradient(to top, var(--bg-app) 10%, transparent);
}

.input-dock {
  pointer-events: auto;
  width: 100%;
  max-width: 960px; /* Increased width */
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.1);
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.input-dock:focus-within {
  box-shadow: 0 24px 48px -12px rgba(79, 70, 229, 0.15);
  border-color: #fff;
}

.dock-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.emotion-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.03);
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
}

.emotion-pill .label {
  color: var(--text-secondary);
  font-weight: 500;
}

.transparent-input {
  background: transparent;
  border: none;
  outline: none;
  font-size: 12px;
  color: var(--text-primary);
  width: 60px;
  font-family: var(--font-sans);
}

.dock-input :deep(.el-textarea__inner) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0;
  font-size: 16px;
  line-height: 1.5;
  color: var(--text-primary);
  font-family: var(--font-sans);
}

.dock-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
}

.voice-trigger {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.voice-trigger:hover {
  background: rgba(0, 0, 0, 0.05);
  color: var(--text-primary);
}

.voice-trigger.is-recording {
  background: #fee2e2;
  color: #ef4444;
}

.send-trigger {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  background: var(--primary-color);
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
}

.send-trigger:hover:not(:disabled) {
  transform: scale(1.05);
  background: var(--primary-hover);
}

.send-trigger:disabled {
  background: var(--text-disabled);
  cursor: not-allowed;
  box-shadow: none;
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

@media (max-width: 1024px) {
  .messages-container {
    padding: 120px 16px 160px; /* Adjust padding for mobile/tablet */
  }
  .digital-human-widget {
    width: 120px;
    height: 160px;
  }
}
</style>
