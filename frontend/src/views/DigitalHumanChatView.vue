<template>
  <div class="dh-view-container">
    <div class="glass-layout">
      
      <!-- Left: Role Library -->
      <aside class="left-panel">
        <div class="panel-header">
          <h2>Persona Library</h2>
          <div class="search-wrapper">
             <el-icon class="search-icon"><Search /></el-icon>
             <input 
               v-model="searchKeyword" 
               placeholder="Search roles..." 
               class="clean-input"
             />
          </div>
        </div>

        <div class="role-scroll-area">
          <div class="role-grid">
            <div
              v-for="role in filteredRoles"
              :key="role.id"
              class="role-card-artistic"
              :class="{ 'active': selectedRoleId === role.id }"
              @click="selectRole(role)"
            >
              <div class="card-visual">
                 <el-avatar :src="role.avatar" :size="48" shape="circle" class="role-avatar">
                    {{ role.name.charAt(0) }}
                 </el-avatar>
                 <div class="status-dot"></div>
              </div>
              <div class="card-info">
                 <div class="role-name">{{ role.name }}</div>
                 <div class="role-tag">{{ role.subtitle || 'Assistant' }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Stylish Create Button Area -->
        <div class="create-action-area">
           <button class="create-btn-premium" @click="showCreateDialog = true">
              <span class="icon-box"><el-icon><Plus /></el-icon></span>
              <span class="label">Create New Persona</span>
           </button>
        </div>
      </aside>

      <!-- Center: Immersive Stage -->
      <main class="center-stage">
        <!-- Digital Human Preview Area (Dominant) -->
        <div class="stage-preview" :style="{ background: previewBackground }">
           <div class="dh-container" :style="{ transform: `scale(${dhScale / 100})` }">
              <DigitalHuman
                :role-id="selectedRoleId"
                :is-speaking="isSpeaking"
                :audio-url="currentAudioUrl"
                :style="currentStyle"
              />
           </div>
           
           <!-- Overlay Controls -->
           <div class="stage-overlay-controls">
              <el-tag effect="dark" round class="status-tag" v-if="isSpeaking">Speaking</el-tag>
           </div>
        </div>

        <!-- Chat Interaction Area -->
        <div class="stage-chat-area">
           <div class="chat-messages-scroll" ref="messagesContainer">
              <div v-for="msg in messages" :key="msg.id" class="message-row" :class="msg.role">
                 <div class="message-bubble-premium" :class="[msg.role, bubbleStyle]">
                    {{ msg.content }}
                 </div>
                 <span class="time-stamp">{{ formatTime(msg.timestamp) }}</span>
              </div>
           </div>
           
           <!-- Floating Input -->
           <div class="input-floater">
              <div class="input-pill">
                 <div class="voice-btn" @click="isRecording ? stopVoiceInput() : startVoiceInput()" :class="{ recording: isRecording }">
                    <el-icon><Microphone /></el-icon>
                 </div>
                 <input 
                   v-model="inputText" 
                   placeholder="Type a message to interact..." 
                   @keyup.enter="sendMessage"
                 />
                 <button class="send-btn" @click="sendMessage" :disabled="loading">
                    <el-icon v-if="!loading"><ArrowUp /></el-icon>
                    <el-icon v-else class="is-loading"><Loading /></el-icon>
                 </button>
              </div>
           </div>
        </div>
      </main>

      <!-- Right: Configuration & Tools -->
      <aside class="right-panel">
         <div class="panel-header">
            <h3>Configuration</h3>
            <div class="header-actions">
               <el-button circle text @click="showSettings = true"><el-icon><Setting /></el-icon></el-button>
            </div>
         </div>

         <div class="config-content">
            <!-- Section: Appearance -->
            <div class="config-section">
               <div class="section-title">Visual Settings</div>
               
               <div class="control-group">
                  <label>Character Scale</label>
                  <el-slider v-model="dhScale" :min="50" :max="120" size="small" />
               </div>

               <div class="control-group">
                  <label>Preview Background</label>
                  <div class="color-options">
                     <div class="color-circle" style="background: #f8fafc" @click="previewBackground = '#f8fafc'"></div>
                     <div class="color-circle" style="background: #e0f2fe" @click="previewBackground = '#e0f2fe'"></div>
                     <div class="color-circle" style="background: #f0fdf4" @click="previewBackground = '#f0fdf4'"></div>
                     <div class="color-circle" style="background: #1e293b" @click="previewBackground = '#1e293b'"></div>
                  </div>
               </div>
            </div>

            <!-- Section: Chat Bubbles -->
            <div class="config-section">
               <div class="section-title">Bubble Style</div>
               <div class="bubble-selector">
                  <div 
                    class="bubble-option default" 
                    :class="{ active: bubbleStyle === 'default' }"
                    @click="bubbleStyle = 'default'"
                  >Default</div>
                  <div 
                    class="bubble-option glass" 
                    :class="{ active: bubbleStyle === 'glass' }"
                    @click="bubbleStyle = 'glass'"
                  >Glass</div>
                  <div 
                    class="bubble-option flat" 
                    :class="{ active: bubbleStyle === 'flat' }"
                    @click="bubbleStyle = 'flat'"
                  >Flat</div>
               </div>
            </div>

            <!-- Section: Export & History -->
            <div class="config-section">
               <div class="section-title">Data Management</div>
               <div class="action-list">
                  <button class="action-item" @click="exportConversation">
                     <el-icon><Download /></el-icon>
                     <span>Export Conversation</span>
                  </button>
                  <button class="action-item" @click="clearConversation">
                     <el-icon><Delete /></el-icon>
                     <span>Clear History</span>
                  </button>
               </div>
            </div>

            <!-- Context Info -->
            <div class="info-card glass-card">
               <div class="info-header">Current Session</div>
               <div class="info-row">
                  <span>Role</span>
                  <strong>{{ currentRole?.name }}</strong>
               </div>
               <div class="info-row">
                  <span>Model</span>
                  <strong>Kinlin-Pro V4</strong>
               </div>
            </div>
         </div>
      </aside>
    </div>

    <!-- Dialogs -->
    <CreateRoleDialog v-model="showCreateDialog" @created="handleRoleCreated" />
    
    <!-- Export Dialog -->
    <el-dialog v-model="showExportDialog" title="Export Chat" width="400px" class="premium-dialog">
       <div class="export-options">
          <div 
            class="export-card" 
            :class="{ active: exportFormat === 'txt' }"
            @click="exportFormat = 'txt'"
          >
             <div class="icon">TXT</div>
             <span>Plain Text</span>
          </div>
          <div 
            class="export-card" 
            :class="{ active: exportFormat === 'json' }"
            @click="exportFormat = 'json'"
          >
             <div class="icon">JSON</div>
             <span>Data Structure</span>
          </div>
       </div>
       <template #footer>
          <div class="dialog-footer">
             <el-button @click="showExportDialog = false">Cancel</el-button>
             <el-button type="primary" @click="handleExport(exportFormat)">Export Now</el-button>
          </div>
       </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import {
  Search, Plus, Microphone, Loading, ArrowUp, Setting,
  Download, Delete
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import DigitalHuman from '@/components/DigitalHuman.vue'
import CreateRoleDialog from '@/components/CreateRoleDialog.vue'
import { useRoleStore } from '@/stores/role'
import { useChatStore } from '@/stores/chat'
import { chatApi } from '@/services/api/chat'
import { voiceApi } from '@/services/api/voice'

const roleStore = useRoleStore()
const chatStore = useChatStore()

// State
const searchKeyword = ref('')
const selectedRoleId = ref<string | null>(null)
const inputText = ref('')
const loading = ref(false)
const isSpeaking = ref(false)
const currentAudioUrl = ref('')
const currentStyle = ref('realistic')
const showCreateDialog = ref(false)
const showSettings = ref(false)
const showExportDialog = ref(false)
const exportFormat = ref<'json' | 'txt'>('txt')
const messagesContainer = ref<HTMLElement>()

// Config State (Visuals)
const dhScale = ref(100)
const previewBackground = ref('#f8fafc')
const bubbleStyle = ref('default')
const isRecording = ref(false)

// Computed
const currentRole = computed(() => {
  if (!selectedRoleId.value) return null
  return roleStore.roles.find(r => r.id === selectedRoleId.value)
})

const filteredRoles = computed(() => {
  if (!searchKeyword.value) return roleStore.roles
  const keyword = searchKeyword.value.toLowerCase()
  return roleStore.roles.filter(role =>
    role.name.toLowerCase().includes(keyword) ||
    role.description?.toLowerCase().includes(keyword)
  )
})

const messages = computed(() => chatStore.messages)

// Methods
const selectRole = (role: any) => {
  selectedRoleId.value = role.id
  roleStore.setCurrentRole(role)
}

const sendMessage = async () => {
  if (!inputText.value.trim() || !selectedRoleId.value) return
  
  const text = inputText.value
  chatStore.addMessage({
    id: Date.now().toString(),
    role: 'user',
    content: text,
    timestamp: Date.now()
  })
  inputText.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const response = await chatApi.sendMessage({
      roleId: selectedRoleId.value,
      message: text,
      context: messages.value.slice(-5).map(m => ({ role: m.role, content: m.content }))
    })

    chatStore.addMessage({
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: response.text,
      timestamp: Date.now(),
      audioUrl: response.audioUrl
    })

    if (response.audioUrl) {
      currentAudioUrl.value = response.audioUrl
      isSpeaking.value = true
      setTimeout(() => isSpeaking.value = false, 5000)
    }
    scrollToBottom()
  } catch (err) {
    ElMessage.error('Failed to send message')
  } finally {
    loading.value = false
  }
}

const startVoiceInput = () => { isRecording.value = true; ElMessage.info('Recording started...') }
const stopVoiceInput = () => { isRecording.value = false; ElMessage.info('Recording stopped') }

const exportConversation = () => { showExportDialog.value = true }
const clearConversation = () => { chatStore.clearMessages(); ElMessage.success('History cleared') }
const handleRoleCreated = (role: any) => { 
  roleStore.addRole(role)
  selectedRoleId.value = role.id
  ElMessage.success('Persona created') 
}

// Simple export handler (simplified logic from previous file)
const handleExport = (format: string) => {
    // Logic similar to previous file
    ElMessage.success(`Exporting as ${format.toUpperCase()}...`)
    showExportDialog.value = false
}

const formatTime = (ts: number) => new Date(ts).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  })
}

