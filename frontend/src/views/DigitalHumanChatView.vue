<template>
  <div class="dh-view-container">
    <div class="main-layout">
      
      <!-- Left: Digital Human Management -->
      <aside class="left-panel">
        <div class="panel-header">
          <h2 class="panel-title">数字人形象</h2>
          <p class="panel-subtitle">管理已有数字人</p>
        </div>

        <div class="search-section">
          <div class="search-wrapper">
             <el-icon class="search-icon"><Search /></el-icon>
             <input 
               v-model="searchKeyword" 
               placeholder="搜索数字人..." 
               class="clean-input"
             />
          </div>
        </div>

        <div class="role-scroll-area">
          <div class="role-list">
            <div
              v-for="role in filteredRoles"
              :key="role.id"
              class="role-item-wrapper"
              :class="{ 'active': selectedRoleId === role.id }"
            >
              <div class="role-item" @click="selectRole(role)">
                <div class="role-avatar-wrapper">
                   <el-avatar :src="role.avatar" :size="40" shape="circle" class="role-avatar">
                      {{ role.name.charAt(0) }}
                   </el-avatar>
                </div>
                <div class="role-info">
                   <div class="role-name">{{ role.name }}</div>
                   <div class="role-desc">{{ role.description || '数字人助手' }}</div>
                </div>
                <div class="role-badge" v-if="roleAvatars[role.id]?.length">
                  <span class="badge-count">{{ roleAvatars[role.id].length }}</span>
                </div>
                <div class="role-action">
                  <el-icon class="action-icon"><ArrowRight /></el-icon>
                </div>
              </div>
              
              <!-- 形象列表（展开时显示） -->
              <div v-if="selectedRoleId === role.id && roleAvatars[role.id]?.length" class="avatar-list">
                <div
                  v-for="avatar in roleAvatars[role.id]"
                  :key="avatar.avatar_id"
                  class="avatar-item"
                  :class="{ 'active': selectedAvatarId === avatar.avatar_id }"
                  @click.stop="selectAvatar(avatar)"
                >
                  <div class="avatar-thumbnail">
                    <img v-if="avatar.avatar || avatar.local_image_url" 
                         :src="avatar.avatar || avatar.local_image_url" 
                         :alt="avatar.name || '形象'"
                         @error="handleImageError" />
                    <div v-else class="avatar-placeholder">{{ (avatar.name || '形象').charAt(0) }}</div>
                  </div>
                  <div class="avatar-info">
                    <div class="avatar-name">{{ avatar.name || `形象_${avatar.avatar_id?.substring(0, 8)}` }}</div>
                    <div class="avatar-meta">{{ getStyleName(avatar.style || 'realistic') }}</div>
                  </div>
                  <div class="avatar-status" v-if="selectedAvatarId === avatar.avatar_id">
                    <el-icon class="status-icon"><Check /></el-icon>
                  </div>
                </div>
                <div class="avatar-list-actions">
                  <el-button
                    text
                    size="small"
                    @click.stop="showCreateAvatarForRole(role)"
                    class="add-avatar-btn"
                  >
                    <el-icon><Plus /></el-icon>
                    <span>添加新形象</span>
                  </el-button>
                </div>
              </div>
              
              <!-- 加载状态 -->
              <div v-if="selectedRoleId === role.id && loadingAvatars[role.id]" class="avatar-loading">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>加载形象中...</span>
              </div>
              
              <!-- 空状态 -->
              <!-- <div v-if="selectedRoleId === role.id && !loadingAvatars[role.id] && (!roleAvatars[role.id] || roleAvatars[role.id].length === 0)" class="avatar-empty">
                <p>暂无形象</p>
                <el-button size="small" text @click.stop="showCreateAvatarForRole(role)">
                  <el-icon><Plus /></el-icon>
                  创建形象
                </el-button>
              </div> -->
            </div>
          </div>
        </div>

        <!-- Create New Digital Human -->
        <div class="create-section">
           <button class="create-btn" @click="showCreateDialog = true">
              <el-icon class="create-icon"><Plus /></el-icon>
              <span class="create-label">创建新角色</span>
           </button>
        </div>
      </aside>

      <!-- Center: Preview & Interaction -->
      <main class="center-stage">
        <!-- Digital Human Preview Area -->
        <div class="preview-section">
          <div class="preview-header">
            <h3 class="preview-title">预览效果</h3>
            <div class="preview-status" v-if="isSpeaking">
              <span class="status-dot-animated"></span>
              <span class="status-text">正在对话</span>
            </div>
          </div>
          
          <div class="preview-container" :style="{ background: previewBackground }">
             <div 
               class="dh-wrapper" 
               :style="getAvatarWrapperStyle()"
             >
                <DigitalHuman
                  :role-id="selectedRoleId"
                  :avatar-id="selectedAvatarId"
                  :is-speaking="isSpeaking"
                  :audio-url="currentAudioUrl"
                  :style="currentStyle"
                />
             </div>
          </div>
        </div>

        <!-- Chat Interaction Area -->
        <div class="chat-section">
          <div class="chat-header">
            <h3 class="chat-title">对话预览</h3>
            <span class="chat-subtitle">与数字人实时对话测试</span>
          </div>
          
          <div class="chat-messages" ref="messagesContainer">
             <div v-for="msg in messages" :key="msg.id" class="message-item" :class="msg.role">
                <div class="message-content" :class="msg.role">
                   {{ msg.content }}
                </div>
                <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
             </div>
             <div v-if="messages.length === 0" class="empty-chat">
               <el-icon class="empty-icon"><ChatLineRound /></el-icon>
               <p class="empty-text">开始与数字人对话，测试交互效果</p>
             </div>
          </div>
          
          <!-- Input Area -->
          <div class="input-area">
             <div class="input-container">
                <button 
                  class="voice-button" 
                  @click="isRecording ? stopVoiceInput() : startVoiceInput()" 
                  :class="{ recording: isRecording }"
                  title="语音输入"
                >
                   <el-icon><Microphone /></el-icon>
                </button>
                <input 
                  v-model="inputText" 
                  placeholder="输入消息与数字人对话..." 
                  class="message-input"
                  @keyup.enter="sendMessage"
                />
                <button 
                  class="send-button" 
                  @click="sendMessage" 
                  :disabled="loading || !inputText.trim()"
                  title="发送"
                >
                   <el-icon v-if="!loading"><ArrowUp /></el-icon>
                   <el-icon v-else class="is-loading"><Loading /></el-icon>
                </button>
             </div>
          </div>
        </div>
      </main>

      <!-- Right: Settings & Tools -->
      <aside class="right-panel">
         <div class="panel-header">
            <h3 class="panel-title">设置与工具</h3>
         </div>

         <div class="config-content">
            <!-- Digital Human Settings -->
            <div class="config-section">
               <div class="section-title">数字人设置</div>
               
               <!-- 画质级别 -->
               <div class="control-item">
                  <label class="control-label">画质级别</label>
                  <el-radio-group v-model="renderQuality" size="small" @change="handleQualityChange" class="quality-radio-group">
                     <el-radio-button label="low">低</el-radio-button>
                     <el-radio-button label="medium">中</el-radio-button>
                     <el-radio-button label="high">高</el-radio-button>
                  </el-radio-group>
                  <div class="control-hint">{{ qualityHint }}</div>
               </div>

               <!-- 展示风格（仅显示当前形象的风格，不可切换） -->
               <div class="control-item">
                  <label class="control-label">当前风格</label>
                  <div class="style-display">
                     <div class="style-badge" :class="`style-${currentStyle}`">
                        {{ getStyleName(currentStyle) }}
                     </div>
                     <div class="control-hint">当前形象的生成风格，如需切换请创建新形象</div>
                  </div>
               </div>

               <!-- 数字人大小（预览设置，不影响形象本身） -->
               <div class="control-item">
                  <label class="control-label">预览大小</label>
                  <el-slider 
                    v-model="dhScale" 
                    :min="50" 
                    :max="120" 
                    size="small"
                    :show-tooltip="true"
                    @change="handlePreviewScaleChange"
                  />
                  <span class="control-value">{{ dhScale }}%</span>
                  <div class="control-hint">仅影响预览显示，不影响形象本身</div>
               </div>

               <!-- 预览背景 -->
               <div class="control-item">
                  <label class="control-label">预览背景</label>
                  <div class="color-grid">
                     <div 
                       class="color-option" 
                       :class="{ active: previewBackground === '#f8fafc' }"
                       style="background: #f8fafc" 
                       @click="previewBackground = '#f8fafc'"
                       title="浅灰"
                     ></div>
                     <div 
                       class="color-option" 
                       :class="{ active: previewBackground === '#ffffff' }"
                       style="background: #ffffff" 
                       @click="previewBackground = '#ffffff'"
                       title="白色"
                     ></div>
                     <div 
                       class="color-option" 
                       :class="{ active: previewBackground === '#f1f5f9' }"
                       style="background: #f1f5f9" 
                       @click="previewBackground = '#f1f5f9'"
                       title="灰白"
                     ></div>
                     <div 
                       class="color-option" 
                       :class="{ active: previewBackground === '#fafafa' }"
                       style="background: #fafafa" 
                       @click="previewBackground = '#fafafa'"
                       title="米白"
                     ></div>
                  </div>
               </div>
            </div>

            <!-- Current Session Info -->
            <div class="info-section">
               <div class="section-title">当前会话</div>
               <div class="info-card">
                  <div class="info-item">
                     <span class="info-label">角色</span>
                     <span class="info-value">{{ currentRole?.name || '未选择' }}</span>
                  </div>
                  <div class="info-item" v-if="selectedAvatarId">
                     <span class="info-label">形象</span>
                     <span class="info-value">
                        {{ getCurrentAvatarName() || '未选择' }}
                     </span>
                  </div>
                  <div class="info-item">
                     <span class="info-label">风格</span>
                     <span class="info-value">{{ getStyleName(currentStyle) }}</span>
                  </div>
                  <div class="info-item">
                     <span class="info-label">对话数</span>
                     <span class="info-value">{{ messages.length }}</span>
                  </div>
               </div>
            </div>
            
            <!-- Current Avatar Actions -->
            <div class="action-section" v-if="selectedAvatarId">
               <div class="section-title">当前形象</div>
               <div class="avatar-quick-info">
                  <div class="avatar-preview-mini">
                     <img 
                       v-if="getCurrentAvatar()?.avatar" 
                       :src="getCurrentAvatar()?.avatar" 
                       alt="形象预览"
                       @error="handleImageError"
                     />
                     <div v-else class="mini-placeholder">{{ (getCurrentAvatarName() || 'A').charAt(0) }}</div>
                  </div>
                  <div class="avatar-mini-info">
                     <div class="avatar-mini-name">{{ getCurrentAvatarName() }}</div>
                     <div class="avatar-mini-meta">{{ getStyleName(currentStyle) }}</div>
                  </div>
               </div>
               <div class="action-list">
                  <button 
                     class="action-button primary-action" 
                     @click="openCurrentAvatarSettings"
                  >
                     <el-icon class="action-icon"><Setting /></el-icon>
                     <span>调整形象设置</span>
                  </button>
               </div>
            </div>
            
            <!-- Role Actions -->
            <div class="action-section">
               <div class="section-title">形象管理</div>
               <div class="action-list">
                  <!-- <button 
                     class="action-button" 
                     @click="showCreateAvatarDialog = true"
                     :disabled="!selectedRoleId"
                  >
                     <el-icon class="action-icon"><Plus /></el-icon>
                     <span>创建新形象</span>
                  </button> -->
                  <button 
                     class="action-button" 
                     @click="handleRenameAvatar"
                     :disabled="!selectedAvatarId"
                  >
                     <el-icon class="action-icon"><Edit /></el-icon>
                     <span>重命名形象</span>
                  </button>
                  <button 
                     class="action-button danger-action" 
                     @click="handleDeleteCurrentAvatar"
                     :disabled="!selectedAvatarId"
                  >
                     <el-icon class="action-icon"><Delete /></el-icon>
                     <span>删除当前形象</span>
                  </button>
               </div>
            </div>
            
            <!-- Session Actions -->
            <div class="action-section">
               <div class="section-title">会话操作</div>
               <div class="action-list">
                  <button class="action-button" @click="exportConversation">
                     <el-icon class="action-icon"><Download /></el-icon>
                     <span>导出对话</span>
                  </button>
                  <button class="action-button" @click="clearConversation">
                     <el-icon class="action-icon"><Delete /></el-icon>
                     <span>清空历史</span>
                  </button>
               </div>
            </div>
         </div>
      </aside>
    </div>

    <!-- Dialogs -->
    <CreateRoleDialog v-model="showCreateDialog" @created="handleRoleCreated" />
    
    <!-- Avatar Settings Panel -->
    <AvatarSettingsPanel
      v-model="showAvatarSettings"
      :avatar-id="currentAvatarSettings?.avatar_id"
      :avatar-name="currentAvatarSettings?.name"
      :initial-settings="currentAvatarSettings ? avatarSettings[currentAvatarSettings.avatar_id] : null"
      @settings-changed="handleAvatarSettingsChanged"
      @save="handleAvatarSettingsSave"
    />
    
    <!-- Create Avatar Dialog -->
    <el-dialog 
      v-model="showCreateAvatarDialog" 
      title="创建数字人形象" 
      width="600px"
      class="premium-dialog"
    >
      <div class="create-avatar-form">
        <el-form :model="newAvatarForm" label-width="100px">
          <el-form-item label="形象名称">
            <el-input v-model="newAvatarForm.name" placeholder="输入形象名称" />
          </el-form-item>
          <el-form-item label="形象描述">
            <el-input 
              v-model="newAvatarForm.description" 
              type="textarea" 
              :rows="3"
              placeholder="描述这个形象的特点"
            />
          </el-form-item>
          <el-form-item label="风格">
            <el-radio-group v-model="newAvatarForm.style">
              <el-radio label="realistic">写实</el-radio>
              <el-radio label="cartoon">卡通</el-radio>
              <el-radio label="anime">二次元</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="个性">
            <el-input v-model="newAvatarForm.personality" placeholder="例如：温柔、活泼、专业" />
          </el-form-item>
          <el-form-item label="职业">
            <el-input v-model="newAvatarForm.profession" placeholder="例如：教师、医生、设计师" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showCreateAvatarDialog = false">取消</el-button>
          <el-button type="primary" @click="handleCreateAvatar" :loading="creatingAvatar">
            创建
          </el-button>
        </div>
      </template>
    </el-dialog>
    
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
  Download, Delete, ArrowRight, ChatLineRound, Edit, Check
} from '@element-plus/icons-vue'
import AvatarSettingsPanel from '@/components/AvatarSettingsPanel.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import DigitalHuman from '@/components/DigitalHuman.vue'
import CreateRoleDialog from '@/components/CreateRoleDialog.vue'
import { useRoleStore } from '@/stores/role'
import { useChatStore } from '@/stores/chat'
import { chatApi } from '@/services/api/chat'
import { voiceApi } from '@/services/api/voice'
import { digitalHumanApi } from '@/services/api/digitalHuman'

