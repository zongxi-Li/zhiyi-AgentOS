<template>
  <div class="voice-chat-view" :class="{ 'is-speaking': isSpeaking, 'is-recording': isRecording }">
    <!-- 背景氛围层 - 丰富的动效 -->
    <div class="ambient-background">
      <div class="wave-layer wave-1"></div>
      <div class="wave-layer wave-2"></div>
      <div class="wave-layer wave-3"></div>
      <div class="particle-layer">
        <div class="particle" v-for="i in 20" :key="i" :style="getParticleStyle(i)"></div>
      </div>
      <div class="glow-orb orb-1" :class="{ 'active': isRecording || isSpeaking }"></div>
      <div class="glow-orb orb-2" :class="{ 'active': isRecording || isSpeaking }"></div>
    </div>

    <!-- 主体内容区 -->
    <div class="main-content">
      <!-- 数字人展示区 -->
      <div class="digital-human-container">
        <div class="digital-human-wrapper" :class="{ 'speaking': isSpeaking, 'recording': isRecording }">
          <DigitalHuman
            :role-id="roleStore.currentRole?.id"
            :is-speaking="isSpeaking"
            :audio-url="currentAudioUrl"
            :transparent="true"
            class="digital-human-entity"
          />
        </div>
        
        <!-- 状态指示器 -->
        <transition name="fade-scale">
          <div class="status-indicator" v-if="processing || isRecording">
            <div class="status-dot" :class="{ 'pulse': isRecording, 'thinking': processing }"></div>
            <span class="status-text">
              {{ isRecording ? '聆听中...' : (processing ? '思考中...' : '') }}
            </span>
          </div>
        </transition>

        <!-- 音频波形可视化 -->
        <transition name="fade-scale">
          <div class="audio-visualizer" v-if="isSpeaking || isRecording">
            <div class="wave-bar" v-for="i in 20" :key="i" :style="getWaveBarStyle(i)"></div>
          </div>
        </transition>
      </div>

      <!-- 识别文本展示 -->
      <transition name="slide-up-fade">
        <div class="transcription-area" v-if="recognizedText">
          <div class="transcription-bubble">
            <div class="transcription-icon">
              <el-icon><Microphone /></el-icon>
            </div>
            <div class="transcription-text">{{ recognizedText }}</div>
          </div>
        </div>
      </transition>

      <!-- 悬浮控制台 -->
      <div class="control-bar" :class="{ 'settings-expanded': showSettings }">
        <!-- 核心控制区 -->
        <div class="control-core">
          <VoiceRecorder
            @recorded="handleVoiceRecorded"
            @recording-start="handleRecordingStart"
            @recording-end="handleRecordingEnd"
            @realtime-text="handleRealtimeText"
            :disabled="processing"
            :enable-realtime="true"
            class="main-recorder-btn"
          />
          
          <!-- 播放器 -->
          <VoicePlayer
            v-if="responseAudioUrl"
            :audio-url="responseAudioUrl"
            @playing="handlePlaying"
            @stopped="handleStopped"
            v-show="false" 
          />
        </div>

        <!-- 扩展设置开关 -->
        <button class="settings-toggle" @click="showSettings = !showSettings">
          <el-icon class="toggle-icon" :class="{ 'rotated': showSettings }"><Setting /></el-icon>
          <span class="toggle-text">{{ showSettings ? '收起设置' : '语音设置' }}</span>
        </button>

        <!-- 可折叠的参数面板 -->
        <transition name="expand">
          <div class="voice-params-panel" v-if="showSettings">
            <div class="panel-header">
              <h3 class="panel-title">语音参数</h3>
              <p class="panel-subtitle">调整语音输出效果</p>
            </div>
            
            <div class="params-content">
              <div class="param-item">
                <div class="param-header">
                  <span class="param-label">语速</span>
                  <span class="param-value">{{ voiceSpeed.toFixed(1) }}x</span>
                </div>
                <el-slider
                  v-model="voiceSpeed"
                  :min="0.5"
                  :max="2.0"
                  :step="0.1"
                  size="small"
                  class="custom-slider"
                />
              </div>
              
              <div class="param-item">
                <div class="param-header">
                  <span class="param-label">音调</span>
                  <span class="param-value">{{ voicePitch.toFixed(1) }}x</span>
                </div>
                <el-slider
                  v-model="voicePitch"
                  :min="0.5"
                  :max="2.0"
                  :step="0.1"
                  size="small"
                  class="custom-slider"
                />
              </div>

              <div class="param-item">
                <div class="param-header">
                  <span class="param-label">语音类型</span>
                </div>
                <el-select v-model="voiceType" size="small" class="voice-select">
                  <el-option label="默认" value="default" />
                  <el-option label="女声" value="female" />
                  <el-option label="男声" value="male" />
                  <el-option label="温柔" value="gentle" />
                  <el-option label="活泼" value="lively" />
                </el-select>
              </div>

              <button class="test-button" @click="handleTestVoice">
                <el-icon><VideoPlay /></el-icon>
                <span>试听效果</span>
              </button>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Microphone, Setting, VideoPlay } from '@element-plus/icons-vue'
