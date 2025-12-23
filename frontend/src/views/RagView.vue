<template>
  <div class="rag-view">
    <!-- 背景装饰 -->
    <div class="rag-bg-decoration">
      <div class="glow-orb orb-1"></div>
      <div class="glow-orb orb-2"></div>
      <div class="grid-overlay"></div>
    </div>

    <el-container class="rag-container">
      <el-header class="rag-header">
        <div class="header-content">
          <div class="header-title-group">
            <div class="header-icon">
              <el-icon><Reading /></el-icon>
            </div>
            <div>
              <h2>知识库查询</h2>
              <p class="header-subtitle">RAG Knowledge Base & Retrieval System</p>
            </div>
          </div>
          <div class="header-stats">
            <el-tag effect="dark" round class="stats-tag">
              <el-icon><Document /></el-icon> {{ documents.length }} 文档
            </el-tag>
          </div>
        </div>
      </el-header>
      
      <el-main class="rag-main">
        <el-row :gutter="24">
          <el-col :span="16" :xs="24">
            <div class="query-section">
              <RagQuery @refresh="loadDocuments" />
            </div>
          </el-col>
          
          <el-col :span="8" :xs="24">
            <div class="docs-section">
              <el-card class="glass-card docs-card" :body-style="{ padding: '0' }">
                <template #header>
                  <div class="card-header">
                    <span class="header-label">
                      <el-icon><Files /></el-icon> 文档管理
                    </span>
                    <el-button
                      type="primary"
                      size="small"
                      round
                      class="upload-btn"
                      @click="showUploadDialog = true"
                    >
                      <el-icon><Upload /></el-icon> 上传
                    </el-button>
                  </div>
                </template>
                
                <div class="docs-list-container">
                  <el-table
                    :data="documents"
                    style="width: 100%"
                    :show-header="true"
                    class="glass-table"
                  >
                    <el-table-column prop="filename" label="文件名" min-width="120">
                      <template #default="{ row }">
                        <div class="file-name-cell">
                          <el-icon class="file-icon"><Document /></el-icon>
                          <span class="text-truncate" :title="row.filename">{{ row.filename }}</span>
                        </div>
                      </template>
                    </el-table-column>
                    <el-table-column prop="upload_time" label="时间" width="100">
                      <template #default="{ row }">
                        <span class="time-text">{{ formatTime(row.upload_time) }}</span>
                      </template>
                    </el-table-column>
                    <el-table-column width="60" align="center">
                      <template #default="{ row }">
                        <el-button
                          type="danger"
                          link
                          class="delete-btn"
                          @click="handleDelete(row.doc_id)"
                        >
                          <el-icon><Delete /></el-icon>
                        </el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                  
                  <div v-if="documents.length === 0" class="empty-state">
                    <el-empty description="暂无文档" :image-size="80" />
                  </div>
                </div>
              </el-card>
            </div>
          </el-col>
        </el-row>
      </el-main>
    </el-container>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传文档"
      width="500px"
      class="glass-dialog"
      align-center
    >
      <div class="upload-container">
        <el-upload
          class="upload-area"
          :action="uploadUrl"
          :headers="uploadHeaders"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          :before-upload="beforeUpload"
          drag
        >
          <div class="upload-icon-wrapper">
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          </div>
          <div class="el-upload__text">
            <h3>点击或拖拽上传</h3>
            <p>支持 PDF, Word, TXT, MD 等格式</p>
          </div>
        </el-upload>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Reading, Document, Files, Upload, Delete } from '@element-plus/icons-vue'
import RagQuery from '@/components/RagQuery.vue'
import { ragApi } from '@/services/api/rag'

const showUploadDialog = ref(false)
const documents = ref<Array<{
  doc_id: string
  filename: string
  upload_time: string
  metadata: any
}>>([])

const uploadUrl = computed(() => '/api/rag/documents')

const uploadHeaders = computed(() => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
})

const beforeUpload = (file: File) => {
  const maxSize = 10 * 1024 * 1024 // 10MB
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过10MB')
    return false
  }
  return true
}

const handleUploadSuccess = () => {
  ElMessage.success('文档上传成功')
  showUploadDialog.value = false
  loadDocuments()
}

const handleUploadError = () => {
  ElMessage.error('文档上传失败')
}

const handleDelete = async (docId: string) => {
  try {
    await ragApi.deleteDocument(docId)
    ElMessage.success('文档删除成功')
    loadDocuments()
  } catch (error: any) {
    ElMessage.error('删除失败: ' + (error.message || '未知错误'))
  }
}

const loadDocuments = async () => {
  try {
    const response = await ragApi.listDocuments()
    documents.value = response.documents || []
  } catch (error: any) {
    ElMessage.error('加载文档列表失败: ' + (error.message || '未知错误'))
  }
}

const formatTime = (timeStr: string) => {
  if (!timeStr) return ''
  try {
    const date = new Date(timeStr)
    // 只显示日期部分，节省空间
    return date.toLocaleDateString()
  } catch {
    return timeStr
  }
}