const roleStore = useRoleStore()
const chatStore = useChatStore()

// State
const searchKeyword = ref('')
const selectedRoleId = ref<string | null>(null)
const selectedAvatarId = ref<string | null>(null)  // 当前选中的形象ID
const roleAvatars = ref<Record<string, any[]>>({})  // 每个角色的形象列表
const loadingAvatars = ref<Record<string, boolean>>({})  // 加载状态
const inputText = ref('')
const loading = ref(false)
const isSpeaking = ref(false)
const currentAudioUrl = ref('')
const currentStyle = ref('realistic')
const showCreateDialog = ref(false)
const showCreateAvatarDialog = ref(false)  // 创建形象对话框
const creatingAvatar = ref(false)  // 创建形象中
const newAvatarForm = ref({
  name: '',
  description: '',
  style: 'realistic',
  personality: '',
  profession: ''
})
const showAvatarSettings = ref(false)  // 形象设置面板
const currentAvatarSettings = ref<any>(null)  // 当前形象设置
const avatarSettings = ref<Record<string, any>>({})  // 所有形象的设置
const showSettings = ref(false)
const showExportDialog = ref(false)
const exportFormat = ref<'json' | 'txt'>('txt')
const messagesContainer = ref<HTMLElement>()

// Config State (Visuals)
const dhScale = ref(100)
const previewBackground = ref('#f8fafc')
const bubbleStyle = ref('default')
const isRecording = ref(false)
const renderQuality = ref('medium')

