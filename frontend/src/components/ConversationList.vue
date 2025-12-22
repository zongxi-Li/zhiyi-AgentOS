<template>
  <div class="conversation-list">
    <div class="list-header">
      <h3>对话历史</h3>
      <el-button size="small" @click="loadConversations" :loading="loading">
        刷新
      </el-button>
    </div>
    <div class="list-content">
      <div
        v-for="conversation in conversations"
        :key="conversation.id"
        :class="['conversation-item', { active: selectedId === conversation.id }]"
        @click="selectConversation(conversation)"
      >
        <div class="item-content">
          <div class="item-title">对话 {{ formatDate(conversation.createdAt) }}</div>
          <div class="item-time">{{ formatTime(conversation.updatedAt) }}</div>
        </div>
        <el-button
          type="danger"
          size="small"
          text
          @click.stop="deleteConversation(conversation.id)"
        >
          删除
        </el-button>
      </div>
      <el-empty v-if="!loading && conversations.length === 0" description="暂无对话历史" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { conversationApi, type Conversation } from '@/services/api/conversation'

interface Emits {
  (e: 'select', conversation: Conversation): void
}

const emit = defineEmits<Emits>()
const router = useRouter()

const conversations = ref<Conversation[]>([])
const selectedId = ref<string | null>(null)
const loading = ref(false)

const loadConversations = async () => {
  loading.value = true
  try {
    conversations.value = await conversationApi.getUserConversations()
  } catch (error) {
    ElMessage.error('加载对话列表失败')
  } finally {
    loading.value = false
  }
}

const selectConversation = (conversation: Conversation) => {
  selectedId.value = conversation.id
  emit('select', conversation)
  
  // 跳转到对话页面并传递 contextId
  router.push({
    path: '/chat',
    query: { contextId: conversation.contextId }
  })
}

const deleteConversation = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定要删除这个对话吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await conversationApi.deleteConversation(id)
    conversations.value = conversations.value.filter(c => c.id !== id)
    if (selectedId.value === id) {
      selectedId.value = null
    }
    ElMessage.success('删除成功')
  } catch {
    // 用户取消
  }
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

const formatTime = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadConversations()
})
</script>

<style scoped>
.conversation-list {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid #e4e7ed;
}

.list-header h3 {
  margin: 0;
  font-size: 16px;
}

.list-content {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.conversation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.conversation-item:hover {
  background: #f5f7fa;
}

.conversation-item.active {
  background: #ecf5ff;
  border: 1px solid #409eff;
}

.item-content {
  flex: 1;
}

.item-title {
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
}

.item-time {
  font-size: 12px;
  color: #909399;
}
</style>

