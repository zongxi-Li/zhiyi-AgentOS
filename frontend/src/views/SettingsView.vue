<template>
  <div class="settings-view">
    <el-container>
      <el-header>
        <h2>{{ $t('settings.title') }}</h2>
      </el-header>
      <el-main>
        <el-card>
          <template #header>
            <span>{{ $t('settings.general') }}</span>
          </template>
          
          <el-form label-width="150px">
            <el-form-item :label="$t('settings.theme')">
              <el-radio-group v-model="settings.theme">
                <el-radio label="light">{{ $t('settings.themeLight') }}</el-radio>
                <el-radio label="dark">{{ $t('settings.themeDark') }}</el-radio>
                <el-radio label="auto">{{ $t('settings.themeAuto') }}</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item :label="$t('settings.language')">
              <el-select v-model="settings.language" @change="handleLanguageChange">
                <el-option :label="$t('settings.languageZhCN')" value="zh-CN" />
                <el-option :label="$t('settings.languageEn')" value="en" />
              </el-select>
            </el-form-item>

            <el-form-item :label="$t('settings.fontSize')">
              <el-slider v-model="settings.fontSize" :min="12" :max="20" />
            </el-form-item>

            <el-form-item :label="$t('settings.primaryColor')">
              <el-color-picker v-model="settings.primaryColor" @change="applyTheme" />
            </el-form-item>

            <el-form-item :label="$t('settings.backgroundStyle')">
              <el-radio-group v-model="settings.backgroundStyle" @change="applyTheme">
                <el-radio label="default">{{ $t('settings.backgroundDefault') }}</el-radio>
                <el-radio label="mesh">{{ $t('settings.backgroundMesh') }}</el-radio>
                <el-radio label="image">{{ $t('settings.backgroundImage') }}</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card style="margin-top: 20px">
          <template #header>
            <span>{{ $t('settings.privacy') }}</span>
          </template>
          
          <el-form label-width="150px">
            <el-form-item :label="$t('settings.storageLocation')">
              <el-radio-group v-model="settings.storageLocation">
                <el-radio label="local">{{ $t('settings.storageLocal') }}</el-radio>
                <el-radio label="cloud">{{ $t('settings.storageCloud') }}</el-radio>
              </el-radio-group>
              <div class="form-tip">{{ $t('settings.storageTip') }}</div>
            </el-form-item>

            <el-form-item :label="$t('settings.autoDelete')">
              <el-select v-model="settings.autoDelete">
                <el-option :label="$t('settings.autoDeleteNever')" value="never" />
                <el-option :label="$t('settings.autoDelete7')" value="7" />
                <el-option :label="$t('settings.autoDelete30')" value="30" />
              </el-select>
            </el-form-item>

            <el-form-item :label="$t('settings.privacyPassword')">
              <el-input 
                v-model="settings.privacyPassword" 
                type="password" 
                show-password 
                :placeholder="$t('settings.privacyPasswordPlaceholder')"
              />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card style="margin-top: 20px">
          <template #header>
            <span>{{ $t('settings.chat') }}</span>
          </template>
          
          <el-form label-width="150px">
            <el-form-item :label="$t('settings.autoSend')">
              <el-switch v-model="settings.autoSend" />
              <span class="form-tip">{{ $t('settings.autoSendTip') }}</span>
            </el-form-item>

            <el-form-item :label="$t('settings.messageSound')">
              <el-switch v-model="settings.messageSound" />
            </el-form-item>

            <el-form-item :label="$t('settings.historyRetention')">
              <el-select v-model="settings.historyRetention">
                <el-option :label="$t('settings.historyRetention1')" value="1" />
                <el-option :label="$t('settings.historyRetention7')" value="7" />
                <el-option :label="$t('settings.historyRetention30')" value="30" />
                <el-option :label="$t('settings.historyRetentionForever')" value="forever" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card style="margin-top: 20px">
          <template #header>
            <span>{{ $t('settings.digitalHuman') }}</span>
          </template>
          
          <el-form label-width="150px">
            <el-form-item :label="$t('settings.renderQuality')">
              <el-select v-model="settings.renderQuality">
                <el-option :label="$t('settings.renderQualityHigh')" value="high" />
                <el-option :label="$t('settings.renderQualityMedium')" value="medium" />
                <el-option :label="$t('settings.renderQualityLow')" value="low" />
              </el-select>
            </el-form-item>

            <el-form-item :label="$t('settings.animationSmoothness')">
              <el-slider v-model="settings.animationSmoothness" :min="30" :max="60" />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card style="margin-top: 20px">
          <template #header>
            <span>{{ $t('settings.voice') }}</span>
          </template>
          
          <VoiceSettings @change="handleVoiceSettingsChange" />
        </el-card>

        <div class="settings-actions">
          <el-button type="primary" @click="saveSettings">{{ $t('settings.saveButton') }}</el-button>
          <el-button @click="resetSettings">{{ $t('common.reset') }}</el-button>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import ElementPlus from 'element-plus'
