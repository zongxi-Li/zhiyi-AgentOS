<template>
  <div class="rag-view">
    <el-container>
      <el-header>
        <h2>知识库查询（RAG）</h2>
      </el-header>
      <el-main>
        <el-row :gutter="20">
          <el-col :span="16">
            <RagQuery @refresh="loadDocuments" />
          </el-col>
          <el-col :span="8">
            <el-card>
              <template #header>
                <div class="card-header">
                  <span>文档管理</span>
                  <el-button
                    type="primary"
                    size="small"
                    @click="showUploadDialog = true"
                  >
                    上传文档
                  </el-button>
                </div>
              </template>
              
              <el-table
                :data="documents"
                style="width: 100%"
                max-height="400"
              >
                <el-table-column prop="filename" label="文件名" />
                <el-table-column prop="upload_time" label="上传时间" width="150">
                  <template #default="{ row }">
                    {{ formatTime(row.upload_time) }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="80">
                  <template #default="{ row }">
                    <el-button
                      type="danger"
                      size="small"
                      @click="handleDelete(row.doc_id)"
                    >
                      删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传文档"
      width="500px"
    >
      <el-upload
        :action="uploadUrl"
        :headers="uploadHeaders"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :before-upload="beforeUpload"
        drag
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持PDF、Word、TXT、MD等文档格式，最大10MB
          </div>
        </template>
      </el-upload>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
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
    return date.toLocaleString('zh-CN')
  } catch {
    return timeStr
  }
}

onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
.rag-view {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
