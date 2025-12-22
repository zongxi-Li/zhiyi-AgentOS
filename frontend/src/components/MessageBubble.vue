<template>
  <div :class="['message-bubble', message.role]">
    <div class="message-avatar">
      <el-avatar :size="40">
        {{ message.role === 'user' ? '我' : roleName }}
      </el-avatar>
    </div>
    <div class="message-content-wrapper">
      <div class="message-content">
        <div v-if="message.fileUrl" class="message-file">
          <el-image
            v-if="isImage(message.fileUrl)"
            :src="message.fileUrl"
            fit="cover"
            style="max-width: 300px; max-height: 300px; border-radius: 8px"
            :preview-src-list="[message.fileUrl]"
          />
          <div v-else class="file-attachment">
            <el-icon><Document /></el-icon>
            <a :href="message.fileUrl" target="_blank">查看文件</a>
          </div>
        </div>
        <div v-if="message.content" class="message-text">{{ message.content }}</div>
        <div v-if="message.role === 'assistant' && message.confidence" class="message-confidence">
          置信度: {{ (message.confidence * 100).toFixed(1) }}%
        </div>
      </div>
      <div class="message-time">{{ formatTime(message.createdAt) }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Document } from '@element-plus/icons-vue'
import { useRoleStore } from '@/stores/role'

interface Props {
  message: {
    id: number | string
    role: 'user' | 'assistant'
    content: string
    createdAt: Date
    confidence?: number
    fileUrl?: string
  }
}

const props = defineProps<Props>()
const roleStore = useRoleStore()

const roleName = computed(() => {
  return roleStore.currentRole?.name || 'AI'
})

const isImage = (url: string) => {
  const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
  return imageExtensions.some(ext => url.toLowerCase().includes(ext))
}

const formatTime = (date: Date) => {
  const d = new Date(date)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  
  return d.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.message-bubble {
  display: flex;
  margin-bottom: 20px;
  gap: 12px;
}

.message-bubble.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.message-content-wrapper {
  max-width: 70%;
  min-width: 100px;
}

.message-bubble.user .message-content-wrapper {
  text-align: right;
}

.message-content {
  padding: 12px 16px;
  border-radius: 12px;
  word-wrap: break-word;
  line-height: 1.5;
}

.message-bubble.user .message-content {
  background: #409eff;
  color: white;
}

.message-bubble.assistant .message-content {
  background: white;
  color: #303133;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.message-file {
  margin-bottom: 8px;
}

.file-attachment {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.message-text {
  white-space: pre-wrap;
}

.message-confidence {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
  padding: 0 4px;
}
</style>
