<template>
  <el-card class="voice-settings">
    <template #header>
      <span>语音设置</span>
    </template>
    
    <el-form label-width="100px">
      <el-form-item label="语音类型">
        <el-select v-model="voice" @change="handleChange">
          <el-option label="默认" value="default" />
          <el-option label="女声" value="female" />
          <el-option label="男声" value="male" />
          <el-option label="温柔" value="gentle" />
          <el-option label="活泼" value="lively" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="语速">
        <el-slider
          v-model="speed"
          :min="0.5"
          :max="2.0"
          :step="0.1"
          :format-tooltip="formatSpeed"
          @change="handleChange"
        />
        <span class="value-display">{{ speed.toFixed(1) }}x</span>
      </el-form-item>
      
      <el-form-item label="音调">
        <el-slider
          v-model="pitch"
          :min="0.5"
          :max="2.0"
          :step="0.1"
          :format-tooltip="formatPitch"
          @change="handleChange"
        />
        <span class="value-display">{{ pitch.toFixed(1) }}x</span>
      </el-form-item>
      
      <el-form-item>
        <el-button type="primary" @click="handleTest">试听</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { voiceApi } from '@/services/api/voice'

const emit = defineEmits<{
  change: [settings: { voice: string; speed: number; pitch: number }]
}>()

const voice = ref('default')
const speed = ref(1.0)
const pitch = ref(1.0)

const formatSpeed = (val: number) => `${val.toFixed(1)}x`
const formatPitch = (val: number) => `${val.toFixed(1)}x`

const handleChange = () => {
  emit('change', {
    voice: voice.value,
    speed: speed.value,
    pitch: pitch.value
  })
}

const handleTest = async () => {
  try {
    const testText = '这是语音测试，请听效果。'
    const audioBlob = await voiceApi.textToSpeech(testText, voice.value, speed.value, pitch.value)
    const audioUrl = URL.createObjectURL(audioBlob)
    const audio = new Audio(audioUrl)
    audio.play()
    
    audio.onended = () => {
      URL.revokeObjectURL(audioUrl)
    }
  } catch (error: any) {
    ElMessage.error('试听失败: ' + (error.message || '未知错误'))
  }
}

const handleReset = () => {
  voice.value = 'default'
  speed.value = 1.0
  pitch.value = 1.0
  handleChange()
  ElMessage.success('已重置为默认设置')
}
</script>

<style scoped>
.voice-settings {
  margin: 20px;
}

.value-display {
  margin-left: 10px;
  color: #409eff;
  font-weight: bold;
}
</style>