onMounted(() => {
  loadDocuments()
})
</script>

<style scoped lang="scss">
// 变量定义
$primary-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
$surface-color: rgba(255, 255, 255, 0.7);
$surface-hover: rgba(255, 255, 255, 0.85);
$glass-border: 1px solid rgba(255, 255, 255, 0.3);
$shadow-soft: 0 8px 32px 0 rgba(31, 38, 135, 0.07);

.rag-view {
  height: calc(100vh - 64px);
  position: relative;
  overflow: hidden;
  background: #f0f2f5; // Fallback
}

.rag-bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
  background: radial-gradient(circle at 50% -20%, #eef2ff, #f3f4f6);
  
  .glow-orb {
    position: absolute;
    border-radius: 50%;
    filter: blur(80px);
    opacity: 0.6;
  }
  
  .orb-1 {
    top: -10%;
    right: -10%;
    width: 600px;
    height: 600px;
    background: rgba(99, 102, 241, 0.15);
  }
  
  .orb-2 {
    bottom: -10%;
    left: -10%;
    width: 500px;
    height: 500px;
    background: rgba(168, 85, 247, 0.15);
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

.rag-container {
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.rag-header {
  height: auto !important;
  padding: 24px 40px;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(10px);
  border-bottom: $glass-border;
  display: flex;
  align-items: center;
  
  .header-content {
    width: 100%;
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-title-group {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .header-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        background: $primary-gradient;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 24px;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
      }
      
      h2 {
        margin: 0;
        font-size: 24px;
        font-weight: 700;
        background: linear-gradient(120deg, #303133, #606266);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
      }
      
      .header-subtitle {
        margin: 4px 0 0;
        font-size: 13px;
        color: #909399;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }
    }
  }
}

.rag-main {
  padding: 32px 40px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.1);
    border-radius: 3px;
  }
}

// Glass Card Styles
.glass-card {
  background: $surface-color !important;
  backdrop-filter: blur(16px) !important;
  border: $glass-border !important;
  box-shadow: $shadow-soft !important;
  border-radius: 16px !important;
  transition: all 0.3s ease;
  
  &:hover {
    background: $surface-hover !important;
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(31, 38, 135, 0.12) !important;
  }
  
  :deep(.el-card__header) {
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    padding: 16px 20px;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .header-label {
    font-weight: 600;
    font-size: 16px;
    color: #303133;
    display: flex;
    align-items: center;
    gap: 8px;
    
    .el-icon {
      color: #6366f1;
    }
  }
}

.upload-btn {
  background: $primary-gradient;
  border: none;
  
  &:hover {
    opacity: 0.9;
    transform: scale(1.05);
  }
}

// Table Styles
.glass-table {
  background: transparent !important;
  --el-table-bg-color: transparent !important;
  --el-table-tr-bg-color: transparent !important;
  --el-table-header-bg-color: rgba(255, 255, 255, 0.3) !important;
  --el-table-row-hover-bg-color: rgba(99, 102, 241, 0.08) !important;
  
  :deep(th.el-table__cell) {
    background: transparent !important;
    font-weight: 600;
    color: #606266;
  }
  
  :deep(td.el-table__cell) {
    border-bottom: 1px solid rgba(0, 0, 0, 0.03);
  }
  
  .file-name-cell {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .file-icon {
      color: #8b5cf6;
      font-size: 16px;
    }
    
    .text-truncate {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      color: #303133;
      font-weight: 500;
    }
  }
  
  .time-text {
    font-size: 12px;
    color: #909399;
  }
  
  .delete-btn {
    padding: 4px;
    height: auto;
    color: #f56c6c;
    opacity: 0.6;
    transition: all 0.2s;
    
    &:hover {
      opacity: 1;
      background: rgba(245, 108, 108, 0.1);
      border-radius: 4px;
    }
  }
}

// Upload Dialog
.upload-container {
  .upload-area {
    :deep(.el-upload-dragger) {
      width: 100%;
      height: 240px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      background: rgba(245, 247, 250, 0.5);
      border: 2px dashed #dcdfe6;
      border-radius: 12px;
      transition: all 0.3s;
      
      &:hover {
        border-color: #6366f1;
        background: rgba(99, 102, 241, 0.04);
        
        .el-icon--upload {
          color: #6366f1;
          transform: scale(1.1);
        }
      }
      
      .upload-icon-wrapper {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        background: rgba(99, 102, 241, 0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 16px;
        transition: all 0.3s;
      }
      
      .el-icon--upload {
        font-size: 32px;
        color: #8b5cf6;
        margin: 0;
        transition: all 0.3s;
      }
      
      h3 {
        margin: 0 0 8px;
        font-size: 16px;
        color: #303133;
      }
      
      p {
        margin: 0;
        font-size: 13px;
        color: #909399;
      }
    }
  }
}

.docs-section {
  position: sticky;
  top: 0;
}

@media (max-width: 768px) {
  .rag-header {
    padding: 16px;
  }
  
  .rag-main {
    padding: 16px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