// Style Options
const styleOptions = [
  { id: 'realistic', name: '写实', icon: null, desc: '极其写实，如同真实人类一般。' },
  { id: 'cartoon', name: '卡通', icon: null, desc: '清新可爱，适合日常交流。' },
  { id: 'anime', name: '二次元', icon: null, desc: '充满艺术感，深受年轻用户喜爱。' }
]

const qualityHint = computed(() => {
  if (renderQuality.value === 'low') return '低功耗模式，保持基本流畅'
  if (renderQuality.value === 'medium') return '平衡性能与画质'
  return '极致细节，对设备性能有要求'
})

const currentStyleDesc = computed(() => {
  return styleOptions.find(s => s.id === currentStyle.value)?.desc || ''
})

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
const selectRole = async (role: any) => {
  selectedRoleId.value = role.id
  selectedAvatarId.value = null
  roleStore.setCurrentRole(role)
  
  // 加载该角色的所有形象
  await loadRoleAvatars(role.id)
}

const loadRoleAvatars = async (roleId: string) => {
  if (loadingAvatars.value[roleId]) return
  
  loadingAvatars.value[roleId] = true
  try {
    const response = await digitalHumanApi.listRoleAvatars(roleId)
    if (response.success && response.data) {
      roleAvatars.value[roleId] = response.data
      // 如果有形象，默认选择第一个
      if (response.data.length > 0 && !selectedAvatarId.value) {
        selectedAvatarId.value = response.data[0].avatar_id
      }
    } else {
      roleAvatars.value[roleId] = []
    }
  } catch (error) {
    console.error('加载形象列表失败:', error)
    roleAvatars.value[roleId] = []
  } finally {
    loadingAvatars.value[roleId] = false
  }
}