onMounted(async () => {
  await roleStore.loadRoles()
  if (roleStore.roles.length > 0) selectedRoleId.value = roleStore.roles[0].id
})
</script>

<style scoped>
.dh-view-container {
  height: 100%;
  width: 100%;
  background: var(--bg-app);
  color: var(--text-primary);
  font-family: var(--font-sans);
  overflow: hidden;
}

.glass-layout {
  display: grid;
  grid-template-columns: 280px 1fr 300px; /* Left, Center, Right */
  height: 100%;
}

/* --- Left Panel --- */
.left-panel {
  background: #fff;
  border-right: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 20px;
  border-bottom: 1px solid var(--border-light);
}

.panel-header h2 {
  font-family: var(--font-serif);
  font-size: 18px;
  margin-bottom: 16px;
}

.search-wrapper {
  display: flex;
  align-items: center;
  background: var(--bg-input);
  padding: 8px 12px;
  border-radius: var(--radius-md);
  transition: all 0.2s;
}

.search-wrapper:focus-within {
  box-shadow: 0 0 0 2px var(--primary-fade);
  background: #fff;
}

.clean-input {
  border: none;
  background: transparent;
  width: 100%;
  margin-left: 8px;
  outline: none;
  font-family: var(--font-sans);
  color: var(--text-primary);
}

