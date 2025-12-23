<template>
  <div :class="['message-bubble', message.role]">
    <div class="message-avatar">
      <el-avatar :size="36" shape="square" :src="roleAvatar">
        {{ message.role === 'user' ? 'Me' : roleName?.charAt(0) }}
      </el-avatar>
    </div>
    <div class="message-content-wrapper">
      <div class="message-meta">
        <span class="sender-name">{{ message.role === 'user' ? '你' : roleName }}</span>
        <span class="message-time">{{ formatTime(message.createdAt) }}</span>
      </div>
      
      <div class="message-content">
        <!-- 文件展示 -->
        <div v-if="message.fileUrl" class="message-file">
          <el-image
            v-if="isImage(message.fileUrl)"
            :src="message.fileUrl"
            fit="cover"
            class="message-image"
            :preview-src-list="[message.fileUrl]"
          />
          <div v-else class="file-attachment">
            <el-icon><Document /></el-icon>
            <div class="file-info">
              <span class="filename">附件文件</span>
              <a :href="message.fileUrl" target="_blank" class="download-link">下载</a>
            </div>
          </div>
        </div>

        <!-- 文本内容 -->
        <div v-if="message.content" class="message-text">{{ message.content }}</div>
        
        <!-- 可解释性信息（仅AI回复显示） -->
        <div v-if="message.role === 'assistant' && hasExplanation" class="message-explanation">
          <el-collapse v-model="activeCollapse" class="explanation-collapse">
            <el-collapse-item name="explanation">
              <template #title>
                <div class="explanation-toggle">
                  <el-icon><InfoFilled /></el-icon>
                  <span>AI 思考过程与详情</span>
                </div>
              </template>
              
              <!-- 置信度 -->
              <div v-if="message.confidence" class="explanation-item">
                <span class="explanation-label">置信度</span>
                <div class="explanation-value-row">
                  <el-progress
                    :percentage="(message.confidence * 100)"
                    :color="getConfidenceColor(message.confidence)"
                    :stroke-width="6"
                    :show-text="false"
                    style="width: 100px;"
                  />
                  <span class="value-text">{{ (message.confidence * 100).toFixed(1) }}%</span>
                </div>
              </div>
              
              <!-- Token使用 -->
              <div v-if="message.tokensUsed" class="explanation-item">
                <span class="explanation-label">消耗</span>
                <span class="explanation-value">{{ message.tokensUsed }} tokens</span>
              </div>
              
              <!-- 答案来源（RAG） -->
              <div v-if="message.sources && message.sources.length > 0" class="explanation-item vertical">
                <span class="explanation-label">参考来源</span>
                <div class="sources-list">
                  <div
                    v-for="(source, index) in message.sources"
                    :key="index"
                    class="source-tag"
                  >
                    <el-icon><Link /></el-icon>
                    {{ source.title || source.filename || `来源 ${index + 1}` }}
                  </div>
                </div>
              </div>
              
              <!-- 推理路径 -->
              <div v-if="message.reasoningPath" class="explanation-item vertical">
                <span class="explanation-label">推理路径</span>
                <div class="reasoning-path">
                  <div v-for="(step, index) in message.reasoningPath" :key="index" class="reasoning-step">
                    <div class="step-dot"></div>
                    <div class="step-content">
                      <div class="step-title">{{ step.title }}</div>
                      <div class="step-desc">{{ step.description }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Document, InfoFilled, Link } from '@element-plus/icons-vue'
import { useRoleStore } from '@/stores/role'

interface Source {
  title?: string
  filename?: string
  url?: string
  content?: string
}

interface ReasoningStep {
  title: string
  description: string
}

interface Props {
  message: {
    id: number | string
    role: 'user' | 'assistant'
    content: string
    createdAt: Date
    confidence?: number
    fileUrl?: string
    tokensUsed?: number
    sources?: Source[]
    reasoningPath?: ReasoningStep[]
    modelInfo?: string
  }
}

const props = defineProps<Props>()
const roleStore = useRoleStore()
const activeCollapse = ref<string[]>([])

const roleName = computed(() => {
  return roleStore.currentRole?.name || 'Assistant'
})

const roleAvatar = computed(() => {
  return props.message.role === 'assistant' ? roleStore.currentRole?.avatar : undefined
})

