<template>
  <div class="voice-recorder">
    <el-button
      :type="isRecording ? 'danger' : 'primary'"
      :icon="Microphone"
      circle
      size="large"
      @mousedown="startRecording"
      @mouseup="stopRecording"
      @mouseleave="stopRecording"
      :loading="processing"
    >
    </el-button>
    <div v-if="isRecording" class="recording-indicator">
      <span class="pulse"></span>
      <span>正在录音...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Microphone } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface Emits {
  (e: 'recorded', audioBlob: Blob): void
}

const emit = defineEmits<Emits>()

const isRecording = ref(false)
const processing = ref(false)
let mediaRecorder: MediaRecorder | null = null
let audioChunks: Blob[] = []

const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new MediaRecorder(stream)
    audioChunks = []

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data)
      }
    }

    mediaRecorder.onstop = () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/wav' })
      emit('recorded', audioBlob)
      stream.getTracks().forEach(track => track.stop())
    }

    mediaRecorder.start()
    isRecording.value = true
  } catch (error) {
    ElMessage.error('无法访问麦克风')
    console.error('录音失败:', error)
  }
}

const stopRecording = () => {
  if (mediaRecorder && isRecording.value) {
    mediaRecorder.stop()
    isRecording.value = false
  }
}
</script>

<style scoped>
.voice-recorder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #f56c6c;
  font-size: 14px;
}

.pulse {
  width: 10px;
  height: 10px;
  background: #f56c6c;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
</style>