import zhCN from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'
import VoiceSettings from '@/components/VoiceSettings.vue'

const { t, locale } = useI18n()

const settings = ref({
  theme: 'light',
  language: 'zh-CN',
  fontSize: 14,
  primaryColor: '#4f46e5',
  backgroundStyle: 'default',
  storageLocation: 'local',
  autoDelete: 'never',
  privacyPassword: '',
  autoSend: false,
  messageSound: true,
  historyRetention: '7',
  renderQuality: 'medium',
  animationSmoothness: 45,
  voice: 'default',
  speed: 1.0,
  pitch: 1.0
})

// 更新 Element Plus 语言
const updateElementPlusLocale = (lang: string) => {
  const elementLocale = lang === 'en' ? en : zhCN
  ElementPlus.locale(elementLocale)
}

// 处理语言切换
const handleLanguageChange = (newLang: string) => {
  locale.value = newLang
  updateElementPlusLocale(newLang)
  // 立即保存语言设置
  const currentSettings = { ...settings.value, language: newLang }
  localStorage.setItem('appSettings', JSON.stringify(currentSettings))
  ElMessage.success(t('settings.saveSuccess'))
}

const applyTheme = () => {
  const root = document.documentElement
  if (settings.value.primaryColor) {
    root.style.setProperty('--primary-color', settings.value.primaryColor)
  }
  
  if (settings.value.backgroundStyle === 'mesh') {
    document.body.style.backgroundImage = 'radial-gradient(at 0% 0%, var(--primary-fade) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(59, 130, 246, 0.03) 0px, transparent 50%)'
  } else if (settings.value.backgroundStyle === 'default') {
    document.body.style.backgroundImage = ''
  }
}

const loadSettings = () => {
  const saved = localStorage.getItem('appSettings')
  if (saved) {
    try {
      const savedSettings = JSON.parse(saved)
      settings.value = { ...settings.value, ...savedSettings }
      
      // 恢复语言设置
      if (savedSettings.language) {
        locale.value = savedSettings.language
        updateElementPlusLocale(savedSettings.language)
      }
      
      applyTheme()
    } catch (e) {
      console.error('加载设置失败', e)
    }
  }
}

const saveSettings = () => {
  localStorage.setItem('appSettings', JSON.stringify(settings.value))
  applyTheme()
  ElMessage.success(t('settings.saveSuccess'))
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
  locale.value = 'zh-CN'
  updateElementPlusLocale('zh-CN')
  localStorage.removeItem('appSettings')
  ElMessage.success(t('settings.resetSuccess'))
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
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  
  .el-container {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  
  .el-header {
    flex-shrink: 0;
    padding: var(--spacing-lg) var(--spacing-xl);
    border-bottom: 1px solid var(--border-color-base);
    
    h2 {
      margin: 0;
      font-size: var(--font-size-2xl);
      font-weight: 700;
      color: var(--text-color-primary);
      letter-spacing: -0.01em;
    }
  }
  
  .el-main {
    flex: 1;
    padding: var(--spacing-xl);
    overflow-y: auto;
    overflow-x: hidden;
    max-width: 1200px;
    width: 100%;
    margin: 0 auto;
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

