<template>
  <div class="settings-view" :class="themeClass">
    <!-- 环境渲染背景 -->
    <div class="ambient-layer">
      <div class="glow g-1"></div>
      <div class="glow g-2"></div>
      <div class="grain"></div>
    </div>

    <!-- 顶部社论式标题 -->
    <header class="settings-header">
      <button class="back-btn" @click="handleBack" title="返回">
        <el-icon><ArrowLeft /></el-icon>
      </button>
      <div class="header-left">
        <div class="system-meta">
          <span class="meta-tag">PREFERENCES</span>
          <span class="status-indicator">
            <span class="dot"></span> SYSTEM_STABLE
          </span>
        </div>
        <h1 class="grand-title">{{ $t('settings.title') }}</h1>
        <p class="tagline">配置您的智能助手，打造个性化的交互体验</p>
      </div>
      
      <div class="header-right">
        <div class="sync-info">
          <span class="label">LAST SYNCED</span>
          <span class="time">{{ lastSyncTime }}</span>
        </div>
      </div>
    </header>

    <!-- 主布局：侧边分类与内容区 -->
    <div class="settings-layout">
      <!-- 极简侧边导航 -->
      <aside class="settings-nav">
        <nav class="nav-list">
          <button 
            v-for="cat in menuCategories" 
            :key="cat.id"
            class="nav-item"
            :class="{ active: activeCategory === cat.id }"
            @click="activeCategory = cat.id"
          >
            <el-icon><component :is="cat.icon" /></el-icon>
            <span class="nav-label">{{ cat.label }}</span>
          </button>
        </nav>
      </aside>

      <!-- 设置内容区 -->
      <main class="settings-content">
        <transition name="fade-slide" mode="out-in">
          <div :key="activeCategory" class="category-wrapper">
            <!-- 通用设置 -->
            <div v-if="activeCategory === 'general'" class="settings-group">
              <h3 class="group-title">{{ $t('settings.general') }}</h3>
              <div class="art-card">
                <el-form label-position="top">
                  <div class="form-grid">
                    <el-form-item :label="$t('settings.theme')" class="grid-item">
                      <el-radio-group v-model="settings.theme" class="art-radio-group">
                        <el-radio-button label="light">{{ $t('settings.themeLight') }}</el-radio-button>
                        <el-radio-button label="dark">{{ $t('settings.themeDark') }}</el-radio-button>
                        <el-radio-button label="auto">{{ $t('settings.themeAuto') }}</el-radio-button>
                      </el-radio-group>
                    </el-form-item>

                    <el-form-item :label="$t('settings.language')" class="grid-item">
                      <el-select v-model="settings.language" @change="handleLanguageChange" class="art-select">
                        <el-option :label="$t('settings.languageZhCN')" value="zh-CN" />
                        <el-option :label="$t('settings.languageEn')" value="en" />
                      </el-select>
                    </el-form-item>

                    <el-form-item :label="$t('settings.fontSize')" class="grid-item full-width">
                      <div class="slider-box">
                        <el-slider v-model="settings.fontSize" :min="12" :max="20" class="art-slider" />
                        <span class="slider-val">{{ settings.fontSize }}px</span>
                      </div>
                    </el-form-item>

                    <el-form-item :label="$t('settings.primaryColor')" class="grid-item">
                      <el-color-picker v-model="settings.primaryColor" @change="applyTheme" class="art-color-picker" />
                    </el-form-item>

                    <el-form-item :label="$t('settings.backgroundStyle')" class="grid-item full-width">
                      <el-radio-group v-model="settings.backgroundStyle" @change="applyTheme" class="art-pill-group">
                        <el-radio label="default">{{ $t('settings.backgroundDefault') }}</el-radio>
                        <el-radio label="mesh">{{ $t('settings.backgroundMesh') }}</el-radio>
                        <el-radio label="image">{{ $t('settings.backgroundImage') }}</el-radio>
                      </el-radio-group>
                    </el-form-item>
                  </div>
                </el-form>
              </div>
            </div>

            <!-- 隐私与安全 -->
            <div v-if="activeCategory === 'privacy'" class="settings-group">
              <h3 class="group-title">{{ $t('settings.privacy') }}</h3>
              <div class="art-card">
                <el-form label-position="top">
                  <el-form-item :label="$t('settings.storageLocation')">
                    <el-radio-group v-model="settings.storageLocation" class="art-radio-group">
                      <el-radio-button label="local">{{ $t('settings.storageLocal') }}</el-radio-button>
                      <el-radio-button label="cloud">{{ $t('settings.storageCloud') }}</el-radio-button>
                    </el-radio-group>
                    <p class="form-tip">{{ $t('settings.storageTip') }}</p>
                  </el-form-item>

                  <el-form-item :label="$t('settings.autoDelete')">
                    <el-select v-model="settings.autoDelete" class="art-select">
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
                      class="art-input"
                    />
                  </el-form-item>
                </el-form>
              </div>
            </div>

            <!-- 对话设置 -->
            <div v-if="activeCategory === 'chat'" class="settings-group">
              <h3 class="group-title">{{ $t('settings.chat') }}</h3>
              <div class="art-card">
                <el-form label-position="top">
                  <div class="switch-item">
                    <div class="switch-info">
                      <span class="label">{{ $t('settings.autoSend') }}</span>
                      <span class="desc">{{ $t('settings.autoSendTip') }}</span>
                    </div>
                    <el-switch v-model="settings.autoSend" class="art-switch" />
                  </div>

                  <div class="switch-item">
                    <div class="switch-info">
                      <span class="label">{{ $t('settings.messageSound') }}</span>
                      <span class="desc">收到AI回复时播放提示音</span>
                    </div>
                    <el-switch v-model="settings.messageSound" class="art-switch" />
                  </div>

                  <el-form-item :label="$t('settings.historyRetention')" style="margin-top: 24px">
                    <el-select v-model="settings.historyRetention" class="art-select">
                      <el-option :label="$t('settings.historyRetention1')" value="1" />
                      <el-option :label="$t('settings.historyRetention7')" value="7" />
                      <el-option :label="$t('settings.historyRetention30')" value="30" />
                      <el-option :label="$t('settings.historyRetentionForever')" value="forever" />
                    </el-select>
                  </el-form-item>
                </el-form>
              </div>
            </div>

            <!-- 数字人设置 -->
            <div v-if="activeCategory === 'digital'" class="settings-group">
              <h3 class="group-title">{{ $t('settings.digitalHuman') }}</h3>
              <div class="art-card">
                <el-form label-position="top">
                  <el-form-item :label="$t('settings.renderQuality')">
                    <el-select v-model="settings.renderQuality" class="art-select">
                      <el-option :label="$t('settings.renderQualityHigh')" value="high" />
                      <el-option :label="$t('settings.renderQualityMedium')" value="medium" />
                      <el-option :label="$t('settings.renderQualityLow')" value="low" />
                    </el-select>
                  </el-form-item>

                  <el-form-item :label="$t('settings.animationSmoothness')">
                    <div class="slider-box">
                      <el-slider v-model="settings.animationSmoothness" :min="30" :max="60" class="art-slider" />
                      <span class="slider-val">{{ settings.animationSmoothness }} FPS</span>
                    </div>
                  </el-form-item>
                </el-form>
              </div>
            </div>

            <!-- 语音设置 -->
            <div v-if="activeCategory === 'voice'" class="settings-group">
              <h3 class="group-title">{{ $t('settings.voice') }}</h3>
              <div class="art-card-transparent">
                <VoiceSettings 
                  :initial-voice="settings.voice"
                  :initial-speed="settings.speed"
                  :initial-pitch="settings.pitch"
                  @change="handleVoiceSettingsChange" 
                />
              </div>
            </div>
          </div>
        </transition>
      </main>
    </div>

    <!-- 底部固定的操作栏 -->
    <footer class="settings-footer">
      <div class="footer-inner">
        <div class="footer-info">
          <el-icon><InfoFilled /></el-icon>
          <span>所有修改将实时同步至您的账户</span>
        </div>
        <div class="footer-actions">
          <button class="reset-btn" @click="resetSettings">{{ $t('common.reset') }}</button>
          <button class="save-btn" @click="saveSettings">{{ $t('settings.saveButton') }}</button>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import ElementPlus from 'element-plus'
