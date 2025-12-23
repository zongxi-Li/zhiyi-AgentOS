<template>
  <div class="voice-chat-view" :class="{ 'is-speaking': isSpeaking }">
    <!-- 背景氛围层 -->
    <div class="ambient-background">
      <div class="glow-orb orb-1"></div>
      <div class="glow-orb orb-2"></div>
    </div>

    <!-- 主体内容区 -->
    <div class="main-content">
      <!-- 数字人展示区 -->
      <div class="digital-human-container">
        <DigitalHuman
          :role-id="roleStore.currentRole?.id"
          :is-speaking="isSpeaking"
          :audio-url="currentAudioUrl"
          :transparent="true"
          class="digital-human-entity"
        />
        
        <!-- 状态指示器 (悬浮在人物上方) -->
        <div class="status-indicator" v-if="processing || isRecording">
          <div class="status-dot" :class="{ 'pulse': isRecording, 'thinking': processing }"></div>
          <span class="status-text">
            {{ isRecording ? '聆听中...' : (processing ? '思考中...' : '') }}
          </span>
        </div>
      </div>

      <!-- 识别文本展示 (动态浮现) -->
      <div class="transcription-area" v-if="recognizedText">
        <div class="transcription-bubble">
          {{ recognizedText }}
        </div>
      </div>

      <!-- 悬浮控制台 -->
      <div class="glass-control-bar">
        <!-- 核心控制区 -->
        <div class="control-core">
          <VoiceRecorder
            @recorded="handleVoiceRecorded"
            @recording-start="isRecording = true"
            @recording-end="isRecording = false"
            :disabled="processing"
            class="main-recorder-btn"
          />
          
          <!-- 播放器隐式集成 -->
          <VoicePlayer
            v-if="responseAudioUrl"
            :audio-url="responseAudioUrl"
            @playing="handlePlaying"
            @stopped="handleStopped"
            v-show="false" 
          />
        </div>

        <!-- 扩展设置开关 -->
        <div class="settings-toggle" @click="showSettings = !showSettings">
          <i class="el-icon-setting"></i> 
          <span class="toggle-text">{{ showSettings ? '收起设置' : '语音设置' }}</span>
        </div>

        <!-- 可折叠的参数面板 -->
        <transition name="slide-up">
          <div class="voice-params-panel" v-if="showSettings">
            <div class="param-row">
              <span class="param-label">语速</span>
              <el-slider
                v-model="voiceSpeed"
                :min="0.5"
                :max="2.0"
                :step="0.1"
                size="small"
                class="custom-slider"
              />
              <span class="param-value">{{ voiceSpeed.toFixed(1) }}x</span>
            </div>
            <div class="param-row">
              <span class="param-label">音调</span>
              <el-slider
                v-model="voicePitch"
                :min="0.5"
                :max="2.0"
                :step="0.1"
                size="small"
                class="custom-slider"
              />
              <span class="param-value">{{ voicePitch.toFixed(1) }}x</span>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
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

onMounted(async () => {
  await roleStore.loadBuiltinRoles()
  if (roleStore.builtinRoles.length > 0 && !roleStore.currentRole) {
    roleStore.selectRole(roleStore.builtinRoles[0])
  }
})

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
        undefined, 
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
</script>

<style scoped>
/* 字体引入 */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

.voice-chat-view {
  position: relative;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: #0f1115; /* 深空黑 */
  color: white;
  font-family: 'Inter', sans-serif;
}

/* --- 背景氛围 --- */
.ambient-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  overflow: hidden;
}

.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: float 10s infinite ease-in-out;
}

.orb-1 {
  top: -10%;
  left: -10%;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, #4a192c 0%, transparent 70%);
}

.orb-2 {
  bottom: -10%;
  right: -10%;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, #1c2e4a 0%, transparent 70%);
  animation-delay: -5s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(20px, 30px); }
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
  padding-bottom: 40px; /* 为底部控制栏留空 */
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
}

.digital-human-entity {
  max-height: 70vh;
  /* 可以添加一些入场动画 */
  transition: transform 0.5s ease;
}

.is-speaking .digital-human-entity {
  transform: scale(1.02); /* 说话时微微放大 */
}

/* 状态指示器 */
.status-indicator {
  position: absolute;
  top: 10%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #fff;
}

.status-dot.pulse {
  background: #ff4d4f;
  box-shadow: 0 0 0 0 rgba(255, 77, 79, 0.7);
  animation: pulse-red 1.5s infinite;
}

.status-dot.thinking {
  background: #409eff;
  animation: bounce 1s infinite;
}

.status-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 1px;
}

@keyframes pulse-red {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 77, 79, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(255, 77, 79, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 77, 79, 0); }
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

/* 识别文本气泡 */
.transcription-area {
  margin-bottom: 20px;
  width: 80%;
  max-width: 600px;
  text-align: center;
  min-height: 60px; /* 占位防止跳动 */
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.transcription-bubble {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  padding: 15px 25px;
  border-radius: 20px;
  font-size: 16px;
  line-height: 1.5;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  animation: fade-in-up 0.3s ease-out;
}

@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* --- 玻璃拟态控制台 --- */
.glass-control-bar {
  width: 90%;
  max-width: 500px;
  background: rgba(22, 22, 24, 0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.control-core {
  display: flex;
  justify-content: center;
  width: 100%;
}

/* 录音按钮容器样式微调 */
:deep(.voice-recorder-btn) {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff, #337ecc);
  border: none;
  box-shadow: 0 4px 15px rgba(64, 158, 255, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s, box-shadow 0.2s;
}

:deep(.voice-recorder-btn:hover) {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.5);
}

:deep(.voice-recorder-btn:active) {
  transform: scale(0.95);
}

.settings-toggle {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: color 0.2s;
}

.settings-toggle:hover {
  color: white;
}

/* 参数面板 */
.voice-params-panel {
  width: 100%;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  padding: 15px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.param-row {
  display: flex;
  align-items: center;
  gap: 15px;
}

.param-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  min-width: 30px;
}

.param-value {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.9);
  min-width: 30px;
  text-align: right;
}

.custom-slider {
  flex: 1;
  --el-slider-main-bg-color: #409eff;
  --el-slider-runway-bg-color: rgba(255, 255, 255, 0.2);
}

/* 动画效果 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
  max-height: 200px;
  opacity: 1;
}

.slide-up-enter-from,
.slide-up-leave-to {
  max-height: 0;
  opacity: 0;
  margin-top: 0;
  padding-top: 0;
  padding-bottom: 0;
}
</style>