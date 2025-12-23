<template>
  <div class="create-role-view">
    <el-container>
      <el-header class="header">
        <div class="header-content">
          <div class="left-section">
            <el-button @click="handleBack" :icon="ArrowLeft" circle plain />
            <h2>创建自定义角色</h2>
          </div>
        </div>
      </el-header>

      <el-main>
        <div class="form-container">
          <el-card class="form-card">
            <template #header>
              <div class="card-header">
                <span>角色信息设定</span>
                <el-tooltip content="创建具有独特个性和专业知识的AI角色" placement="top">
                  <el-icon><InfoFilled /></el-icon>
                </el-tooltip>
              </div>
            </template>
            
            <el-form
              ref="formRef"
              :model="form"
              :rules="rules"
              label-position="top"
              size="large"
            >
              <el-form-item label="角色名称" prop="name">
                <el-input 
                  v-model="form.name" 
                  placeholder="给你的角色起个名字，例如：Python专家、心理咨询师" 
                  maxlength="50"
                  show-word-limit
                />
              </el-form-item>

              <el-form-item label="角色描述" prop="description">
                <el-input
                  v-model="form.description"
                  type="textarea"
                  :rows="3"
                  placeholder="简短描述这个角色的主要功能和特点"
                  maxlength="200"
                  show-word-limit
                />
              </el-form-item>

              <el-form-item label="系统提示词 (System Prompt)" prop="systemPrompt">
                <div class="label-helper">
                  <span>这是核心设定，决定了角色的行为方式。</span>
                  <el-link type="primary" :underline="false" href="#" @click.prevent>查看示例</el-link>
                </div>
                <el-input
                  v-model="form.systemPrompt"
                  type="textarea"
                  :rows="8"
                  placeholder="你是一名经验丰富的Python后端工程师，专注于高性能Web服务开发。你擅长使用FastAPI和Django框架。在回答问题时，请提供清晰的代码示例和最佳实践建议。"
                />
              </el-form-item>

              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="对话风格">
                    <el-input
                      v-model="form.dialogueStyleText"
                      type="textarea"
                      :rows="4"
                      placeholder='例如：{"formal": "high", "warmth": "medium"} (JSON格式)'
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="性格特点">
                    <el-input
                      v-model="form.personalityText"
                      type="textarea"
                      :rows="4"
                      placeholder='例如：{"traits": ["patient", "professional", "creative"]} (JSON格式)'
                    />
                  </el-form-item>
                </el-col>
              </el-row>

              <!-- 形象配色部分 -->
              <div class="section-divider">
                <span class="section-title">形象与配色</span>
                <div class="section-line"></div>
              </div>

              <div class="color-selection-container">
                <p class="section-desc">选择三个基准颜色，这将决定数字人的外观风格以及聊天界面的主题配色。</p>
                <el-row :gutter="40" justify="center">
                  <el-col :span="8" class="color-item">
                    <span class="color-label">主色调 (Primary)</span>
                    <el-color-picker v-model="form.colors.primary" show-alpha />
                    <span class="color-value">{{ form.colors.primary }}</span>
                    <div class="color-desc">决定界面的主要视觉风格</div>
                  </el-col>
                  <el-col :span="8" class="color-item">
                    <span class="color-label">辅助色 (Secondary)</span>
                    <el-color-picker v-model="form.colors.secondary" show-alpha />
                    <span class="color-value">{{ form.colors.secondary }}</span>
                    <div class="color-desc">用于搭配和衬托主色调</div>
                  </el-col>
                  <el-col :span="8" class="color-item">
                    <span class="color-label">点缀色 (Accent)</span>
                    <el-color-picker v-model="form.colors.accent" show-alpha />
                    <span class="color-value">{{ form.colors.accent }}</span>
                    <div class="color-desc">用于强调重点和交互元素</div>
                  </el-col>
                </el-row>
                
                <!-- 预览色块 -->
                <div class="color-preview" :style="{
                  '--preview-primary': form.colors.primary,
                  '--preview-secondary': form.colors.secondary,
                  '--preview-accent': form.colors.accent
                }">
                  <div class="preview-card">
                    <div class="preview-header">
                      <div class="preview-avatar">
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <circle cx="12" cy="12" r="12" :fill="form.colors.secondary" />
                          <circle cx="12" cy="12" r="11" stroke="white" stroke-width="1.5" />
                          <path d="M7 16C7 13.2386 9.23858 11 12 11C14.7614 11 17 13.2386 17 16" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
                          <circle cx="12" cy="8" r="2.5" fill="white" />
                        </svg>
                      </div>
                      <div class="preview-title">配色与形象预览</div>
                    </div>
                    <div class="preview-body">
                      <div class="preview-bubble left">你好，我是你的AI助手。</div>
                      <div class="preview-bubble right">
                        <span class="preview-btn">开始对话</span>
                      </div>
                      <div class="preview-model-hint">
                        数字人形象将基于您选择的基准色生成
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="form-actions">
                <el-button @click="handleBack">取消</el-button>
                <el-button type="primary" @click="handleSubmit" :loading="loading">
                  立即创建
                </el-button>
              </div>
            </el-form>
          </el-card>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { ArrowLeft, InfoFilled } from '@element-plus/icons-vue'
