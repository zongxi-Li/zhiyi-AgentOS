<template>
  <div class="create-role-view">
    <!-- Atmospheric Background -->
    <div class="ambient-glow top-left"></div>
    <div class="ambient-glow bottom-right"></div>

    <el-container class="view-layout">
      <el-header class="header glass-header">
        <div class="header-content">
          <div class="left-section">
            <div class="back-btn" @click="handleBack">
              <el-icon><ArrowLeft /></el-icon>
            </div>
            <h2 class="page-title">创建自定义角色</h2>
          </div>
          <div class="header-actions">
            <el-button @click="handleBack" class="cancel-btn">取消</el-button>
            <el-button type="primary" @click="handleSubmit" :loading="loading" class="create-btn">
              立即创建
            </el-button>
          </div>
        </div>
      </el-header>

      <el-main class="scroll-area">
        <div class="content-wrapper">
          <div class="form-grid">
            <!-- Left: Info Settings -->
            <div class="form-main-side">
              <div class="glass-card section-card">
                <div class="section-header">
                  <div class="title-box">
                    <span class="dot"></span>
                    <h3>基本信息设定</h3>
                  </div>
                  <el-tooltip content="这些信息将定义角色的基础身份" placement="top">
                    <el-icon class="info-trigger"><InfoFilled /></el-icon>
                  </el-tooltip>
                </div>

                <el-form
                  ref="formRef"
                  :model="form"
                  :rules="rules"
                  label-position="top"
                  class="premium-form"
                >
                  <el-form-item label="角色名称" prop="name">
                    <el-input 
                      v-model="form.name" 
                      placeholder="例如：Python专家、心理咨询师" 
                      maxlength="50"
                      show-word-limit
                      class="premium-input"
                    />
                  </el-form-item>

                  <el-form-item label="角色描述" prop="description">
                    <el-input
                      v-model="form.description"
                      type="textarea"
                      :rows="2"
                      placeholder="简短描述这个角色的主要功能和特点"
                      maxlength="200"
                      show-word-limit
                      class="premium-input"
                    />
                  </el-form-item>

                  <el-form-item prop="systemPrompt">
                    <template #label>
                      <div class="label-with-helper">
                        <span>系统提示词 (System Prompt)</span>
                        <el-link type="primary" :underline="false" class="example-link">查看示例</el-link>
                      </div>
                    </template>
                    <el-input
                      v-model="form.systemPrompt"
                      type="textarea"
                      :rows="10"
                      placeholder="这是核心设定，决定了角色的行为方式。请输入详细的角色指令..."
                      class="premium-input prompt-input"
                    />
                  </el-form-item>

                  <div class="form-row">
                    <el-form-item label="对话风格" class="half-width">
                      <el-input
                        v-model="form.dialogueStyleText"
                        type="textarea"
                        :rows="3"
                        placeholder='例如：{"formal": "high", "warmth": "medium"}'
                        class="premium-input"
                      />
                    </el-form-item>
                    <el-form-item label="性格特点" class="half-width">
                      <el-input
                        v-model="form.personalityText"
                        type="textarea"
                        :rows="3"
                        placeholder='例如：{"traits": ["patient", "professional"]}'
                        class="premium-input"
                      />
                    </el-form-item>
                  </div>
                </el-form>
              </div>
            </div>

            <!-- Right: Visual & Preview -->
            <div class="form-side-pane">
              <!-- Digital Human Style Selection -->
              <div class="glass-card section-card">
                <div class="section-header">
                  <div class="title-box">
                    <span class="dot accent"></span>
                    <h3>数字人形象风格</h3>
                  </div>
                </div>
                
                <div class="style-selection">
                  <p class="config-hint">选择数字人形象的生成风格，系统将根据此风格生成对应的数字人形象。</p>
                  
                  <div class="style-options">
                    <div 
                      v-for="style in digitalHumanStyles" 
                      :key="style.id"
                      class="style-option-card"
                      :class="{ active: form.digitalHumanStyle === style.id }"
                      @click="form.digitalHumanStyle = style.id"
                    >
                      <div class="style-icon">{{ style.icon }}</div>
                      <div class="style-name">{{ style.name }}</div>
                      <div class="style-desc">{{ style.description }}</div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Visual Styles -->
              <div class="glass-card section-card">
                <div class="section-header">
                  <div class="title-box">
                    <span class="dot accent"></span>
                    <h3>视觉形象与配色</h3>
                  </div>
                </div>
                
                <div class="color-config">
                  <p class="config-hint">选择品牌基准色，系统将自动生成对应的数字人形象与界面主题。</p>
                  
                  <div class="color-pickers">
                    <div class="picker-item">
                      <span class="p-label">主色调</span>
                      <el-color-picker v-model="form.colors.primary" show-alpha />
                    </div>
                    <div class="picker-item">
                      <span class="p-label">辅助色</span>
                      <el-color-picker v-model="form.colors.secondary" show-alpha />
                    </div>
                    <div class="picker-item">
                      <span class="p-label">点缀色</span>
                      <el-color-picker v-model="form.colors.accent" show-alpha />
                    </div>
                  </div>
                </div>

                <div class="preview-area">
                  <div class="preview-device" :style="{
                    '--p-color': form.colors.primary,
                    '--s-color': form.colors.secondary,
                    '--a-color': form.colors.accent
                  }">
                    <div class="device-header">
                      <div class="avatar-circle"></div>
                      <div class="header-lines">
                        <div class="line long"></div>
                        <div class="line short"></div>
                      </div>
                    </div>
                    <div class="device-body">
                      <div class="chat-bubble bot">Hello, I'm your AI.</div>
                      <div class="chat-bubble user">Nice to meet you!</div>
                      <div class="action-bar">
                        <div class="btn-mock">Send</div>
                      </div>
                    </div>
                  </div>
                  <p class="preview-label">界面配色效果实时预览</p>
                </div>
              </div>

              <!-- Extra Tip -->
              <div class="glass-card tip-card">
                <el-icon><StarFilled /></el-icon>
                <div class="tip-content">
                  <h4>设计建议</h4>
                  <p>优秀的提示词应包含角色的身份背景、专业技能范围以及特定的语言禁忌。</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { ArrowLeft, InfoFilled, StarFilled } from '@element-plus/icons-vue'
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
  digitalHumanStyle: 'realistic',  // 数字人形象风格
  colors: {
    primary: '#409EFF',
    secondary: '#79bbff',
    accent: '#95d475'
  }
})