const selectAvatar = async (avatar: any) => {
  selectedAvatarId.value = avatar.avatar_id
  currentStyle.value = avatar.style || 'realistic'
  
  // 加载并应用该形象的设置
  await loadAndApplyAvatarSettings(avatar)
}

const loadAndApplyAvatarSettings = async (avatar: any) => {
  try {
    // 从avatar数据中获取设置（如果存在）
    let settings = avatar.display_settings
    
    // 如果没有设置，使用默认值
    if (!settings) {
      settings = {
        colors: {
          primary: '#409EFF',
          secondary: '#79bbff',
          accent: '#95d475'
        },
        scale: 100,
        background: {
          color: '#f8fafc',
          opacity: 100
        },
        position: {
          x: 0,
          y: 0
        },
        rotation: 0,
        opacity: 100
      }
    }
    
    // 保存到本地状态
    avatarSettings.value[avatar.avatar_id] = settings
    
    // 立即应用到预览
    applyAvatarSettings(settings)
    
    // 提示用户
    ElMessage.success({
      message: `已切换到形象：${avatar.name || '未命名'}`,
      duration: 1500
    })
  } catch (error) {
    console.error('加载形象设置失败:', error)
  }
}

const deleteAvatar = async (avatarId: string) => {
  try {
    const response = await digitalHumanApi.deleteAvatar(avatarId)
    if (response.success) {
      ElMessage.success('形象删除成功')
      // 重新加载形象列表
      if (selectedRoleId.value) {
        await loadRoleAvatars(selectedRoleId.value)
      }
    } else {
      ElMessage.error('删除失败')
    }
  } catch (error) {
    console.error('删除形象失败:', error)
    ElMessage.error('删除失败')
  }
}

const showCreateAvatarForRole = (role: any) => {
  selectedRoleId.value = role.id
  showCreateAvatarDialog.value = true
}

const handleImageError = (event: any) => {
  event.target.style.display = 'none'
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  } catch {
    return dateStr
  }
}

