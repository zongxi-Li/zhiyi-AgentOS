<template>
  <div class="history-view">
    <!-- 背景装饰 -->
    <div class="history-bg-decoration">
      <div class="glow-orb orb-1"></div>
      <div class="glow-orb orb-2"></div>
      <div class="grid-overlay"></div>
    </div>

    <div class="history-content-wrapper">
      <el-card class="history-card">
        <template #header>
          <div class="card-header">
            <div class="header-left">
              <div class="icon-box">
                <el-icon><Clock /></el-icon>
              </div>
              <div>
                <h3>历史记录</h3>
                <p class="subtitle">查看和管理您的对话与文件历史</p>
              </div>
            </div>
            
            <div class="header-actions">
              <el-input
                v-model="searchKeyword"
                placeholder="搜索历史记录..."
                :prefix-icon="Search"
                class="search-input"
                clearable
              />
              <el-button 
                type="danger" 
                plain 
                class="clear-btn"
                @click="clearAll"
              >
                <el-icon><Delete /></el-icon>
                <span>清空全部</span>
              </el-button>
            </div>
          </div>
        </template>
        
        <el-tabs v-model="activeTab" class="history-tabs">
          <el-tab-pane name="conversations">
            <template #label>
              <span class="custom-tab-label">
                <el-icon><ChatLineRound /></el-icon> 对话历史
              </span>
            </template>
            <ConversationList
              :search-keyword="searchKeyword"
              @select="handleSelectConversation"
            />
          </el-tab-pane>
          
          <el-tab-pane name="files">
            <template #label>
              <span class="custom-tab-label">
                <el-icon><Document /></el-icon> 文件历史
              </span>
            </template>
            <div class="empty-state-wrapper">
              <el-empty description="暂无文件历史" :image-size="120" />
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Delete, Clock, ChatLineRound, Document } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ConversationList from '@/components/ConversationList.vue'

const router = useRouter()
const searchKeyword = ref('')
const activeTab = ref('conversations')

const handleSelectConversation = (conversation: any) => {
  router.push(`/chat?contextId=${conversation.id}`)
}

const clearAll = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有历史记录吗？此操作不可恢复。', '确认清空', {
      confirmButtonText: '确定清空',
      cancelButtonText: '取消',
      type: 'warning',
      customClass: 'glass-message-box'
    })
    ElMessage.success('历史记录已清空')
  } catch {
    // 用户取消
  }
}
</script>

<style scoped lang="scss">
// 变量定义 - 保持一致性
$primary-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
$surface-color: rgba(255, 255, 255, 0.75);
$glass-border: 1px solid rgba(255, 255, 255, 0.5);
$shadow-soft: 0 8px 32px 0 rgba(31, 38, 135, 0.07);

.history-view {
  min-height: calc(100vh - 64px);
  padding: 40px;
  position: relative;
  overflow: hidden;
  background: #f0f2f5;
}

.history-bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
  background: radial-gradient(circle at 80% 20%, #eef2ff, #f3f4f6);
  
  .glow-orb {
    position: absolute;
    border-radius: 50%;
    filter: blur(80px);
    opacity: 0.5;
  }
  
  .orb-1 {
    top: -5%;
    left: 20%;
    width: 600px;
    height: 600px;
    background: rgba(99, 102, 241, 0.1);
  }
  
  .orb-2 {
    bottom: -10%;
    right: 10%;
    width: 500px;
    height: 500px;
    background: rgba(236, 72, 153, 0.1);
  }
  
  .grid-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: 
      linear-gradient(rgba(0, 0, 0, 0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0, 0, 0, 0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    opacity: 0.5;
  }
}

.history-content-wrapper {
  position: relative;
  z-index: 1;
  max-width: 1200px;
  margin: 0 auto;
}

.history-card {
  min-height: 700px;
  background: $surface-color !important;
  backdrop-filter: blur(20px) !important;
  border: $glass-border !important;
  box-shadow: $shadow-soft !important;
  border-radius: 20px !important;
  transition: transform 0.3s;
  
  :deep(.el-card__header) {
    padding: 24px 32px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  }
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 20px;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .icon-box {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 24px;
      box-shadow: 0 4px 12px rgba(217, 119, 6, 0.25);
    }
    
    h3 {
      margin: 0;
      font-size: 20px;
      font-weight: 700;
      color: #303133;
    }
    
    .subtitle {
      margin: 4px 0 0;
      font-size: 13px;
      color: #909399;
    }
  }
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  
  .search-input {
    width: 280px;
    
    :deep(.el-input__wrapper) {
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.5);
      box-shadow: none;
      border: 1px solid rgba(0, 0, 0, 0.1);
      padding-left: 16px;
      
      &.is-focus {
        background: white;
        border-color: #f59e0b;
        box-shadow: 0 0 0 1px #f59e0b;
      }
    }
  }
  
  .clear-btn {
    border-radius: 20px;
    padding: 8px 20px;
    
    &:hover {
      background: #fef0f0;
      color: #f56c6c;
      border-color: #fbc4c4;
    }
    
    .el-icon {
      margin-right: 6px;
    }
  }
}

.history-tabs {
  :deep(.el-tabs__nav-wrap::after) {
    height: 1px;
    background-color: rgba(0, 0, 0, 0.05);
  }
  
  :deep(.el-tabs__header) {
    margin: 0 0 24px;
    padding: 0 32px;
  }
  
  :deep(.el-tabs__item) {
    font-size: 15px;
    height: 50px;
    color: #909399;
    transition: all 0.3s;
    
    &.is-active {
      color: #303133;
      font-weight: 600;
      
      .custom-tab-label {
        color: #d97706; // Matching the icon color
      }
    }
    
    &:hover {
      color: #606266;
    }
  }
  
  :deep(.el-tabs__active-bar) {
    background-color: #d97706;
    height: 3px;
    border-radius: 3px;
  }
  
  .custom-tab-label {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .el-icon {
      font-size: 18px;
    }
  }
}

.empty-state-wrapper {
  padding: 60px 0;
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .history-view {
    padding: 16px;
  }
  
  .card-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }
  
  .header-actions {
    flex-direction: column;
    
    .search-input {
      width: 100%;
    }
    
    .clear-btn {
      width: 100%;
    }
  }
  
  :deep(.el-tabs__header) {
    padding: 0 16px;
  }
}
</style>
