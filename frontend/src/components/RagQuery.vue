<template>
  <div class="rag-query-container">
    <el-card class="query-card">
      <template #header>
        <div class="query-header">
          <span class="title">
            <el-icon><Search /></el-icon> 智能检索
          </span>
          <div class="settings">
            <span class="label">Top K:</span>
            <el-input-number 
              v-model="topK" 
              :min="1" 
              :max="10" 
              size="small"
              controls-position="right"
              class="k-input"
            />
          </div>
        </div>
      </template>
      
      <div class="input-area">
        <el-input
          v-model="queryText"
          type="textarea"
          :rows="4"
          placeholder="请输入您的问题，AI 将基于知识库为您解答..."
          resize="none"
          class="custom-textarea"
          @keydown.enter.prevent.ctrl="handleQuery"
        />
        <div class="input-actions">
          <span class="hint">Ctrl + Enter 发送</span>
          <el-button
            type="primary"
            @click="handleQuery"
            :loading="loading"
            round
            class="submit-btn"
          >
            查询
            <el-icon class="el-icon--right"><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>

      <transition name="fade-slide">
        <div v-if="result" class="result-area">
          <div class="result-header">
            <span class="label">AI 回答</span>
            <div class="confidence" v-if="result.confidence">
              <span>置信度</span>
              <el-progress 
                :percentage="Math.round(result.confidence * 100)" 
                :color="confidenceColor"
                :stroke-width="6"
                :width="40"
                type="circle"
              >
                <template #default="{ percentage }">
                  <span class="percentage-text">{{ percentage }}%</span>
                </template>
              </el-progress>
            </div>
          </div>
          
          <div class="answer-box">
            <div class="answer-content">{{ result.answer }}</div>
          </div>
          
          <div v-if="result.sources && result.sources.length > 0" class="sources-list">
            <div class="sources-title">
              <el-icon><Link /></el-icon> 参考来源
            </div>
            <div class="source-items">
              <div 
                v-for="(source, index) in result.sources" 
                :key="index"
                class="source-item"
              >
                <div class="source-index">{{ index + 1 }}</div>
                <div class="source-content">{{ source.title || source.url || '未知来源' }}</div>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, ArrowRight, Link } from '@element-plus/icons-vue'
import { ragApi } from '@/services/api/rag'

const emit = defineEmits<{
  refresh: []
}>()

const queryText = ref('')
const topK = ref(5)
const loading = ref(false)
const result = ref<any>(null)

const confidenceColor = [
  { color: '#f56c6c', percentage: 20 },
  { color: '#e6a23c', percentage: 40 },
  { color: '#5cb87a', percentage: 60 },
  { color: '#1989fa', percentage: 80 },
  { color: '#6f7ad3', percentage: 100 },
]

const handleQuery = async () => {
  if (!queryText.value.trim()) {
    ElMessage.warning('请输入查询内容')
    return
  }

  loading.value = true
  result.value = null // Clear previous result for animation
  
  try {
    // Simulate delay for effect if needed, but API call is enough
    result.value = await ragApi.query(queryText.value, topK.value)
    ElMessage.success('查询成功')
  } catch (error: any) {
    ElMessage.error('查询失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
$primary-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
$surface-color: rgba(255, 255, 255, 0.7);
$glass-border: 1px solid rgba(255, 255, 255, 0.3);

.rag-query-container {
  height: 100%;
}

.query-card {
  background: $surface-color !important;
  backdrop-filter: blur(16px) !important;
  border: $glass-border !important;
  border-radius: 16px !important;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07) !important;
  overflow: visible; // Allow shadows/elements to pop out if needed
  
  :deep(.el-card__header) {
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    padding: 16px 24px;
  }
}

.query-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .title {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
    display: flex;
    align-items: center;
    gap: 8px;
    
    .el-icon {
      color: #6366f1;
    }
  }
  
  .settings {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .label {
      font-size: 13px;
      color: #909399;
    }
    
    .k-input {
      width: 100px;
    }
  }
}

.input-area {
  position: relative;
  
  .custom-textarea {
    :deep(.el-textarea__inner) {
      border-radius: 12px;
      padding: 16px;
      font-size: 15px;
      background: rgba(255, 255, 255, 0.6);
      border: 1px solid rgba(0, 0, 0, 0.1);
      box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02);
      transition: all 0.3s;
      
      &:focus {
        background: white;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
        border-color: #6366f1;
      }
    }
  }
  
  .input-actions {
    margin-top: 12px;
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 16px;
    
    .hint {
      font-size: 12px;
      color: #909399;
    }
    
    .submit-btn {
      background: $primary-gradient;
      border: none;
      padding: 10px 24px;
      height: auto;
      font-weight: 500;
      letter-spacing: 0.5px;
      transition: all 0.3s;
      
      &:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
      }
    }
  }
}

.result-area {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px dashed rgba(0, 0, 0, 0.1);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  .label {
    font-size: 16px;
    font-weight: 700;
    color: #303133;
    position: relative;
    padding-left: 12px;
    
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      width: 4px;
      height: 16px;
      background: #8b5cf6;
      border-radius: 2px;
    }
  }
  
  .confidence {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: #909399;
    
    .percentage-text {
      font-size: 10px;
      transform: scale(0.9);
    }
  }
}

.answer-box {
  background: linear-gradient(to right bottom, rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.4));
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
  
  .answer-content {
    line-height: 1.8;
    color: #4b5563;
    font-size: 15px;
    text-align: justify;
  }
}

.sources-list {
  margin-top: 24px;
  
  .sources-title {
    font-size: 13px;
    font-weight: 600;
    color: #606266;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  
  .source-items {
    display: grid;
    gap: 8px;
    
    .source-item {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 10px;
      background: rgba(243, 244, 246, 0.5);
      border-radius: 8px;
      transition: all 0.2s;
      
      &:hover {
        background: rgba(243, 244, 246, 0.9);
      }
      
      .source-index {
        width: 20px;
        height: 20px;
        background: #e0e7ff;
        color: #6366f1;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: 700;
        flex-shrink: 0;
        margin-top: 2px;
      }
      
      .source-content {
        font-size: 13px;
        color: #6b7280;
        line-height: 1.5;
        word-break: break-all;
      }
    }
  }
}

// Transitions
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.4s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>