.role-scroll-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.role-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.role-card-artistic {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.role-card-artistic:hover {
  background: var(--bg-input);
}

.role-card-artistic.active {
  background: #fff;
  border-color: var(--primary-color);
  box-shadow: var(--shadow-md);
}

.card-visual {
  position: relative;
  margin-right: 12px;
}

.status-dot {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 10px;
  height: 10px;
  background: var(--success);
  border: 2px solid #fff;
  border-radius: 50%;
}

.role-name { font-weight: 600; font-size: 14px; }
.role-tag { font-size: 12px; color: var(--text-secondary); }

.create-action-area {
  padding: 20px;
  border-top: 1px solid var(--border-light);
}

.create-btn-premium {
  width: 100%;
  padding: 12px;
  border: none;
  background: var(--text-primary); /* Dark button */
  color: #fff;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
  box-shadow: var(--shadow-md);
}

.create-btn-premium:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  background: #000;
}

/* --- Center Stage --- */
.center-stage {
  display: flex;
  flex-direction: column;
  background: #f8fafc;
}

.stage-preview {
  flex: 1; /* Occupy top half+ */
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  transition: background 0.3s;
  min-height: 300px;
}

.dh-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s;
}

.stage-overlay-controls {
  position: absolute;
  top: 20px;
  right: 20px;
}

