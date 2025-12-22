<template>
  <div class="chat-view">
    <el-container>
      <!-- 侧边栏：角色选择 -->
      <el-aside width="250px" class="sidebar">
        <div class="sidebar-header">
          <h3>角色选择</h3>
        </div>
        <SearchBar @search="handleSearch" @clear="handleClearSearch" />
        <div class="role-list">
          <div
            v-for="role in filteredRoles"
            :key="role.id"
            :class="['role-item', { active: roleStore.currentRole?.id === role.id }]"
            @click="selectRole(role)"
          >
            <span>{{ role.name }}</span>
          </div>
        </div>
      </el-aside>

      <!-- 主内容区 -->
      <el-container class="main-container">
        <!-- 对话区域 -->
        <el-main class="chat-main">
          <div class="chat-messages" ref="messagesContainer">
            <MessageBubble
              v-for="message in chatStore.messages"
              :key="message.id"
              :message="message"
            />
            <div v-if="chatStore.loading" class="loading-indicator">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>AI正在思考...</span>
            </div>
            <div v-if="chatStore.messages.length === 0" class="empty-state">
              <el-empty description="开始对话吧！" />
            </div>
          </div>
        </el-main>

        <!-- 输入区域 -->
        <el-footer class="chat-footer" height="auto">
          <div class="chat-input-wrapper">
            <div class="input-toolbar">
              <FileUpload
                type="chat"
                button-text="上传"
                @uploaded="handleFileUploaded"
              />
            </div>
            <el-input
              v-model="inputText"
              type="textarea"
              :rows="3"
              placeholder="输入消息...（Shift+Enter换行，Enter发送）"
              @keydown.enter.exact.prevent="sendMessage"
              :disabled="chatStore.loading"
              :maxlength="1000"
              show-word-limit
            />
            <div class="input-actions">
              <el-button
                type="primary"
                @click="sendMessage"
                :loading="chatStore.loading"
                :disabled="!inputText.trim() && !currentFileUrl"
              >
                发送
              </el-button>
              <el-button @click="clearHistory">清除历史</el-button>
            </div>
          </div>
        </el-footer>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import { useRoleStore } from '@/stores/role'
import MessageBubble from '@/components/MessageBubble.vue'
import FileUpload from '@/components/FileUpload.vue'
import SearchBar from '@/components/SearchBar.vue'
import { useScrollToBottom } from '@/composables/useScrollToBottom'

const route = useRoute()
const chatStore = useChatStore()
const roleStore = useRoleStore()
const inputText = ref('')
const messagesContainer = ref<HTMLElement>()
const currentFileUrl = ref<string>('')
const searchKeyword = ref('')

const filteredRoles = computed(() => {
  if (!searchKeyword.value) {
    return roleStore.builtinRoles
  }
  const keyword = searchKeyword.value.toLowerCase()
  return roleStore.builtinRoles.filter(role =>
    role.name.toLowerCase().includes(keyword) ||
    role.description?.toLowerCase().includes(keyword)
  )
})

const sendMessage = async () => {
  if ((!inputText.value.trim() && !currentFileUrl.value) || chatStore.loading) return

  const text = inputText.value.trim()
  const fileUrl = currentFileUrl.value
  inputText.value = ''
  currentFileUrl.value = ''

  try {
    await chatStore.sendMessage(text, fileUrl)
    await nextTick()
    scrollToBottom()
  } catch (error: any) {
    ElMessage.error(error.message || '发送消息失败')
  }
}

const handleFileUploaded = (url: string, fileName: string) => {
  currentFileUrl.value = url
}

const handleSearch = (keyword: string) => {
  searchKeyword.value = keyword
}

const handleClearSearch = () => {
  searchKeyword.value = ''
}

const selectRole = (role: any) => {
  roleStore.selectRole(role)
  chatStore.setRole(role.id)
  ElMessage.success(`已切换到角色: ${role.name}`)
}

const clearHistory = async () => {
  try {
    await ElMessageBox.confirm('确定要清除对话历史吗？', '确认清除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await chatStore.clearHistory()
    ElMessage.success('历史已清除')
  } catch {
    // 用户取消
  }
}

const { scrollToBottom } = useScrollToBottom(messagesContainer)


// 监听消息变化，自动滚动
watch(() => chatStore.messages.length, () => {
  nextTick(() => scrollToBottom())
})

// 监听路由参数变化，当 contextId 变化时重新加载历史
watch(() => route.query.contextId, async (newContextId) => {
  if (newContextId && typeof newContextId === 'string') {
    await chatStore.loadHistory(newContextId)
    await nextTick()
    scrollToBottom()
  }
})

onMounted(async () => {
  // 加载角色列表
  await roleStore.loadBuiltinRoles()
  if (roleStore.builtinRoles.length > 0) {
    selectRole(roleStore.builtinRoles[0])
  }

  // 检查路由参数中是否有 contextId
  const contextId = route.query.contextId as string | undefined
  if (contextId) {
    // 如果有 contextId，加载对话历史
    await chatStore.loadHistory(contextId)
    await nextTick()
    scrollToBottom()
  } else {
    // 如果没有 contextId，检查是否有已存在的 contextId（可能是从其他页面跳转过来的）
    if (chatStore.contextId) {
      await chatStore.loadHistory(chatStore.contextId)
      await nextTick()
      scrollToBottom()
    }
  }
})
</script>

<style scoped>
.chat-view {
  height: calc(100vh - 60px); /* 减去header高度 */
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar {
  background: #f5f7fa;
  border-right: 1px solid #e4e7ed;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
}

.role-list {
  padding: 10px;
}

.role-item {
  padding: 12px 15px;
  margin-bottom: 5px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.role-item:hover {
  background: #e4e7ed;
}

.role-item.active {
  background: #409eff;
  color: white;
}

.chat-main {
  padding: 0;
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #fafafa;
  min-height: 0;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px;
  color: #909399;
}

.chat-footer {
  background: white;
  border-top: 1px solid #e4e7ed;
  padding: 15px 20px;
  height: auto !important;
  flex-shrink: 0;
}

.chat-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>

