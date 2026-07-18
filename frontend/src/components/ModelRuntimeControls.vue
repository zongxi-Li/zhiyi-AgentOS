<template>
  <div class="model-runtime-controls" :class="{ compact }" aria-label="模型运行设置">
    <el-select
      v-model="settings.selectedModel"
      class="model-select"
      :disabled="settings.provider === 'system'"
      aria-label="选择模型"
      @change="persistSettings"
    >
      <template #prefix><el-icon><Cpu /></el-icon></template>
      <el-option v-for="model in availableModels" :key="model" :label="model" :value="model" />
    </el-select>

    <el-select
      v-model="settings.reasoningEffort"
      class="reasoning-select"
      aria-label="选择思考程度"
      @change="persistSettings"
    >
      <template #prefix><el-icon><Opportunity /></el-icon></template>
      <el-option
        v-for="option in reasoningOptions"
        :key="option.value"
        :label="compact ? option.shortLabel : option.label"
        :value="option.value"
      />
    </el-select>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Cpu, Opportunity } from '@element-plus/icons-vue'
import {
  MODEL_SETTINGS_EVENT,
  loadModelSettings,
  reasoningOptions,
  saveModelSettings,
  type ModelSettings
} from '@/config/modelSettings'

withDefaults(defineProps<{ compact?: boolean }>(), { compact: false })

const settings = ref(loadModelSettings())
const availableModels = computed(() => settings.value.models.length ? settings.value.models : ['系统默认'])

function persistSettings(): void {
  saveModelSettings(settings.value)
}

function syncSettings(event: Event): void {
  const detail = (event as CustomEvent<ModelSettings>).detail
  settings.value = detail ? { ...detail, models: [...detail.models] } : loadModelSettings()
}

onMounted(() => window.addEventListener(MODEL_SETTINGS_EVENT, syncSettings))
onUnmounted(() => window.removeEventListener(MODEL_SETTINGS_EVENT, syncSettings))
</script>

<style scoped>
.model-runtime-controls {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.model-select {
  width: 164px;
}

.reasoning-select {
  width: 126px;
}

.model-runtime-controls.compact .model-select {
  width: 142px;
}

.model-runtime-controls.compact .reasoning-select {
  width: 82px;
}

.model-runtime-controls :deep(.el-select__wrapper) {
  min-height: 32px;
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 0 0 1px var(--border-light) inset;
}

.model-runtime-controls :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--border-hover) inset;
}

@media (max-width: 620px) {
  .model-runtime-controls,
  .model-runtime-controls.compact {
    width: 100%;
  }

  .model-runtime-controls .model-select,
  .model-runtime-controls.compact .model-select {
    width: auto;
    flex: 1 1 auto;
  }

  .model-runtime-controls .reasoning-select,
  .model-runtime-controls.compact .reasoning-select {
    width: 92px;
    flex: 0 0 92px;
  }
}
</style>