import { useRoleStore } from '@/stores/role'
import DigitalHuman from '@/components/DigitalHuman.vue'
import VoiceRecorder from '@/components/VoiceRecorder.vue'
import VoicePlayer from '@/components/VoicePlayer.vue'
import { voiceApi } from '@/services/api/voice'

const roleStore = useRoleStore()
const isSpeaking = ref(false)
const isRecording = ref(false)
const processing = ref(false)
const showSettings = ref(false)
const recognizedText = ref('')
const currentAudioUrl = ref<string>('')
const responseAudioUrl = ref<string>('')
const voiceSpeed = ref(1.0)
const voicePitch = ref(1.0)
const voiceType = ref('default')
const waveAnimationFrame = ref<number>()

onMounted(async () => {
  await roleStore.loadBuiltinRoles()
  if (roleStore.builtinRoles.length > 0 && !roleStore.currentRole) {
    roleStore.selectRole(roleStore.builtinRoles[0])
  }
  startWaveAnimation()
})

onUnmounted(() => {
  if (waveAnimationFrame.value) {
    cancelAnimationFrame(waveAnimationFrame.value)
  }
})

const handleRecordingStart = () => {
  isRecording.value = true
}

const handleRecordingEnd = () => {
  isRecording.value = false
}

const handleRealtimeText = (text: string) => {
  // 实时识别文本更新
  if (text) {
    recognizedText.value = text
  }
}

const handleVoiceRecorded = async (audioBlob: Blob) => {
  isRecording.value = false
  processing.value = true
  recognizedText.value = ''

  try {
    const audioFile = new File([audioBlob], 'recording.wav', { type: 'audio/wav' })
    
    const response = await voiceApi.sendVoiceMessage({
      audio: audioFile,
      roleId: roleStore.currentRole?.id
    })

    recognizedText.value = response.recognizedText || response.text

    if (response.text) {
      const audioBlob = await voiceApi.textToSpeech(
        response.text, 
        voiceType.value,
        voiceSpeed.value, 
        voicePitch.value
      )
      responseAudioUrl.value = URL.createObjectURL(audioBlob)
    }
  } catch (error: any) {
    ElMessage.error('语音处理失败: ' + (error.message || '未知错误'))
  } finally {
    processing.value = false
  }
}

const handlePlaying = () => {
  isSpeaking.value = true
}

const handleStopped = () => {
  isSpeaking.value = false
}

const handleTestVoice = async () => {
  try {
    const testText = '这是语音测试，请听效果。'
    const audioBlob = await voiceApi.textToSpeech(
      testText, 
      voiceType.value,
      voiceSpeed.value, 
      voicePitch.value
    )
    const audioUrl = URL.createObjectURL(audioBlob)
    const audio = new Audio(audioUrl)
    audio.play()
    
    audio.onended = () => {
      URL.revokeObjectURL(audioUrl)
    }
    ElMessage.success('正在播放试听')
  } catch (error: any) {
    ElMessage.error('试听失败: ' + (error.message || '未知错误'))
  }
}