import zhCN from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'
import { 
  Setting, Lock, ChatDotRound, UserFilled, Microphone, 
  ArrowLeft, InfoFilled, Moon, Sunny, Top 
} from '@element-plus/icons-vue'
import VoiceSettings from '@/components/VoiceSettings.vue'

const { t, locale } = useI18n()
const router = useRouter()

const handleBack = () => {
  router.push('/chat')
}

const lastSyncTime = ref(new Date().toLocaleTimeString())
const activeCategory = ref('general')
const isDark = computed(() => settings.value.theme === 'dark')
const themeClass = computed(() => `theme-${settings.value.theme}`)

const menuCategories = [
  { id: 'general', label: t('settings.general'), icon: Setting },
  { id: 'privacy', label: t('settings.privacy'), icon: Lock },
  { id: 'chat', label: t('settings.chat'), icon: ChatDotRound },
  { id: 'digital', label: t('settings.digitalHuman'), icon: UserFilled },
  { id: 'voice', label: t('settings.voice'), icon: Microphone },
]

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
  saveSettings(false)
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

const saveSettings = (showMessage = true) => {
  localStorage.setItem('appSettings', JSON.stringify(settings.value))
  applyTheme()
  if (showMessage) {
    ElMessage({
      message: t('settings.saveSuccess'),
      type: 'success',
      customClass: 'art-message'
    })
  }
  lastSyncTime.value = new Date().toLocaleTimeString()
}

