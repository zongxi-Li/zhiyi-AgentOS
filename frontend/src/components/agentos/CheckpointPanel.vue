<template>
  <section class="checkpoint-panel">
    <div class="section-head">
      <h3>恢复点</h3>
      <span>{{ checkpoints.length }} 个</span>
    </div>

    <div v-if="loading" class="empty">正在加载恢复点...</div>
    <div v-else-if="!checkpoints.length" class="empty">暂无可用恢复点</div>

    <div v-else class="checkpoint-list">
      <article v-for="checkpoint in checkpoints" :key="checkpoint.checkpointId" class="checkpoint-item">
        <div>
          <strong>{{ checkpoint.stepId }}</strong>
          <span>{{ checkpoint.checkpointId }}</span>
          <time>{{ formatTime(checkpoint.createdAt) }}</time>
        </div>
        <button
          type="button"
          :disabled="!checkpoint.canResume"
          @click="$emit('resume', checkpoint.checkpointId)"
        >
          恢复
        </button>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { Checkpoint } from '@/services/api/workflow'

defineProps<{
  checkpoints: Checkpoint[]
  loading?: boolean
}>()

defineEmits<{
  resume: [checkpointId: string]
}>()

const formatTime = (value?: string) => {
  if (!value) return '时间未知'
  return new Date(value).toLocaleString()
}
</script>

<style scoped>
.checkpoint-panel {
  padding: 16px;
  border: 1px solid #dde4ef;
  border-radius: 8px;
  background: #fff;
}

.section-head,
.checkpoint-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.section-head {
  margin-bottom: 12px;
}

h3 {
  margin: 0;
  color: #0f172a;
  font-size: 15px;
}

.section-head span,
.empty {
  color: #64748b;
  font-size: 12px;
}

.checkpoint-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.checkpoint-item {
  padding: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

.checkpoint-item > div {
  min-width: 0;
}

strong,
span,
time {
  display: block;
}

strong {
  color: #111827;
  font-size: 13px;
}

span,
time {
  margin-top: 3px;
  overflow-wrap: anywhere;
  color: #64748b;
  font-size: 12px;
}

button {
  flex: 0 0 auto;
  height: 30px;
  padding: 0 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #fff;
  color: #0f172a;
  cursor: pointer;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}
</style>