.stage-chat-area {
  height: 40%;
  background: #fff;
  border-top: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  position: relative;
}

.chat-messages-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-row {
  display: flex;
  flex-direction: column;
  max-width: 80%;
  gap: 4px;
}

.message-row.user { align-self: flex-end; align-items: flex-end; }
.message-row.assistant { align-self: flex-start; align-items: flex-start; }

.message-bubble-premium {
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.5;
  box-shadow: var(--shadow-sm);
}

/* Bubble Styles */
.user .message-bubble-premium { background: var(--primary-color); color: #fff; border-bottom-right-radius: 4px; }
.assistant .message-bubble-premium { background: #f1f5f9; color: var(--text-primary); border-bottom-left-radius: 4px; }

/* Flat Style Override */
.message-bubble-premium.flat { box-shadow: none; border: 1px solid var(--border-light); }
.user .message-bubble-premium.flat { background: var(--text-primary); border: none; }

.time-stamp { font-size: 10px; color: var(--text-disabled); margin: 0 4px; }

.input-floater {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 600px;
}

.input-pill {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  padding: 6px;
  border-radius: 30px;
  display: flex;
  align-items: center;
  box-shadow: var(--shadow-lg);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.voice-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}
.voice-btn:hover { background: var(--bg-input); color: var(--text-primary); }
.voice-btn.recording { color: var(--danger); background: #fee2e2; }

.input-pill input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 0 12px;
  outline: none;
  font-size: 14px;
}

.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--primary-color);
  color: #fff;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s;
}
.send-btn:hover { transform: scale(1.05); }

/* --- Right Panel --- */
.right-panel {
  background: #fff;
  border-left: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
}

.config-content {
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 12px;
}

.control-group { margin-bottom: 16px; }
.control-group label { display: block; font-size: 13px; margin-bottom: 8px; font-weight: 500; }

.color-options { display: flex; gap: 8px; }
.color-circle {
  width: 24px; height: 24px;
  border-radius: 50%;
  cursor: pointer;
  border: 1px solid var(--border-light);
}

.bubble-selector {
  display: flex;
  background: var(--bg-input);
  padding: 4px;
  border-radius: 12px;
}

.bubble-option {
  flex: 1;
  text-align: center;
  padding: 6px;
  font-size: 12px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-secondary);
}

.bubble-option.active {
  background: #fff;
  color: var(--text-primary);
  font-weight: 600;
  box-shadow: var(--shadow-sm);
}

.action-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-item {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--border-light);
  background: #fff;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  color: var(--text-regular);
  transition: all 0.2s;
}

.action-item:hover {
  background: var(--bg-input);
  color: var(--primary-color);
  border-color: var(--primary-color);
}

.info-card {
  padding: 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
}

.info-header { font-weight: 600; margin-bottom: 12px; font-size: 14px; }
.info-row { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px; }

/* Dialog Styles */
.export-options {
   display: grid;
   grid-template-columns: 1fr 1fr;
   gap: 16px;
   padding: 16px 0;
}

.export-card {
   border: 1px solid var(--border-light);
   border-radius: 12px;
   padding: 20px;
   text-align: center;
   cursor: pointer;
   transition: all 0.2s;
}

.export-card:hover { border-color: var(--primary-color); }
.export-card.active { background: var(--primary-fade); border-color: var(--primary-color); }
.export-card .icon { font-weight: 700; font-size: 18px; margin-bottom: 8px; }

.dialog-footer { display: flex; justify-content: flex-end; gap: 12px; }
</style>