const handleCreateAvatar = async () => {
  if (!selectedRoleId.value) {
    ElMessage.warning('请先选择角色')
    return
  }
  
  creatingAvatar.value = true
  try {
    const response = await digitalHumanApi.createDigitalHuman({
      roleId: selectedRoleId.value,
      name: newAvatarForm.value.name || undefined,
      description: newAvatarForm.value.description || undefined,
      style: newAvatarForm.value.style,
      personality: newAvatarForm.value.personality || undefined,
      profession: newAvatarForm.value.profession || undefined
    })
    
    if (response.success && response.data) {
      ElMessage.success('形象创建成功')
      showCreateAvatarDialog.value = false
      // 重置表单
      newAvatarForm.value = {
        name: '',
        description: '',
        style: 'realistic',
        personality: '',
        profession: ''
      }
      // 重新加载形象列表
      await loadRoleAvatars(selectedRoleId.value)
      // 选择新创建的形象并加载设置
      if (response.data.avatar_id) {
        selectedAvatarId.value = response.data.avatar_id
        // 等待形象列表加载完成后再加载设置
        await nextTick()
        const avatars = roleAvatars.value[selectedRoleId.value] || []
        const newAvatar = avatars.find((a: any) => a.avatar_id === response.data.avatar_id)
        if (newAvatar) {
          await loadAndApplyAvatarSettings(newAvatar)
        }
      }
    } else {
      ElMessage.error('创建失败')
    }
  } catch (error: any) {
    console.error('创建形象失败:', error)
    ElMessage.error(error.message || '创建失败')
  } finally {
    creatingAvatar.value = false
  }
}

const openAvatarSettings = async (avatar: any) => {
  currentAvatarSettings.value = avatar
  
  // 加载形象的设置（优先使用avatar数据中的设置）
  let settings = avatar.display_settings || avatarSettings.value[avatar.avatar_id]
  
  // 如果没有设置，使用默认值
  if (!settings) {
    settings = {
      colors: {
        primary: '#409EFF',
        secondary: '#79bbff',
        accent: '#95d475'
      },
      scale: 100,
      background: {
        color: '#f8fafc',
        opacity: 100
      },
      position: {
        x: 0,
        y: 0
      },
      rotation: 0,
      opacity: 100
    }
  }
  
  // 保存到本地状态
  avatarSettings.value[avatar.avatar_id] = settings
  
  // 打开设置面板
  showAvatarSettings.value = true
}

const handleAvatarSettingsChanged = (settings: any) => {
  if (currentAvatarSettings.value?.avatar_id) {
    avatarSettings.value[currentAvatarSettings.value.avatar_id] = settings
    // 实时应用设置到预览（仅当前选中的形象）
    if (selectedAvatarId.value === currentAvatarSettings.value.avatar_id) {
      applyAvatarSettings(settings)
    }
  }
}

const handleAvatarSettingsSave = async (settings: any) => {
  if (!currentAvatarSettings.value?.avatar_id) {
    ElMessage.warning('请先选择形象')
    return
  }
  
  try {
    // 保存到本地状态
    avatarSettings.value[currentAvatarSettings.value.avatar_id] = settings
    
    // 调用API保存到后端
    const response = await digitalHumanApi.updateAvatarSettings(
      currentAvatarSettings.value.avatar_id,
      settings
    )
    
    if (response.success) {
      ElMessage.success('设置已保存')
      
      // 如果当前选中的是这个形象，立即应用设置
      if (selectedAvatarId.value === currentAvatarSettings.value.avatar_id) {
        applyAvatarSettings(settings)
      }
      
      // 更新形象列表中的设置
      const roleId = currentAvatarSettings.value.role_id
      if (roleId && roleAvatars.value[roleId]) {
        const avatar = roleAvatars.value[roleId].find(
          (a: any) => a.avatar_id === currentAvatarSettings.value.avatar_id
        )
        if (avatar) {
          avatar.display_settings = settings
        }
      }
    } else {
      ElMessage.error('保存失败')
    }
  } catch (error: any) {
    console.error('保存形象设置失败:', error)
    ElMessage.error(error.message || '保存失败')
  }
}

const applyAvatarSettings = (settings: any) => {
  // 应用设置到数字人预览（仅应用形象相关的设置，预览背景保持独立）
  if (settings) {
    // 形象大小（影响数字人本身）
    // 注意：这里不直接修改dhScale，因为dhScale是预览设置
    // 形象的大小设置应该在形象设置面板中调整
    // 如果需要，可以通过props传递给DigitalHuman组件
  }
}

const handlePreviewScaleChange = () => {
  // 预览大小改变时的处理（这是全局预览设置，不影响形象本身）
  // 可以在这里添加实时预览更新逻辑
}

const getCurrentAvatarName = () => {
  if (!selectedRoleId.value || !selectedAvatarId.value) return ''
  const avatars = roleAvatars.value[selectedRoleId.value] || []
  const avatar = avatars.find((a: any) => a.avatar_id === selectedAvatarId.value)
  return avatar?.name || `形象_${selectedAvatarId.value.substring(0, 8)}`
}

const getAvatarWrapperStyle = () => {
  const style: any = {
    transform: `scale(${dhScale.value / 100})`
  }
  
  // 如果有当前形象的设置，应用位置和旋转
  if (selectedAvatarId.value && avatarSettings.value[selectedAvatarId.value]) {
    const settings = avatarSettings.value[selectedAvatarId.value]
    if (settings.position) {
      style.transform += ` translate(${settings.position.x}%, ${settings.position.y}%)`
    }
    if (settings.rotation) {
      style.transform += ` rotate(${settings.rotation}deg)`
    }
    if (settings.opacity !== undefined) {
      style.opacity = settings.opacity / 100
    }
  }
  
  return style
}