const resetSettings = () => {
  settings.value = {
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
  }
  locale.value = 'zh-CN'
  updateElementPlusLocale('zh-CN')
  localStorage.removeItem('appSettings')
  applyTheme()
  ElMessage.success(t('settings.resetSuccess'))
}

const handleVoiceSettingsChange = (voiceSettings: { voice: string; speed: number; pitch: number }) => {
  settings.value.voice = voiceSettings.voice
  settings.value.speed = voiceSettings.speed
  settings.value.pitch = voiceSettings.pitch
  // 语音设置变化时自动保存
  localStorage.setItem('appSettings', JSON.stringify(settings.value))
}

const toggleTheme = () => {
  settings.value.theme = settings.value.theme === 'dark' ? 'light' : 'dark'
  saveSettings(false)
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped lang="scss">
.settings-view {
  --bg: #f8f9fb;
  --text: #1a1a1a;
  --text-dim: #718096;
  --accent: #4f46e5;
  --border: rgba(0, 0, 0, 0.05);
  --card-bg: #ffffff;
  --nav-bg: #ffffff;
  
  &.theme-dark {
    --bg: #02040a;
    --text: #f8fafc;
    --text-dim: rgba(255, 255, 255, 0.45);
    --accent: #6366f1;
    --border: rgba(255, 255, 255, 0.06);
    --card-bg: rgba(255, 255, 255, 0.02);
    --nav-bg: rgba(255, 255, 255, 0.01);
  }

  position: relative;
  height: 100vh;
  width: 100%;
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', -apple-system, system-ui, sans-serif;
  transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* --- 环境层 --- */
.ambient-layer {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  .glow { position: absolute; border-radius: 50%; filter: blur(120px); opacity: 0.1; }
  .g-1 { top: -10%; right: -5%; width: 50%; height: 50%; background: var(--accent); }
  .g-2 { bottom: -5%; left: -5%; width: 40%; height: 40%; background: #10b981; opacity: 0.05; }
  .grain { position: absolute; inset: 0; opacity: 0.02; background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"); }
}

/* --- Header --- */
.settings-header {
  position: relative;
  z-index: 10;
  height: 140px;
  padding: 0 80px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;

  .system-meta {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 12px;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 2px;
    .meta-tag { color: var(--accent); }
    .status-indicator {
      color: var(--text-dim);
      display: flex;
      align-items: center;
      gap: 6px;
      .dot { width: 4px; height: 4px; background: #10b981; border-radius: 50%; }
    }
  }

  .grand-title { font-size: 32px; font-weight: 800; letter-spacing: -1px; margin: 0; }
  .tagline { font-size: 14px; color: var(--text-dim); margin: 4px 0 0 0; }

  .header-right {
    .sync-info {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      .label { font-size: 9px; font-weight: 900; color: var(--text-dim); letter-spacing: 1px; }
      .time { font-size: 14px; font-weight: 700; font-family: 'JetBrains Mono', monospace; margin-top: 4px; }
    }
  }
}

/* --- Layout --- */
.settings-layout {
  position: relative;
  z-index: 1;
  flex: 1;
  display: grid;
  grid-template-columns: 280px 1fr;
  padding: 0 80px 100px;
  gap: 60px;
  overflow: hidden;
}

/* --- Sidebar Nav --- */
.settings-nav {
  .nav-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    
    .nav-item {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 16px 24px;
      background: transparent;
      border: 1px solid transparent;
      border-radius: 16px;
      color: var(--text-dim);
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      
      .el-icon { font-size: 18px; }
      
      &:hover {
        background: var(--nav-bg);
        color: var(--text);
      }
      
      &.active {
        background: var(--card-bg);
        border-color: var(--border);
        color: var(--accent);
        box-shadow: 0 4px 20px rgba(0,0,0,0.02);
      }
    }
  }
}

/* --- Content --- */
.settings-content {
  overflow-y: auto;
  padding-right: 20px;
  
  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }

  .category-wrapper {
    max-width: 800px;
  }

  .group-title {
    font-size: 20px;
    font-weight: 800;
    margin: 0 0 32px 0;
    letter-spacing: -0.5px;
  }

  .art-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 32px;
    padding: 40px;
    backdrop-filter: blur(20px);
  }

  .art-card-transparent {
    background: transparent;
  }
}

/* --- Form Art --- */
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  
  .grid-item {
    margin-bottom: 0;
    &.full-width { grid-column: span 2; }
  }
}

:deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 800;
  color: var(--text-dim) !important;
  text-transform: uppercase;
  letter-spacing: 1px;
  padding-bottom: 12px !important;
}