const digitalHumanStyles = [
  {
    id: 'realistic',
    name: '写实风格',
    icon: '🎭',
    description: '极其写实，如同真实人类一般'
  },
  {
    id: 'cartoon',
    name: '卡通风格',
    icon: '🎨',
    description: '清新可爱，适合日常交流'
  },
  {
    id: 'anime',
    name: '二次元风格',
    icon: '✨',
    description: '充满艺术感，深受年轻用户喜爱'
  }
]

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
            colors: form.colors,
            style: form.digitalHumanStyle
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
  height: 100vh;
  width: 100%;
  position: relative;
  overflow: hidden;
  background-color: var(--bg-app);
}

/* Ambient Background - 使用简洁的纯色，不使用深层渐变 */
.ambient-glow {
  display: none;
}

.view-layout {
  height: 100%;
  position: relative;
  z-index: 1;
}

.glass-header {
  background: #ffffff;
  border-bottom: 1px solid var(--border-light);
  height: 72px !important;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.left-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border: 1px solid var(--border-light);
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text-secondary);
}

.back-btn:hover {
  color: var(--primary-color);
  background: var(--bg-input);
  border-color: var(--primary-color);
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  font-family: var(--font-serif);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.cancel-btn {
  border-radius: 12px;
  height: 42px;
  padding: 0 24px;
}

.create-btn {
  border-radius: 12px;
  height: 42px;
  padding: 0 24px;
  font-weight: 600;
}

.scroll-area {
  padding: 40px 0;
  overflow-y: auto;
}

.content-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1.6fr 0.9fr;
  gap: 24px;
  align-items: start;
}