const getCurrentAvatar = () => {
  if (!selectedRoleId.value || !selectedAvatarId.value) return null
  const avatars = roleAvatars.value[selectedRoleId.value] || []
  return avatars.find((a: any) => a.avatar_id === selectedAvatarId.value)
}

const openCurrentAvatarSettings = () => {
  const avatar = getCurrentAvatar()
  if (avatar) {
    openAvatarSettings(avatar)
  } else {
    ElMessage.warning('请先选择形象')
  }
}

const handleRenameAvatar = async () => {
  const avatar = getCurrentAvatar()
  if (!avatar) {
    ElMessage.warning('请先选择形象')
    return
  }
  
  ElMessageBox.prompt('请输入新的形象名称', '重命名形象', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputValue: avatar.name || '',
    inputPlaceholder: '输入形象名称'
  }).then(async ({ value }) => {
    if (value && value.trim()) {
      // 更新形象名称
      avatar.name = value.trim()
      // 保存到后端
      try {
        const response = await digitalHumanApi.updateAvatarSettings(avatar.avatar_id, {
          ...avatar.display_settings,
          name: value.trim()
        })
        if (response.success) {
          ElMessage.success('重命名成功')
          // 重新加载形象列表
          if (selectedRoleId.value) {
            await loadRoleAvatars(selectedRoleId.value)
          }
        }
      } catch (error) {
        ElMessage.error('重命名失败')
      }
    }
  }).catch(() => {
    // 取消操作
  })
}

const handleDeleteCurrentAvatar = async () => {
  const avatar = getCurrentAvatar()
  if (!avatar) {
    ElMessage.warning('请先选择形象')
    return
  }
  
  ElMessageBox.confirm(
    `确定要删除形象 "${avatar.name || '未命名'}" 吗？此操作不可恢复。`,
    '确认删除',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    await deleteAvatar(avatar.avatar_id)
  }).catch(() => {
    // 取消操作
  })
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

const getStyleName = (style: string) => {
  const styleMap: Record<string, string> = {
    'realistic': '写实',
    'cartoon': '卡通',
    'anime': '二次元'
  }
  return styleMap[style] || style
}

// 处理画质级别变化
const handleQualityChange = async () => {
  try {
    // 通知 DigitalHuman 组件更新画质
    ElMessage.success({
      message: `画质已切换为：${renderQuality.value === 'low' ? '低' : renderQuality.value === 'medium' ? '中' : '高'}`,
      duration: 2000
    })
    // 这里可以触发重新渲染或更新渲染器设置
    // 实际实现需要与 DigitalHuman 组件通信
  } catch (error) {
    console.error('切换画质失败:', error)
  }
}

// 注意：风格切换功能已移除，因为风格是形象创建时的属性
// 如果需要不同风格，应该创建新的形象

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
  position: relative;
}

.main-layout {
  display: grid;
  grid-template-columns: 280px 1fr 320px;
  height: 100%;
  gap: 0;
}

.left-panel,
.center-stage,
.right-panel {
  min-width: 0;
}

/* --- Left Panel --- */
.left-panel {
  background: #ffffff;
  border-right: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 24px 20px;
  border-bottom: 1px solid var(--border-light);
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
  letter-spacing: -0.01em;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
}

.panel-subtitle {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
  font-weight: 400;
  letter-spacing: 0.01em;
}

.search-section {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-light);
}

.search-wrapper {
  display: flex;
  align-items: center;
  background: var(--bg-input);
  padding: 10px 14px;
  border-radius: 10px;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.search-wrapper:focus-within {
  background: #ffffff;
  border-color: var(--border-hover);
}

.search-icon {
  color: var(--text-secondary);
  font-size: 16px;
}

.clean-input {
  border: none;
  background: transparent;
  width: 100%;
  margin-left: 10px;
  outline: none;
  font-family: var(--font-sans);
  font-size: 14px;
  color: var(--text-primary);
}

.clean-input::placeholder {
  color: var(--text-disabled);
}

.role-scroll-area {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 12px 20px;
  /* 优化滚动条样式 */
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.2) transparent;
}

.role-scroll-area::-webkit-scrollbar {
  width: 6px;
}

.role-scroll-area::-webkit-scrollbar-track {
  background: transparent;
}

.role-scroll-area::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.role-scroll-area::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

.role-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.role-item-wrapper {
  margin-bottom: 8px;
}

.role-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  background: transparent;
}

.avatar-list {
  margin-top: 8px;
  padding-left: 52px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.avatar-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  background: rgba(0, 0, 0, 0.02);
}

.avatar-item:hover {
  background: rgba(0, 0, 0, 0.04);
  border-color: rgba(79, 70, 229, 0.2);
}

.avatar-item.active {
  background: rgba(79, 70, 229, 0.08);
  border-color: rgba(79, 70, 229, 0.3);
}

.avatar-thumbnail {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  overflow: hidden;
  margin-right: 10px;
  flex-shrink: 0;
  background: rgba(0, 0, 0, 0.05);
}

.avatar-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.4);
}

.avatar-info {
  flex: 1;
  min-width: 0;
}

.avatar-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.avatar-meta {
  font-size: 11px;
  color: var(--text-secondary);
}

.avatar-status {
  margin-left: auto;
  flex-shrink: 0;
  padding-left: 8px;
}

.status-icon {
  font-size: 18px;
  color: var(--primary-color);
}

