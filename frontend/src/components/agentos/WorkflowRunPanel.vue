<template>
  <section class="workflow-run-panel">
    <div class="panel-head">
      <div>
        <span class="eyebrow">WorkflowRun</span>
        <h2>{{ run?.workflowId || '暂无运行' }}</h2>
      </div>
      <div class="actions">
        <button type="button" @click="$emit('refresh')" :disabled="loading">刷新</button>
        <button type="button" @click="$emit('export-trace')" :disabled="!run || loading">导出 Trace</button>
      </div>
    </div>

    <div v-if="!run" class="empty">选择左侧运行记录后查看详情</div>

    <template v-else>
      <div class="status-row">
        <span class="status-pill" :class="run.status">{{ statusLabel(run.status) }}</span>
        <span>当前步骤：{{ run.currentStepId || '已结束' }}</span>
        <span>领域：{{ run.domain }}</span>
      </div>

      <div class="meta-grid">
        <div>
          <small>Run ID</small>
          <strong>{{ run.runId }}</strong>
        </div>
        <div>
          <small>Task ID</small>
          <strong>{{ run.taskId }}</strong>
        </div>
        <div>
          <small>审核模式</small>
          <strong>{{ run.reviewMode }}</strong>
        </div>
        <div>
          <small>恢复次数</small>
          <strong>{{ run.recoveryCount || 0 }}</strong>
        </div>
      </div>

      <div class="metric-strip">
        <div>
          <small>完成率</small>
          <strong>{{ percent(metrics?.metrics.completionRate) }}</strong>
        </div>
        <div>
          <small>失败率</small>
          <strong>{{ percent(metrics?.metrics.failureRate) }}</strong>
        </div>
        <div>
          <small>恢复成功率</small>
          <strong>{{ percent(metrics?.metrics.recoverySuccessRate) }}</strong>
        </div>
        <div>
          <small>审核记录</small>
          <strong>{{ metrics?.metrics.reviewCount ?? 0 }}</strong>
        </div>
      </div>

      <p v-if="run.error" class="error-line">{{ run.error }}</p>
    </template>
  </section>
</template>

<script setup lang="ts">
import type { EvaluationRun, WorkflowRun, WorkflowStatus } from '@/services/api/workflow'

defineProps<{
  run: WorkflowRun | null
  metrics: EvaluationRun | null
  loading?: boolean
}>()

defineEmits<{
  refresh: []
  'export-trace': []
}>()

const statusLabel = (status: WorkflowStatus) => {
  const labels: Record<WorkflowStatus, string> = {
    pending: '等待中',
    planning: '规划中',
    running: '运行中',
    waiting_review: '待审核',
    retrying: '重试中',
    failed: '失败',
    completed: '已完成',
    cancelled: '已取消'
  }
  return labels[status] || status
}

const percent = (value?: number) => `${Math.round((value || 0) * 100)}%`
</script>

<style scoped>
.workflow-run-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 18px;
  border: 1px solid #dde4ef;
  border-radius: 8px;
  background: #fff;
}

.panel-head,
.status-row,
.actions,
.metric-strip {
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-head {
  justify-content: space-between;
}

.eyebrow,
small {
  color: #64748b;
  font-size: 12px;
}

h2 {
  margin: 4px 0 0;
  font-size: 18px;
  color: #0f172a;
}

button {
  height: 32px;
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

.status-row {
  flex-wrap: wrap;
  color: #475569;
  font-size: 13px;
}

.status-pill {
  padding: 4px 8px;
  border-radius: 999px;
  background: #e2e8f0;
  color: #334155;
  font-size: 12px;
  font-weight: 700;
}

.status-pill.running,
.status-pill.retrying {
  background: #dbeafe;
  color: #1d4ed8;
}

.status-pill.waiting_review {
  background: #fef3c7;
  color: #b45309;
}

.status-pill.completed {
  background: #dcfce7;
  color: #15803d;
}

.status-pill.failed,
.status-pill.cancelled {
  background: #fee2e2;
  color: #b91c1c;
}

.meta-grid,
.metric-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.meta-grid > div,
.metric-strip > div {
  min-width: 0;
  padding: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

strong {
  display: block;
  margin-top: 4px;
  overflow-wrap: anywhere;
  color: #111827;
  font-size: 13px;
}

.metric-strip strong {
  font-size: 18px;
}

.empty,
.error-line {
  color: #64748b;
  font-size: 13px;
}

.error-line {
  padding: 10px;
  border: 1px solid #fecaca;
  border-radius: 8px;
  background: #fef2f2;
  color: #b91c1c;
}

@media (max-width: 900px) {
  .panel-head,
  .actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .meta-grid,
  .metric-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