const hasExplanation = computed(() => {
  return !!(
    props.message.confidence ||
    props.message.tokensUsed ||
    (props.message.sources && props.message.sources.length > 0) ||
    (props.message.reasoningPath && props.message.reasoningPath.length > 0) ||
    props.message.modelInfo
  )
})

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return 'var(--success-color)'
  if (confidence >= 0.6) return 'var(--warning-color)'
  return 'var(--danger-color)'
}

const isImage = (url: string) => {
  const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
  return imageExtensions.some(ext => url.toLowerCase().includes(ext))
}

const formatTime = (date: Date) => {
  const d = new Date(date)
  return d.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped lang="scss">
.message-bubble {
  display: flex;
  margin-bottom: 24px;
  gap: 16px;
  animation: fadeIn 0.3s ease-out;
  padding: 0 16px;
}

.message-bubble.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
  margin-top: 2px;
}

.message-content-wrapper {
  max-width: 75%;
  min-width: 120px;
  display: flex;
  flex-direction: column;
}

.message-bubble.user .message-content-wrapper {
  align-items: flex-end;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 12px;
  color: var(--text-color-secondary);
}

.message-bubble.user .message-meta {
  flex-direction: row-reverse;
}

.sender-name {
  font-weight: 500;
  color: var(--text-color-primary);
}

.message-content {
  padding: 12px 16px;
  border-radius: 12px;
  word-wrap: break-word;
  line-height: 1.6;
  font-size: 15px;
  position: relative;
  transition: all 0.2s ease;
}

/* User Bubble Style - Solid Primary, No Gradient */
.message-bubble.user .message-content {
  background-color: var(--primary-color);
  color: white;
  border-top-right-radius: 2px;
  box-shadow: var(--box-shadow-base);
}

/* Assistant Bubble Style - White, Bordered */
.message-bubble.assistant .message-content {
  background-color: var(--bg-color);
  color: var(--text-color-primary);
  border: 1px solid var(--border-color-base);
  border-top-left-radius: 2px;
  box-shadow: var(--box-shadow-base);
}

/* File Attachments */
.message-image {
  max-width: 100%;
  border-radius: 8px;
  border: 1px solid rgba(0,0,0,0.1);
}

.file-attachment {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 8px;
}

.message-bubble.assistant .file-attachment {
  background: var(--bg-color-secondary);
  border-color: var(--border-color-base);
}

.message-text {
  white-space: pre-wrap;
}

/* Explanation Section */
.message-explanation {
  margin-top: 12px;
  border-top: 1px solid rgba(0,0,0,0.05);
  padding-top: 8px;
}

.message-bubble.user .message-explanation {
  border-top-color: rgba(255,255,255,0.2);
}

.explanation-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-color-secondary);
  cursor: pointer;
  
  &:hover {
    color: var(--primary-color);
  }
}

.explanation-collapse {
  --el-collapse-header-height: 32px;
  --el-collapse-border-color: transparent;
  
  :deep(.el-collapse-item__header) {
    background: transparent;
    border: none;
    font-size: 13px;
  }
  
  :deep(.el-collapse-item__content) {
    background: transparent;
    padding-bottom: 0;
  }
}

.explanation-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 12px;
  font-size: 13px;
  
  &.vertical {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }
}

.explanation-label {
  color: var(--text-color-secondary);
  font-weight: 500;
  min-width: 60px;
}

.explanation-value-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.value-text {
  font-size: 12px;
  color: var(--text-color-regular);
}

.source-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background-color: var(--bg-color-secondary);
  border-radius: 4px;
  font-size: 12px;
  color: var(--text-color-regular);
  margin-right: 4px;
  margin-bottom: 4px;
  border: 1px solid var(--border-color-light);
}

.reasoning-path {
  padding-left: 8px;
  border-left: 2px solid var(--border-color-light);
  margin-left: 4px;
}

.reasoning-step {
  position: relative;
  padding-bottom: 12px;
  padding-left: 12px;
  
  &:last-child {
    padding-bottom: 0;
  }
  
  .step-dot {
    position: absolute;
    left: -5px;
    top: 6px;
    width: 8px;
    height: 8px;
    background-color: var(--border-color-base);
    border-radius: 50%;
  }
  
  .step-title {
    font-weight: 500;
    font-size: 13px;
    color: var(--text-color-primary);
  }
  
  .step-desc {
    font-size: 12px;
    color: var(--text-color-secondary);
    margin-top: 2px;
  }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