.avatar-list-actions {
  padding: 8px 12px 4px;
  border-top: 1px dashed rgba(0, 0, 0, 0.08);
  margin-top: 4px;
}

.add-avatar-btn {
  width: 100%;
  justify-content: center;
  color: var(--text-secondary);
  font-size: 13px;
  padding: 6px 12px;
  
  &:hover {
    color: var(--primary-color);
    background: rgba(79, 70, 229, 0.05);
  }
}

.avatar-loading,
.avatar-empty {
  padding: 16px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 13px;
  padding-left: 52px;
}

.avatar-empty p {
  margin: 0 0 8px 0;
}

.create-avatar-form {
  padding: 8px 0;
}

.role-item:hover {
  background: var(--bg-input);
}

.role-item.active {
  background: var(--primary-fade);
  border-color: var(--primary-color);
}

.role-avatar-wrapper {
  margin-right: 12px;
  flex-shrink: 0;
}

.role-info {
  flex: 1;
  min-width: 0;
}

.role-name {
  font-weight: 500;
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-desc {
  font-size: 12px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-badge {
  margin-left: auto;
  margin-right: 8px;
  flex-shrink: 0;
}

.badge-count {
  display: inline-block;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background: rgba(79, 70, 229, 0.1);
  color: var(--primary-color);
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  line-height: 20px;
  text-align: center;
  border: 1px solid rgba(79, 70, 229, 0.2);
}

.role-item.active .badge-count {
  background: var(--primary-color);
  color: #ffffff;
  border-color: var(--primary-color);
}

.role-action {
  margin-left: 0;
  color: var(--text-disabled);
  transition: color 0.2s;
  flex-shrink: 0;
}

.role-item:hover .role-action,
.role-item.active .role-action {
  color: var(--primary-color);
}

.action-icon {
  font-size: 16px;
}

.create-section {
  padding: 20px;
  border-top: 1px solid var(--border-light);
}

.create-btn {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-light);
  background: #ffffff;
  color: var(--text-primary);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
  font-size: 14px;
}

.create-btn:hover {
  background: var(--bg-input);
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.create-icon {
  font-size: 18px;
}

.create-label {
  font-size: 14px;
}

/* --- Center Stage --- */
.center-stage {
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-left: 1px solid var(--border-light);
  border-right: 1px solid var(--border-light);
}

.preview-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 400px;
  border-bottom: 1px solid var(--border-light);
}

.preview-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.preview-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.01em;
}

.preview-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.status-dot-animated {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--success);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-size: 13px;
}

.preview-container {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  transition: background-color 0.3s ease;
}

.dh-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s ease, opacity 0.3s ease;
  transform-origin: center center;
}

.chat-section {
  height: 45%;
  display: flex;
  flex-direction: column;
  background: #ffffff;
}

.chat-header {
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-light);
}

.chat-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
  letter-spacing: -0.01em;
}

.chat-subtitle {
  font-size: 12px;
  color: var(--text-secondary);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  /* 优化滚动条样式 */
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.2) transparent;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

.message-item {
  display: flex;
  flex-direction: column;
  max-width: 75%;
  gap: 4px;
}

.message-item.user {
  align-self: flex-end;
  align-items: flex-end;
}

.message-item.assistant {
  align-self: flex-start;
  align-items: flex-start;
}

.message-content {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  word-wrap: break-word;
}

.message-content.user {
  background: var(--primary-color);
  color: #ffffff;
  border-bottom-right-radius: 4px;
}

.message-content.assistant {
  background: var(--bg-input);
  color: var(--text-primary);
  border-bottom-left-radius: 4px;
}

.message-time {
  font-size: 11px;
  color: var(--text-disabled);
  padding: 0 4px;
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--text-disabled);
  gap: 12px;
}

.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.empty-text {
  font-size: 14px;
  margin: 0;
}

.input-area {
  padding: 16px 24px;
  border-top: 1px solid var(--border-light);
}

.input-container {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-input);
  padding: 8px;
  border-radius: 12px;
  border: 1px solid var(--border-light);
  transition: all 0.2s ease;
}

.input-container:focus-within {
  background: #ffffff;
  border-color: var(--primary-color);
}

.voice-button {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.voice-button:hover {
  background: rgba(0, 0, 0, 0.05);
  color: var(--text-primary);
}

.voice-button.recording {
  color: var(--danger);
  background: rgba(220, 38, 38, 0.1);
}

.message-input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 0 12px;
  outline: none;
  font-size: 14px;
  font-family: var(--font-sans);
  color: var(--text-primary);
  line-height: 1.5;
}

.message-input::placeholder {
  color: var(--text-disabled);
}

.send-button {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--primary-color);
  color: #ffffff;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.send-button:hover:not(:disabled) {
  background: var(--primary-hover);
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* --- Right Panel --- */
.right-panel {
  background: #ffffff;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.config-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  gap: 24px;
  /* 优化滚动条样式 */
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.2) transparent;
}

.config-content::-webkit-scrollbar {
  width: 6px;
}

.config-content::-webkit-scrollbar-track {
  background: transparent;
}

.config-content::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.config-content::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

.config-section,
.info-section,
.action-section {
  display: flex;
  flex-direction: column;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
  letter-spacing: -0.01em;
}

.control-item {
  margin-bottom: 20px;
}

