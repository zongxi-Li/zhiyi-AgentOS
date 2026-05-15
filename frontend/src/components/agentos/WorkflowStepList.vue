<template>
  <section class="workflow-step-list">
    <div class="section-head">
      <h3>步骤状态</h3>
      <span>{{ steps.length }} 个步骤</span>
    </div>

    <div v-if="!steps.length" class="empty">暂无步骤</div>

    <div v-else class="steps">
      <article
        v-for="step in steps"
        :key="step.stepId"
        class="step-card"
        :class="[step.status, { active: step.stepId === currentStepId }]"
      >
        <div class="step-top">
          <span>{{ step.stepId }}</span>
          <strong>{{ statusLabel(step.status) }}</strong>
        </div>
        <h4>{{ step.name }}</h4>
        <p>{{ step.agentName }}{{ step.capability ? ` · ${step.capability}` : '' }}</p>
        <div class="step-meta">
          <span v-if="step.reviewRequired">需要审核</span>
          <span v-if="step.retryCount">重试 {{ step.retryCount }} 次</span>
          <span v-if="step.durationMs">{{ step.durationMs }}ms</span>
        </div>
        <p v-if="step.error" class="step-error">{{ step.error }}</p>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { StepStatus, WorkflowStep } from '@/services/api/agentos'

defineProps<{
  steps: WorkflowStep[]
  currentStepId?: string
}>()

const statusLabel = (status: StepStatus) => {
  const labels: Record<StepStatus, string> = {
    pending: '等待',
    running: '运行',
    waiting_review: '待审',
    retrying: '重试',
    failed: '失败',
    completed: '完成',
    cancelled: '取消'
  }
  return labels[status] || status
}
</script>

<style scoped>
.workflow-step-list {
  padding: 16px;
  border: 1px solid #dde4ef;
  border-radius: 8px;
  background: #fff;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

h3,
h4,
p {
  margin: 0;
}

h3 {
  font-size: 15px;
  color: #0f172a;
}

.section-head span,
.empty,
p,
.step-meta {
  color: #64748b;
  font-size: 12px;
}

.steps {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 10px;
}

.step-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 138px;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

.step-card.active {
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.12);
}

.step-top,
.step-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.step-top span {
  overflow-wrap: anywhere;
  color: #334155;
  font-size: 12px;
  font-weight: 700;
}

.step-top strong {
  flex: 0 0 auto;
  padding: 3px 7px;
  border-radius: 999px;
  background: #e2e8f0;
  color: #334155;
  font-size: 11px;
}

.running .step-top strong,
.retrying .step-top strong {
  background: #dbeafe;
  color: #1d4ed8;
}

.waiting_review .step-top strong {
  background: #fef3c7;
  color: #b45309;
}

.completed .step-top strong {
  background: #dcfce7;
  color: #15803d;
}

.failed .step-top strong,
.cancelled .step-top strong {
  background: #fee2e2;
  color: #b91c1c;
}

h4 {
  color: #111827;
  font-size: 14px;
}

.step-meta {
  flex-wrap: wrap;
  justify-content: flex-start;
}

.step-error {
  padding: 8px;
  border-radius: 6px;
  background: #fef2f2;
  color: #b91c1c;
  overflow-wrap: anywhere;
}
</style>
