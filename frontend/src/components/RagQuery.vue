<template>
  <div class="rag-query">
    <el-card>
      <template #header>
        <span>知识库查询（RAG）</span>
      </template>
      
      <el-form @submit.prevent="handleQuery">
        <el-form-item label="查询">
          <el-input
            v-model="queryText"
            type="textarea"
            :rows="3"
            placeholder="输入要查询的问题..."
          />
        </el-form-item>
        <el-form-item label="返回数量">
          <el-input-number
            v-model="topK"
            :min="1"
            :max="10"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            @click="handleQuery"
            :loading="loading"
          >
            查询
          </el-button>
        </el-form-item>
      </el-form>

      <div v-if="result" class="rag-result">
        <h4>回答：</h4>
        <p>{{ result.answer }}</p>
        <div v-if="result.sources && result.sources.length > 0">
          <h4>来源：</h4>
          <ul>
            <li v-for="(source, index) in result.sources" :key="index">
              {{ source.title || source.url || '未知来源' }}
            </li>
          </ul>
        </div>
        <div v-if="result.confidence">
          <el-text type="info">置信度: {{ (result.confidence * 100).toFixed(1) }}%</el-text>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { ragApi } from '@/services/api/rag'

const emit = defineEmits<{
  refresh: []
}>()

const queryText = ref('')
const topK = ref(5)
const loading = ref(false)
const result = ref<any>(null)

const handleQuery = async () => {
  if (!queryText.value.trim()) {
    ElMessage.warning('请输入查询内容')
    return
  }

  loading.value = true
  try {
    result.value = await ragApi.query(queryText.value, topK.value)
    ElMessage.success('查询成功')
  } catch (error: any) {
    ElMessage.error('查询失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.rag-query {
  padding: 20px;
}

.rag-result {
  margin-top: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.rag-result h4 {
  margin: 10px 0 5px 0;
  color: #303133;
}

.rag-result ul {
  margin: 10px 0;
  padding-left: 20px;
}
</style>