.control-item:last-child {
  margin-bottom: 0;
}

.control-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.control-value {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 8px;
  text-align: right;
}

.color-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.color-option {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s ease;
  position: relative;
}

.color-option:hover {
  transform: scale(1.05);
}

.color-option.active {
  border-color: var(--primary-color);
}

.color-option.active::after {
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: var(--primary-color);
  font-size: 14px;
  font-weight: 600;
}

/* 画质级别样式 */
.quality-radio-group {
  width: 100%;
  display: flex;
  gap: 8px;
}

.quality-radio-group :deep(.el-radio-button) {
  flex: 1;
}

.quality-radio-group :deep(.el-radio-button + .el-radio-button) {
  margin-left: 0;
}

.quality-radio-group :deep(.el-radio-button__inner) {
  width: 100%;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  transition: all 0.2s ease;
  margin-left: 0 !important;
  border-left: 1px solid var(--border-light) !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quality-radio-group :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: var(--primary-color);
  border-color: var(--primary-color);
  color: white;
}

.control-hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 8px;
  line-height: 1.5;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 6px;
}

/* 展示风格网格 */
.style-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 8px;
}

.style-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px 8px;
  border-radius: 10px;
  border: 2px solid var(--border-light);
  background: var(--bg-input);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.style-option:hover {
  border-color: var(--primary-color);
  background: rgba(79, 70, 229, 0.05);
}

.style-option.active {
  border-color: var(--primary-color);
  background: rgba(79, 70, 229, 0.1);
}

.style-option.active::after {
  content: '✓';
  position: absolute;
  top: 4px;
  right: 4px;
  width: 18px;
  height: 18px;
  background: var(--primary-color);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.style-preview {
  width: 56px;
  height: 56px;
  border-radius: 10px;
  background: rgba(79, 70, 229, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(79, 70, 229, 0.2);
  transition: all 0.2s ease;
}

.style-option.active .style-preview {
  background: rgba(79, 70, 229, 0.15);
  border-color: var(--primary-color);
}

.style-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 600;
  color: var(--primary-color);
  background: rgba(79, 70, 229, 0.08);
  border-radius: 10px;
}

.style-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
  text-align: center;
}

.style-option.active .style-name {
  color: var(--primary-color);
  font-weight: 600;
}

/* Style Display (Read-only) */
.style-display {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.style-badge {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  text-align: center;
  background: rgba(79, 70, 229, 0.1);
  color: var(--primary-color);
  border: 1px solid rgba(79, 70, 229, 0.2);
}

.style-badge.style-realistic {
  background: rgba(79, 70, 229, 0.1);
  color: var(--primary-color);
}

.style-badge.style-cartoon {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.2);
}

.style-badge.style-anime {
  background: rgba(236, 72, 153, 0.1);
  color: #ec4899;
  border-color: rgba(236, 72, 153, 0.2);
}

.info-card {
  padding: 16px;
  border-radius: 12px;
  background: var(--bg-input);
  border: 1px solid var(--border-light);
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  font-size: 13px;
}

.info-item:not(:last-child) {
  border-bottom: 1px solid var(--border-light);
}

.info-label {
  color: var(--text-secondary);
  font-weight: 400;
}

.info-value {
  color: var(--text-primary);
  font-weight: 500;
}

.action-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-button {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--border-light);
  background: #ffffff;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  color: var(--text-primary);
  transition: all 0.2s ease;
  font-size: 14px;
  font-weight: 500;
}

.action-button:hover:not(:disabled) {
  background: var(--bg-input);
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.action-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-button.primary-action {
  background: var(--primary-color);
  color: #ffffff;
  border-color: var(--primary-color);
}

.action-button.primary-action:hover:not(:disabled) {
  background: var(--primary-hover);
  border-color: var(--primary-hover);
}

.action-button.danger-action:hover:not(:disabled) {
  background: rgba(220, 38, 38, 0.05);
  border-color: #dc2626;
  color: #dc2626;
}

.action-icon {
  font-size: 16px;
}

/* Avatar Quick Info */
.avatar-quick-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-input);
  border-radius: 10px;
  margin-bottom: 12px;
}

.avatar-preview-mini {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
}

.avatar-preview-mini img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.mini-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.3);
}

.avatar-mini-info {
  flex: 1;
  min-width: 0;
}

.avatar-mini-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 2px;
}

.avatar-mini-meta {
  font-size: 12px;
  color: var(--text-secondary);
}

/* Dialog Styles */
.export-options {
   display: grid;
   grid-template-columns: 1fr 1fr;
   gap: 12px;
   padding: 16px 0;
}

.export-card {
   border: 1px solid var(--border-light);
   border-radius: 12px;
   padding: 20px;
   text-align: center;
   cursor: pointer;
   transition: all 0.2s ease;
   background: #ffffff;
}

.export-card:hover {
   border-color: var(--primary-color);
   background: var(--bg-input);
}

.export-card.active {
   background: var(--primary-fade);
   border-color: var(--primary-color);
}

.export-card .icon {
   font-weight: 600;
   font-size: 16px;
   margin-bottom: 8px;
   color: var(--text-primary);
}

.dialog-footer {
   display: flex;
   justify-content: flex-end;
   gap: 12px;
   margin-top: 20px;
}
</style>