.glass-card {
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid var(--border-light);
  padding: 32px;
}

.section-card {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.title-box {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-box h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary-color);
}

.dot.accent { background: #10b981; }

.info-trigger {
  color: var(--text-disabled);
  cursor: help;
}

/* Premium Form Elements */
.premium-form {
  :deep(.el-form-item__label) {
    font-weight: 600;
    font-size: 14px;
    color: var(--text-regular);
    padding-bottom: 8px;
  }
}

.premium-input {
  :deep(.el-input__wrapper), :deep(.el-textarea__inner) {
    background-color: #f8fafc !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    border: 1px solid transparent !important;
    transition: all 0.2s;
  }
  
  :deep(.el-input__wrapper:hover), :deep(.el-textarea__inner:hover) {
    background-color: white !important;
    border-color: var(--border-hover) !important;
  }
  
  :deep(.el-input__wrapper.is-focus), :deep(.el-textarea__inner:focus) {
    background-color: white !important;
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 1px var(--primary-color) inset !important;
  }
}

.label-with-helper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.example-link {
  font-weight: 500;
  font-size: 13px;
}

.form-row {
  display: flex;
  gap: 20px;
}

.half-width {
  flex: 1;
}

/* Side Pane Styles */
.color-config {
  margin-bottom: 32px;
}

.config-hint {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 24px;
}

.color-pickers {
  display: flex;
  justify-content: space-between;
  background: #f1f5f9;
  padding: 20px;
  border-radius: 16px;
}

.picker-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.p-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

/* Device Preview Mockup */
.preview-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background: #f8fafc;
  border-radius: 20px;
}

.preview-device {
  width: 220px;
  height: 320px;
  background: white;
  border-radius: 16px;
  border: 2px solid var(--border-light);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  margin-bottom: 16px;
}

.device-header {
  height: 50px;
  background: var(--p-color);
  display: flex;
  align-items: center;
  padding: 0 12px;
  gap: 10px;
}

.avatar-circle {
  width: 28px;
  height: 28px;
  background: rgba(255,255,255,0.3);
  border-radius: 50%;
}

.header-lines {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.line { height: 4px; background: rgba(255,255,255,0.3); border-radius: 2px; }
.line.long { width: 60px; }
.line.short { width: 30px; }

.device-body {
  flex: 1;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chat-bubble {
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 10px;
  max-width: 80%;
  font-weight: 500;
}

.chat-bubble.bot {
  background: #f1f5f9;
  color: #334155;
  border-left: 3px solid var(--s-color);
  align-self: flex-start;
}

.chat-bubble.user {
  background: var(--p-color);
  color: white;
  align-self: flex-end;
}

.action-bar {
  margin-top: auto;
  padding-top: 10px;
  border-top: 1px dashed #e2e8f0;
  display: flex;
  justify-content: flex-end;
}

.btn-mock {
  background: var(--a-color);
  color: white;
  padding: 4px 12px;
  border-radius: 10px;
  font-size: 9px;
  font-weight: 700;
}

.preview-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-disabled);
}

.tip-card {
  display: flex;
  gap: 16px;
  background: rgba(79, 70, 229, 0.05);
  border: 1px solid rgba(79, 70, 229, 0.15);
  padding: 24px;
}

.tip-card .el-icon {
  font-size: 24px;
  color: var(--primary-color);
}

.tip-content h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 700;
}

.tip-content p {
  margin: 0;
  font-size: 13px;
  color: var(--text-regular);
  line-height: 1.5;
}

/* Style Selection */
.style-selection {
  margin-bottom: 32px;
}

.style-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.style-option-card {
  padding: 16px;
  border: 2px solid var(--border-light);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;

  &:hover {
    border-color: var(--primary-color);
    background: rgba(79, 70, 229, 0.02);
  }

  &.active {
    border-color: var(--primary-color);
    background: rgba(79, 70, 229, 0.05);
  }
}

.style-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.style-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.style-desc {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
}

@media (max-width: 1024px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>

