<template>
  <div class="conversation-list-container">
    <div class="list-content">
      <div
        v-for="conversation in filteredConversations"
        :key="conversation.id"
        class="conversation-item"
        @click="$emit('select', conversation)"
      >
        <div class="item-left">
          <el-avatar 
            :src="conversation.avatar" 
            :size="44" 
            class="avatar"
            :style="{ background: getRandomGradient(conversation.id) }"
          >
            <el-icon v-if="!conversation.avatar"><User /></el-icon>
          </el-avatar>
        </div>
        
        <div class="item-main">
          <div class="item-header">
            <span class="title">{{ conversation.title || '未命名对话' }}</span>
            <span class="time">{{ formatTime(conversation.updatedAt) }}</span>
          </div>
          <div class="item-preview">
            {{ conversation.preview || '暂无预览内容...' }}
          </div>
        </div>
        
        <div class="item-right">
          <el-button circle size="small" class="action-btn">
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
    
    <div v-if="loading" class="loading-state">
      <el-skeleton animated :count="3">
        <template #template>
          <div style="padding: 14px; display: flex; gap: 16px; align-items: center;">
            <el-skeleton-item variant="circle" style="width: 44px; height: 44px" />
            <div style="flex: 1">
              <el-skeleton-item variant="text" style="width: 30%; margin-bottom: 8px" />
              <el-skeleton-item variant="text" style="width: 80%" />
            </div>
          </div>
        </template>
      </el-skeleton>
    </div>
    
    <div v-else-if="filteredConversations.length === 0" class="empty-state">
      <el-empty description="暂无对话历史" :image-size="100" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { User, Loading, ArrowRight } from '@element-plus/icons-vue'
import { conversationApi, type Conversation as ApiConversation } from '@/services/api/conversation'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

interface Conversation {
  id: string
  title?: string
  preview?: string
  avatar?: string
  updatedAt: number | Date
}

interface Props {
  searchKeyword?: string
  userId?: string
}

const props = withDefaults(defineProps<Props>(), {
  searchKeyword: '',
  userId: ''
})

const userStore = useUserStore()

defineEmits<{
  select: [conversation: Conversation]
}>()

const conversations = ref<Conversation[]>([])
const loading = ref(false)

// Generate a consistent gradient based on ID
const getRandomGradient = (id: string) => {
  const hash = id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  const hues = [
    ['#6366f1', '#a855f7'],
    ['#3b82f6', '#06b6d4'],
    ['#f59e0b', '#d97706'],
    ['#ec4899', '#8b5cf6'],
    ['#10b981', '#3b82f6']
  ]
  const [c1, c2] = hues[hash % hues.length]
  return `linear-gradient(135deg, ${c1}, ${c2})`
}

// 从API获取对话列表
const loadConversations = async () => {
  // 优先使用props中的userId，否则从userStore获取
  const userId = props.userId || userStore.currentUser?.id
  
  if (!userId) {
    conversations.value = []
    return
  }

  try {
    loading.value = true
    const apiConversations = await conversationApi.getUserConversations(userId)
    
    // 转换为组件需要的格式
    conversations.value = apiConversations.map(conv => ({
      id: conv.id,
      title: `对话 ${conv.id.substring(0, 8)}`,
      preview: `上下文ID: ${conv.contextId || 'N/A'} - 点击继续之前的对话...`,
      avatar: undefined,
      updatedAt: new Date(conv.updatedAt || conv.createdAt)
    }))
  } catch (error: any) {
    ElMessage.error('加载对话列表失败: ' + (error.message || '未知错误'))
    conversations.value = []
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  // 如果userStore中没有用户信息，先加载
  if (!userStore.currentUser) {
    await userStore.loadCurrentUser()
  }
  loadConversations()
})

// 监听userId变化
watch(() => props.userId, () => {
  loadConversations()
})

// 监听userStore中的用户变化
watch(() => userStore.currentUser, () => {
  loadConversations()
})

const filteredConversations = computed(() => {
  if (!props.searchKeyword) return conversations.value
  
  const keyword = props.searchKeyword.toLowerCase()
  return conversations.value.filter(conv => 
    conv.title?.toLowerCase().includes(keyword) ||
    conv.preview?.toLowerCase().includes(keyword)
  )
})

const formatTime = (time: number | Date) => {
  const date = time instanceof Date ? time : new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}
</script>

<style scoped lang="scss">
.conversation-list-container {
  max-height: 600px;
  overflow-y: auto;
  padding: 0 16px;
  
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.1);
    border-radius: 3px;
    
    &:hover {
      background: rgba(0, 0, 0, 0.2);
    }
  }
}

.list-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 20px;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
  
  &:hover {
    background: rgba(255, 255, 255, 0.8);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    border-color: rgba(99, 102, 241, 0.3);
    
    .action-btn {
      opacity: 1;
      transform: translateX(0);
    }
  }
}

.item-left {
  flex-shrink: 0;
  
  .avatar {
    color: white;
    font-size: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
}

.item-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .title {
    font-size: 15px;
    font-weight: 600;
    color: #303133;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .time {
    font-size: 12px;
    color: #909399;
    flex-shrink: 0;
    margin-left: 8px;
  }
}

.item-preview {
  font-size: 13px;
  color: #606266;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  opacity: 0.8;
}

.item-right {
  flex-shrink: 0;
  
  .action-btn {
    opacity: 0;
    transform: translateX(10px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    background: transparent;
    border: none;
    color: #909399;
    
    &:hover {
      color: #6366f1;
      background: rgba(99, 102, 241, 0.1);
    }
  }
}

.loading-state {
  padding: 20px 0;
}

.empty-state {
  padding: 40px 0;
}
</style>
