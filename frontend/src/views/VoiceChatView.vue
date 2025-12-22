<template>
  <div class="voice-chat-view">
    <el-container>
      <!-- 数字人展示区 -->
      <el-main class="digital-human-area">
        <DigitalHuman
          :role-id="roleStore.currentRole?.id"
          :is-speaking="isSpeaking"
          :audio-url="currentAudioUrl"
        />
      </el-main>

      <!-- 控制区 -->
      <el-footer class="voice-controls">
        <div class="control-panel">
          <VoiceRecorder
            @recorded="handleVoiceRecorded"
            :disabled="processing"
          />
          <div class="control-info">
            <el-text v-if="recognizedText" type="info">
              识别: {{ recognizedText }}
            </el-text>
            <el-text v-if="processing" type="warning">
              处理中...
            </el-text>
          </div>
          
          <!-- 语音参数调节 -->
          <div class="voice-params">
            <div class="param-item">
              <el-text size="small">语速:</el-text>
              <el-slider
                v-model="voiceSpeed"
                :min="0.5"
                :max="2.0"
                :step="0.1"
                :show-tooltip="true"
                :format-tooltip="(val: number) => val.toFixed(1) + 'x'"
                style="width: 150px; margin: 0 10px;"
              />
              <el-text size="small" type="info">{{ voiceSpeed.toFixed(1) }}x</el-text>
            </div>
            <div class="param-item">
              <el-text size="small">音调:</el-text>
              <el-slider
                v-model="voicePitch"
                :min="0.5"
                :max="2.0"
                :step="0.1"
                :show-tooltip="true"
                :format-tooltip="(val: number) => val.toFixed(1) + 'x'"
                style="width: 150px; margin: 0 10px;"
              />
              <el-text size="small" type="info">{{ voicePitch.toFixed(1) }}x</el-text>
            </div>
          </div>
          
          <VoicePlayer
            v-if="responseAudioUrl"
            :audio-url="responseAudioUrl"
            @playing="handlePlaying"
            @stopped="handleStopped"
          />
        </div>
      </el-footer>
    </el-container>
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
const processing = ref(false)
const recognizedText = ref('')
const currentAudioUrl = ref<string>('')
const responseAudioUrl = ref<string>('')
const voiceSpeed = ref(1.0) // 语速：0.5-2.0
const voicePitch = ref(1.0) // 音调：0.5-2.0

// 加载角色列表
onMounted(async () => {
  await roleStore.loadBuiltinRoles()
  if (roleStore.builtinRoles.length > 0 && !roleStore.currentRole) {
    roleStore.selectRole(roleStore.builtinRoles[0])
  }
})

const handleVoiceRecorded = async (audioBlob: Blob) => {
  processing.value = true
  recognizedText.value = ''

  try {
    // 创建File对象
    const audioFile = new File([audioBlob], 'recording.wav', { type: 'audio/wav' })
    
    // 发送语音消息
    const response = await voiceApi.sendVoiceMessage({
      audio: audioFile,
      roleId: roleStore.currentRole?.id
    })

    recognizedText.value = response.recognizedText || response.text

    // 获取回复的文本转语音（使用当前设置的语速和音调）
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
.voice-chat-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.digital-human-area {
  flex: 1;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.voice-controls {
  background: white;
  border-top: 1px solid #e4e7ed;
  padding: 20px;
}

.control-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  max-width: 600px;
  margin: 0 auto;
}

.control-info {
  min-height: 30px;
  text-align: center;
}

.voice-params {
  display: flex;
  flex-direction: column;
  gap: 15px;
  width: 100%;
  max-width: 400px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.param-item {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>

