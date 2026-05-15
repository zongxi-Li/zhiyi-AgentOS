<template>
  <section class="trace-event-timeline">
    <div class="section-head">
      <h3>Trace 事件</h3>
      <button type="button" :disabled="!events.length" @click="$emit('export-markdown')">Markdown</button>
    </div>

    <div v-if="loading" class="empty">正在加载 Trace...</div>
    <div v-else-if="!events.length" class="empty">暂无 Trace 事件</div>

    <div v-else class="events">
      <article v-for="event in events" :key="event.eventId" class="event-item">
        <div class="event-dot" :class="event.eventType"></div>
        <div class="event-content">
          <div class="event-top">
            <strong>{{ eventLabel(event.eventType) }}</strong>
            <time>{{ formatTime(event.createdAt) }}</time>
          </div>
          <p>{{ event.observation || '无观察记录' }}</p>
          <div class="event-meta">
            <span v-if="event.stepId">step={{ event.stepId }}</span>
            <span v-if="event.agentName">agent={{ event.agentName }}</span>
            <span v-if="event.durationMs">{{ event.durationMs }}ms</span>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { TraceEvent } from '@/services/api/workflow'

defineProps<{
  events: TraceEvent[]
  loading?: boolean
}>()

defineEmits<{
  'export-markdown': []
}>()

const eventLabel = (eventType: string) => {
  const labels: Record<string, string> = {
    task_created: '任务创建',
    run_started: '运行启动',
    step_started: '步骤开始',
    agent_called: 'Agent 调用',
    tool_called: '工具调用',
    checkpoint_created: '创建恢复点',
    review_required: '等待审核',
    review_decided: '审核决定',
    step_failed: '步骤失败',
    run_failed: '运行失败',
    run_recovered: '运行恢复',
    run_completed: '运行完成',
    run_cancelled: '运行取消'
  }
  return labels[eventType] || eventType
}

const formatTime = (value?: string) => {
  if (!value) return ''
  return new Date(value).toLocaleString()
}
</script>

<style scoped>
.trace-event-timeline {
  padding: 16px;
  border: 1px solid #dde4ef;
  border-radius: 8px;
  background: #fff;
}

.section-head,
.event-top,
.event-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-head {
  justify-content: space-between;
  margin-bottom: 12px;
}

h3,
p {
  margin: 0;
}

h3 {
  color: #0f172a;
  font-size: 15px;
}

button {
  height: 28px;
  padding: 0 10px;
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

.empty {
  color: #64748b;
  font-size: 12px;
}

.events {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 460px;
  overflow: auto;
}

.event-item {
  display: grid;
  grid-template-columns: 12px 1fr;
  gap: 10px;
}

.event-dot {
  width: 10px;
  height: 10px;
  margin-top: 6px;
  border-radius: 50%;
  background: #94a3b8;
}

.event-dot.agent_called,
.event-dot.run_completed {
  background: #22c55e;
}

.event-dot.review_required,
.event-dot.review_decided,
.event-dot.checkpoint_created {
  background: #f59e0b;
}

.event-dot.step_failed,
.event-dot.run_failed,
.event-dot.run_cancelled {
  background: #ef4444;
}

.event-content {
  min-width: 0;
  padding: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

.event-top {
  justify-content: space-between;
}

strong {
  color: #111827;
  font-size: 13px;
}

time,
p,
.event-meta {
  color: #64748b;
  font-size: 12px;
}

p {
  margin-top: 6px;
  overflow-wrap: anywhere;
  line-height: 1.45;
}

.event-meta {
  flex-wrap: wrap;
  margin-top: 8px;
}
</style>