import { useRoleStore } from '@/stores/role'
import type { RoleCreateRequest } from '@/services/api/role'

const router = useRouter()
const roleStore = useRoleStore()
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  name: '',
  description: '',
  systemPrompt: '',
  dialogueStyleText: '',
  personalityText: '',
  colors: {
    primary: '#409EFF',
    secondary: '#79bbff',
    accent: '#95d475'
  }
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入角色描述', trigger: 'blur' }
  ],
  systemPrompt: [
    { required: true, message: '请输入系统提示词', trigger: 'blur' }
  ]
}

const handleBack = () => {
  router.back()
}

const parseJson = (text: string): any => {
  if (!text || !text.trim()) return undefined
  try {
    return JSON.parse(text)
  } catch {
    return undefined
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const request: RoleCreateRequest = {
          name: form.name,
          description: form.description,
          systemPrompt: form.systemPrompt,
          dialogueStyle: parseJson(form.dialogueStyleText),
          personality: parseJson(form.personalityText),
          avatarConfig: {
            colors: form.colors
          }
        }

        await roleStore.createRole(request)
        ElMessage.success('角色创建成功')
        router.push('/roles')
      } catch (error: any) {
        ElMessage.error(error.message || '创建角色失败')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped lang="scss">
.create-role-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-color-page);
}

:deep(.el-container) {
  height: 100%;
  overflow: hidden;
}

.header {
  flex-shrink: 0;
  background: var(--bg-color);
  border-bottom: 1px solid var(--border-color-base);
  padding: 0 var(--spacing-xl);
  box-shadow: var(--box-shadow-base);
}

.header-content {
  display: flex;
  align-items: center;
  height: 100%;
  
  .left-section {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    
    h2 {
      margin: 0;
      font-size: var(--font-size-xl);
      font-weight: 600;
      color: var(--text-color-primary);
    }
  }
}

:deep(.el-main) {
  padding: var(--spacing-xl);
  overflow-y: auto;
  display: flex;
  justify-content: center;
  /* 确保在内容溢出时可以滚动 */
  height: 100%;
}

.form-container {
  width: 100%;
  max-width: 800px;
  /* 增加底部间距，防止滚动到底部时紧贴 */
  padding-bottom: var(--spacing-2xl);
}

.form-card {
  border-radius: var(--border-radius-large);
  box-shadow: var(--box-shadow-light);
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: var(--font-size-lg);
    font-weight: 600;
  }
}

.label-helper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  font-size: var(--font-size-sm);
  color: var(--text-color-secondary);
}

.form-actions {
  margin-top: var(--spacing-xl);
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--border-color-light);
}

.section-divider {
  display: flex;
  align-items: center;
  margin: var(--spacing-xl) 0 var(--spacing-lg);
  
  .section-title {
    font-size: var(--font-size-md);
    font-weight: 600;
    color: var(--text-color-primary);
    white-space: nowrap;
    margin-right: var(--spacing-md);
  }
  
  .section-line {
    flex-grow: 1;
    height: 1px;
    background-color: var(--border-color-light);
  }
}

.color-selection-container {
  padding: 0 var(--spacing-md);
  
  .section-desc {
    color: var(--text-color-secondary);
    font-size: var(--font-size-sm);
    margin-bottom: var(--spacing-xl);
  }
}

.color-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  
  .color-label {
    font-size: var(--font-size-sm);
    font-weight: 500;
    color: var(--text-color-regular);
  }
  
  .color-value {
    font-family: monospace;
    font-size: 12px;
    color: var(--text-color-secondary);
  }
  
  .color-desc {
    font-size: 12px;
    color: var(--text-color-secondary);
    text-align: center;
    margin-top: 4px;
  }
}

.color-preview {
  margin-top: var(--spacing-2xl);
  padding: var(--spacing-xl);
  background: #f5f7fa;
  border-radius: 8px;
  display: flex;
  justify-content: center;
  
  .preview-card {
    width: 300px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    
    .preview-header {
      background: var(--preview-primary);
      padding: 16px;
      display: flex;
      align-items: center;
      gap: 12px;
      
      .preview-avatar {
        width: 36px;
        height: 36px;
        flex-shrink: 0;
        
        svg {
          width: 100%;
          height: 100%;
          display: block;
        }
      }
      
      .preview-title {
        color: white;
        font-weight: 600;
        font-size: 14px;
        text-shadow: 0 1px 2px rgba(0,0,0,0.1);
      }
    }
    
    .preview-body {
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      
      .preview-bubble {
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 12px;
        max-width: 80%;
        
        &.left {
          align-self: flex-start;
          background: #f0f2f5;
          color: #333;
          border-left: 3px solid var(--preview-secondary);
        }
        
        &.right {
          align-self: flex-end;
          
          .preview-btn {
            display: inline-block;
            padding: 6px 16px;
            background: var(--preview-accent);
            color: white;
            border-radius: 16px;
            font-weight: 500;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          }
        }
      }

      .preview-model-hint {
        text-align: center;
        font-size: 10px;
        color: #909399;
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px dashed #e4e7ed;
      }
    }
  }
}
</style>

