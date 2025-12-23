<template>
  <div class="settings-view">
    <el-container>
      <el-header>
        <h2>系统设置</h2>
      </el-header>
      <el-main>
        <el-card>
          <template #header>
            <span>通用设置</span>
          </template>
          
          <el-form label-width="150px">
            <el-form-item label="主题">
              <el-radio-group v-model="settings.theme">
                <el-radio label="light">浅色</el-radio>
                <el-radio label="dark">深色</el-radio>
                <el-radio label="auto">跟随系统</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="语言">
              <el-select v-model="settings.language">
                <el-option label="简体中文" value="zh-CN" />
                <el-option label="English" value="en" />
              </el-select>
            </el-form-item>

            <el-form-item label="字体大小">
              <el-slider v-model="settings.fontSize" :min="12" :max="20" />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card style="margin-top: 20px">
          <template #header>
            <span>对话设置</span>
          </template>
          
          <el-form label-width="150px">
            <el-form-item label="自动发送">
              <el-switch v-model="settings.autoSend" />
              <span class="form-tip">语音识别后自动发送</span>
            </el-form-item>

            <el-form-item label="消息提示音">
              <el-switch v-model="settings.messageSound" />
            </el-form-item>

            <el-form-item label="历史记录保留">
              <el-select v-model="settings.historyRetention">
                <el-option label="1天" value="1" />
                <el-option label="7天" value="7" />
                <el-option label="30天" value="30" />
                <el-option label="永久" value="forever" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card style="margin-top: 20px">
          <template #header>
            <span>数字人设置</span>
          </template>
          
          <el-form label-width="150px">
            <el-form-item label="渲染质量">
              <el-select v-model="settings.renderQuality">
                <el-option label="高" value="high" />
                <el-option label="中" value="medium" />
                <el-option label="低" value="low" />
              </el-select>
            </el-form-item>

            <el-form-item label="动画流畅度">
              <el-slider v-model="settings.animationSmoothness" :min="30" :max="60" />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card style="margin-top: 20px">
          <template #header>
            <span>语音设置</span>
          </template>
          
          <VoiceSettings @change="handleVoiceSettingsChange" />
        </el-card>

        <div class="settings-actions">
          <el-button type="primary" @click="saveSettings">保存设置</el-button>
          <el-button @click="resetSettings">重置</el-button>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import VoiceSettings from '@/components/VoiceSettings.vue'

const settings = ref({
  theme: 'light',
  language: 'zh-CN',
  fontSize: 14,
  autoSend: false,
  messageSound: true,
  historyRetention: '7',
  renderQuality: 'medium',
  animationSmoothness: 45,
  voice: 'default',
  speed: 1.0,
  pitch: 1.0
})

const loadSettings = () => {
  const saved = localStorage.getItem('appSettings')
  if (saved) {
    try {
      settings.value = { ...settings.value, ...JSON.parse(saved) }
    } catch (e) {
      console.error('加载设置失败', e)
    }
  }
}

const saveSettings = () => {
  localStorage.setItem('appSettings', JSON.stringify(settings.value))
  ElMessage.success('设置已保存')
}

const resetSettings = () => {
  settings.value = {
    theme: 'light',
    language: 'zh-CN',
    fontSize: 14,
    autoSend: false,
    messageSound: true,
    historyRetention: '7',
    renderQuality: 'medium',
    animationSmoothness: 45,
    voice: 'default',
    speed: 1.0,
    pitch: 1.0
  }
  localStorage.removeItem('appSettings')
  ElMessage.success('设置已重置')
}

const handleVoiceSettingsChange = (voiceSettings: { voice: string; speed: number; pitch: number }) => {
  settings.value.voice = voiceSettings.voice
  settings.value.speed = voiceSettings.speed
  settings.value.pitch = voiceSettings.pitch
  saveSettings()
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped lang="scss">
.settings-view {
  padding: var(--spacing-xl);
  max-width: 1200px;
  margin: 0 auto;
  background: var(--bg-color-page);
  min-height: calc(100vh - 64px);
  
  .el-header {
    padding: var(--spacing-lg) 0;
    border-bottom: 1px solid var(--border-color-base);
    margin-bottom: var(--spacing-xl);
    
    h2 {
      margin: 0;
      font-size: var(--font-size-2xl);
      font-weight: 700;
      color: var(--text-color-primary);
      letter-spacing: -0.01em;
    }
  }
  
  .el-main {
    padding: 0;
  }
}

:deep(.el-card) {
  border: 1px solid var(--border-color-base);
  box-shadow: var(--box-shadow-base);
  margin-bottom: var(--spacing-lg);
  
  &:hover {
    box-shadow: var(--box-shadow-hover);
  }
}

:deep(.el-card__header) {
  border-bottom: 1px solid var(--border-color-light);
  padding: var(--spacing-md) var(--spacing-lg);
  
  span {
    font-weight: 600;
    font-size: var(--font-size-md);
    color: var(--text-color-primary);
  }
}

.form-tip {
  margin-left: var(--spacing-md);
  font-size: var(--font-size-sm);
  color: var(--text-color-secondary);
}

.settings-actions {
  margin-top: var(--spacing-xl);
  text-align: right;
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--border-color-light);
}

:deep(.el-form-item__label) {
  color: var(--text-color-regular);
  font-weight: 500;
}
</style>