.slider-box {
  display: flex;
  align-items: center;
  gap: 24px;
  .art-slider { flex: 1; }
  .slider-val { font-size: 13px; font-weight: 800; font-family: 'JetBrains Mono'; min-width: 60px; text-align: right; }
}

.art-pill-group {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  :deep(.el-radio) {
    margin-right: 0;
    padding: 10px 20px;
    border-radius: 12px;
    border: 1px solid var(--border);
    background: var(--glass);
    transition: all 0.3s;
    &.is-checked { border-color: var(--accent); background: rgba(99, 102, 241, 0.05); }
    .el-radio__input { display: none; }
    .el-radio__label { padding-left: 0; font-weight: 700; font-size: 13px; }
  }
}

.art-radio-group {
  background: var(--glass);
  padding: 4px;
  border-radius: 12px;
  border: 1px solid var(--border);
  :deep(.el-radio-button__inner) {
    background: transparent;
    border: none;
    box-shadow: none;
    font-size: 12px;
    font-weight: 800;
    padding: 10px 20px;
    color: var(--text-dim);
    border-radius: 10px;
  }
  :deep(.el-radio-button.is-active .el-radio-button__inner) {
    background: var(--text);
    color: var(--bg);
  }
}

.switch-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 0;
  border-bottom: 1px solid var(--border);
  &:first-child { padding-top: 0; }
  &:last-child { border-bottom: none; }
  
  .switch-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
    .label { font-size: 15px; font-weight: 700; }
    .desc { font-size: 12px; color: var(--text-dim); }
  }
}

.form-tip {
  margin-top: 12px;
  font-size: 12px;
  color: var(--text-dim);
  line-height: 1.6;
}

/* --- Footer --- */
.settings-footer {
  position: relative;
  z-index: 20;
  height: 100px;
  background: var(--bg);
  border-top: 1px solid var(--border);
  padding: 0 80px;
  display: flex;
  align-items: center;
  flex-shrink: 0;

  .footer-inner {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .footer-info {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-dim);
    .el-icon { font-size: 16px; color: var(--accent); }
  }

  .footer-actions {
    display: flex;
    gap: 16px;
    
    .reset-btn {
      height: 48px; padding: 0 32px; background: transparent; border: 1px solid var(--border);
      border-radius: 14px; color: var(--text); font-size: 13px; font-weight: 800; cursor: pointer;
      transition: all 0.3s;
      &:hover { background: var(--btn-hover); }
    }

    .save-btn {
      height: 48px; padding: 0 40px; background: var(--accent); color: white; border: none;
      border-radius: 14px; font-size: 13px; font-weight: 900; letter-spacing: 1px; cursor: pointer;
      transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      &:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3); }
    }
  }
}

/* --- Transitions --- */
.fade-slide-enter-active, .fade-slide-leave-active { transition: all 0.4s ease; }
.fade-slide-enter-from { opacity: 0; transform: translateY(10px); }
.fade-slide-leave-to { opacity: 0; transform: translateY(-10px); }

/* --- Global Overrides --- */
:deep(.el-input__wrapper), :deep(.el-select .el-input__wrapper) {
  background-color: var(--glass) !important;
  box-shadow: none !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  padding: 8px 16px !important;
}

:deep(.el-input__inner) { font-weight: 600; font-size: 14px; }
</style>