// 粒子样式生成
const getParticleStyle = (index: number) => {
  const delay = (index * 0.1) % 2
  const duration = 3 + (index % 3)
  const size = 2 + (index % 3)
  const left = (index * 5) % 100
  return {
    left: `${left}%`,
    width: `${size}px`,
    height: `${size}px`,
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`
  }
}

// 波形条样式生成
const getWaveBarStyle = (index: number) => {
  const delay = index * 0.05
  const height = 20 + Math.sin(index * 0.5) * 15
  return {
    animationDelay: `${delay}s`,
    height: `${height}%`
  }
}

// 启动波形动画
const startWaveAnimation = () => {
  const animate = () => {
    waveAnimationFrame.value = requestAnimationFrame(animate)
  }
  animate()
}
</script>

<style scoped>
/* 字体引入 */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

.voice-chat-view {
  position: relative;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: #0a0d14;
  color: #ffffff;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* --- 背景氛围层 - 丰富的动效 --- */
.ambient-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  overflow: hidden;
}

/* 波形层 */
.wave-layer {
  position: absolute;
  width: 200%;
  height: 100%;
  opacity: 0.15;
  background: linear-gradient(90deg, transparent, rgba(64, 158, 255, 0.3), transparent);
  animation: wave-flow 20s linear infinite;
}

.wave-1 {
  top: 20%;
  animation-duration: 25s;
  animation-delay: 0s;
}

.wave-2 {
  top: 50%;
  animation-duration: 30s;
  animation-delay: -10s;
  opacity: 0.1;
}

.wave-3 {
  top: 80%;
  animation-duration: 35s;
  animation-delay: -5s;
  opacity: 0.08;
}

@keyframes wave-flow {
  0% { transform: translateX(-50%) translateY(0); }
  100% { transform: translateX(0) translateY(0); }
}

/* 粒子层 */
.particle-layer {
  position: absolute;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.particle {
  position: absolute;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 50%;
  animation: particle-float linear infinite;
}

@keyframes particle-float {
  0% {
    transform: translateY(100vh) translateX(0) rotate(0deg);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(-10vh) translateX(100px) rotate(360deg);
    opacity: 0;
  }
}

/* 光球 */
.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.2;
  transition: opacity 0.5s ease, transform 0.5s ease;
}

.orb-1 {
  top: -15%;
  left: -10%;
  width: 500px;
  height: 500px;
  background: rgba(64, 158, 255, 0.4);
  animation: orb-float-1 15s ease-in-out infinite;
}

.orb-2 {
  bottom: -15%;
  right: -10%;
  width: 450px;
  height: 450px;
  background: rgba(103, 126, 255, 0.3);
  animation: orb-float-2 18s ease-in-out infinite;
  animation-delay: -7s;
}

.glow-orb.active {
  opacity: 0.35;
  transform: scale(1.1);
}

@keyframes orb-float-1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, 40px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

@keyframes orb-float-2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-30px, -40px) scale(1.05); }
  66% { transform: translate(20px, -20px) scale(0.95); }
}

/* --- 主体内容 --- */
.main-content {
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  padding: 40px 20px 120px;
}

/* 数字人容器 */
.digital-human-container {
  flex: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  min-height: 400px;
}

.digital-human-wrapper {
  position: relative;
  transition: transform 0.3s ease;
}

.digital-human-wrapper.speaking {
  animation: speaking-pulse 2s ease-in-out infinite;
}

.digital-human-wrapper.recording {
  animation: recording-pulse 1.5s ease-in-out infinite;
}

@keyframes speaking-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}

@keyframes recording-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.03); }
}

.digital-human-entity {
  max-height: 70vh;
  transition: opacity 0.3s ease;
}

/* 状态指示器 */
.status-indicator {
  position: absolute;
  top: 15%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  z-index: 10;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #ffffff;
}

.status-dot.pulse {
  background: #ff4757;
  animation: pulse-red 1.5s ease-in-out infinite;
}

.status-dot.thinking {
  background: #409eff;
  animation: thinking-bounce 1.2s ease-in-out infinite;
}

.status-text {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.85);
  letter-spacing: 0.5px;
  text-transform: uppercase;
  font-size: 11px;
}

@keyframes pulse-red {
  0%, 100% { 
    transform: scale(1);
    opacity: 1;
  }
  50% { 
    transform: scale(1.3);
    opacity: 0.7;
  }
}

@keyframes thinking-bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

/* 音频波形可视化 */
.audio-visualizer {
  position: absolute;
  bottom: 20%;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  height: 40px;
  z-index: 5;
}

.wave-bar {
  width: 3px;
  background: rgba(64, 158, 255, 0.8);
  border-radius: 2px;
  animation: wave-animate 1.2s ease-in-out infinite;
}

@keyframes wave-animate {
  0%, 100% { transform: scaleY(0.3); }
  50% { transform: scaleY(1); }
}

/* 识别文本气泡 */
.transcription-area {
  margin-bottom: 30px;
  width: 85%;
  max-width: 650px;
  text-align: center;
  min-height: 70px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.transcription-bubble {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
  padding: 16px 24px;
  border-radius: 16px;
  font-size: 15px;
  line-height: 1.6;
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.12);
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: 100%;
  word-wrap: break-word;
}

.transcription-icon {
  color: rgba(64, 158, 255, 0.9);
  font-size: 18px;
  flex-shrink: 0;
}

.transcription-text {
  flex: 1;
  text-align: left;
  font-weight: 400;
}

/* --- 控制台 --- */
.control-bar {
  position: fixed;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 520px;
  background: rgba(20, 22, 28, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 100;
}

.control-bar.settings-expanded {
  padding-bottom: 24px;
}

.control-core {
  display: flex;
  justify-content: center;
  width: 100%;
}

/* 录音按钮样式 */
:deep(.voice-recorder-btn) {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: #409eff;
  border: 2px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

:deep(.voice-recorder-btn:hover) {
  transform: scale(1.08);
  background: #5dade2;
}

:deep(.voice-recorder-btn:active) {
  transform: scale(0.95);
}

.voice-chat-view.is-recording :deep(.voice-recorder-btn) {
  background: #ff4757;
  animation: recording-glow 1.5s ease-in-out infinite;
}

@keyframes recording-glow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255, 71, 87, 0.4); }
  50% { box-shadow: 0 0 0 12px rgba(255, 71, 87, 0); }
}

.settings-toggle {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.settings-toggle:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.05);
}

.toggle-icon {
  font-size: 16px;
  transition: transform 0.3s ease;
}

.toggle-icon.rotated {
  transform: rotate(180deg);
}

.toggle-text {
  font-size: 13px;
}

/* 参数面板 */
.voice-params-panel {
  width: 100%;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 14px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.panel-header {
  margin-bottom: 4px;
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 4px 0;
  letter-spacing: -0.01em;
}

.panel-subtitle {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.params-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.param-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.param-label {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.85);
}

.param-value {
  font-size: 13px;
  font-weight: 600;
  color: #409eff;
  min-width: 40px;
  text-align: right;
}

.custom-slider {
  --el-slider-main-bg-color: #409eff;
  --el-slider-runway-bg-color: rgba(255, 255, 255, 0.15);
  --el-slider-button-size: 16px;
}

.voice-select {
  width: 100%;
}

.test-button {
  width: 100%;
  padding: 12px;
  background: rgba(64, 158, 255, 0.15);
  border: 1px solid rgba(64, 158, 255, 0.3);
  border-radius: 10px;
  color: #409eff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s ease;
  margin-top: 4px;
}

.test-button:hover {
  background: rgba(64, 158, 255, 0.25);
  border-color: rgba(64, 158, 255, 0.5);
  transform: translateY(-1px);
}

/* 过渡动画 */
.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: all 0.3s ease;
}

.fade-scale-enter-from,
.fade-scale-leave-to {
  opacity: 0;
  transform: scale(0.9);
}

.slide-up-fade-enter-active,
.slide-up-fade-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-up-fade-enter-from,
.slide-up-fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
  margin-top: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.expand-enter-to,
.expand-leave-from {
  max-height: 500px;
  opacity: 1;
}
</style>