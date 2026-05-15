<template>
  <main class="agentos-console">
    <header class="console-header">
      <div>
        <span>Zhiyi AgentOS</span>
        <h1>AgentOS Console</h1>
        <p>统一查看 WorkflowRun 生命周期、审核记录、恢复点和治理指标。</p>
      </div>
      <button type="button" @click="refreshAll" :disabled="loading.runs || loading.detail">刷新</button>
    </header>

    <section class="console-layout">
      <aside class="run-sidebar">
        <div class="filter-panel">
          <div class="filter-row">
            <label>
              <span>状态</span>
              <select v-model="filters.status" @change="loadRuns">
                <option value="">全部</option>
                <option v-for="item in statusOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
              </select>
            </label>
            <label>
              <span>来源</span>
              <input v-model="filters.source" placeholder="chat/workbench" @keyup.enter="loadRuns" />
            </label>
          </div>
          <label>
            <span>领域</span>
            <input v-model="filters.domain" placeholder="legal / education" @keyup.enter="loadRuns" />
          </label>
          <label>
            <span>Workflow ID</span>
            <input v-model="filters.workflowId" placeholder="legal_contract_review_v1" @keyup.enter="loadRuns" />
          </label>
        </div>

        <div class="run-list-head">
          <strong>运行列表</strong>
          <span>{{ totalRuns }} 条</span>
        </div>

        <div v-if="loading.runs" class="empty">正在加载...</div>
        <div v-else-if="!runs.length" class="empty">暂无 WorkflowRun</div>
        <template v-else>
          <button
            v-for="run in runs"
            :key="run.runId"
            type="button"
            class="run-item"
            :class="{ active: run.runId === selectedRunId }"
            @click="selectRun(run.runId)"
          >
            <span class="run-status" :class="run.status">{{ run.status }}</span>
            <strong>{{ run.workflowId }}</strong>
            <small>{{ run.runId }}</small>
          </button>
        </template>
      </aside>

      <section class="console-main">
        <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>

        <WorkflowRunPanel
          :run="selectedRun"
          :metrics="metrics"
          :loading="loading.detail"
          @refresh="refreshSelectedRun"
          @export-trace="exportTrace"
        />

        <WorkflowStepList
          :steps="selectedRun?.steps || []"
          :current-step-id="selectedRun?.currentStepId"
        />

        <CheckpointPanel
          :checkpoints="checkpoints"
          :loading="loading.checkpoints"
          @resume="resumeFromCheckpoint"
        />
      </section>

      <aside class="console-side">
        <HumanReviewPanel
          :run="selectedRun"
          :reviews="reviews"
          :loading="loading.reviews"
          :submitting="loading.reviewSubmit"
          @submit="submitReview"
        />

        <TraceEventTimeline
          :events="traceEvents"
          :loading="loading.trace"
          @export-markdown="exportTrace"
        />
      </aside>
    </section>
  </main>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import CheckpointPanel from '@/components/agentos/CheckpointPanel.vue'
import HumanReviewPanel from '@/components/agentos/HumanReviewPanel.vue'
import TraceEventTimeline from '@/components/agentos/TraceEventTimeline.vue'
import WorkflowRunPanel from '@/components/agentos/WorkflowRunPanel.vue'
import WorkflowStepList from '@/components/agentos/WorkflowStepList.vue'
import { workflowApi, type Checkpoint, type EvaluationRun, type ReviewRecord, type ReviewRequest, type TraceEvent, type WorkflowRun, type WorkflowRunQuery } from '@/services/api/workflow'

const runs = ref<WorkflowRun[]>([])
const totalRuns = ref(0)
const selectedRunId = ref('')
const selectedRun = ref<WorkflowRun | null>(null)
const traceEvents = ref<TraceEvent[]>([])
const checkpoints = ref<Checkpoint[]>([])
const reviews = ref<ReviewRecord[]>([])
const metrics = ref<EvaluationRun | null>(null)
const errorMessage = ref('')

const filters = reactive<WorkflowRunQuery>({
  status: '',
  domain: '',
  workflowId: '',
  source: '',
  page: 1,
  pageSize: 20
})

const loading = reactive({
  runs: false,
  detail: false,
  trace: false,
  checkpoints: false,
  reviews: false,
  reviewSubmit: false
})

const statusOptions = [
  { value: 'pending', label: '等待中' },
  { value: 'running', label: '运行中' },
  { value: 'waiting_review', label: '待审核' },
  { value: 'retrying', label: '重试中' },
  { value: 'failed', label: '失败' },
  { value: 'completed', label: '已完成' },
  { value: 'cancelled', label: '已取消' }
]

const cleanQuery = (query: WorkflowRunQuery) => {
  return Object.fromEntries(
    Object.entries(query).filter(([, value]) => value !== undefined && value !== null && value !== '')
  ) as WorkflowRunQuery
}

const loadRuns = async () => {
  loading.runs = true
  errorMessage.value = ''
  try {
    const page = await workflowApi.listRuns(cleanQuery(filters))
    runs.value = page.items || []
    totalRuns.value = page.total || 0
    if (!selectedRunId.value && runs.value[0]) {
      await selectRun(runs.value[0].runId)
    }
  } catch (error: any) {
    errorMessage.value = error?.message || '加载运行列表失败'
  } finally {
    loading.runs = false
  }
}

const selectRun = async (runId: string) => {
  selectedRunId.value = runId
  await refreshSelectedRun()
}

const refreshSelectedRun = async () => {
  if (!selectedRunId.value) return
  loading.detail = true
  errorMessage.value = ''
  try {
    const run = await workflowApi.getRun(selectedRunId.value)
    selectedRun.value = run
    traceEvents.value = run.trace || []
    checkpoints.value = run.checkpoints || []
    await Promise.all([
      loadTrace(run.runId),
      loadCheckpoints(run.runId),
      loadReviews(run.runId),
      loadMetrics(run)
    ])
  } catch (error: any) {
    errorMessage.value = error?.message || '加载运行详情失败'
  } finally {
    loading.detail = false
  }
}

const loadTrace = async (runId: string) => {
  loading.trace = true
  try {
    const payload = await workflowApi.getTrace(runId)
    traceEvents.value = payload.events || []
  } finally {
    loading.trace = false
  }
}

const loadCheckpoints = async (runId: string) => {
  loading.checkpoints = true
  try {
    const payload = await workflowApi.listCheckpoints(runId)
    checkpoints.value = payload.items || []
  } finally {
    loading.checkpoints = false
  }
}

const loadReviews = async (runId: string) => {
  loading.reviews = true
  try {
    const payload = await workflowApi.listReviews(runId)
    reviews.value = payload.items || []
  } finally {
    loading.reviews = false
  }
}

const loadMetrics = async (run: WorkflowRun) => {
  metrics.value = await workflowApi.getMetrics({ workflowId: run.workflowId })
}

const submitReview = async (payload: ReviewRequest) => {
  if (!selectedRun.value) return
  loading.reviewSubmit = true
  errorMessage.value = ''
  try {
    const reviewed = await workflowApi.submitReview(selectedRun.value.runId, payload)
    selectedRun.value = reviewed
    selectedRunId.value = reviewed.runId
    await refreshSelectedRun()
    await loadRuns()
  } catch (error: any) {
    errorMessage.value = error?.message || '提交审核失败'
  } finally {
    loading.reviewSubmit = false
  }
}

const resumeFromCheckpoint = async (checkpointId: string) => {
  if (!selectedRun.value) return
  loading.detail = true
  errorMessage.value = ''
  try {
    const resumed = await workflowApi.resumeFromCheckpoint(selectedRun.value.runId, checkpointId)
    selectedRun.value = resumed
    selectedRunId.value = resumed.runId
    await refreshSelectedRun()
    await loadRuns()
  } catch (error: any) {
    errorMessage.value = error?.message || '恢复失败'
  } finally {
    loading.detail = false
  }
}

const exportTrace = async () => {
  if (!selectedRun.value) return
  const markdown = await workflowApi.exportTraceMarkdown(selectedRun.value.runId)
  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `agentos-trace-${selectedRun.value.runId}.md`
  link.click()
  URL.revokeObjectURL(url)
}

const refreshAll = async () => {
  await loadRuns()
  await refreshSelectedRun()
}

onMounted(loadRuns)
</script>

<style scoped>
.agentos-console {
  min-height: 100vh;
  padding: 20px;
  background: #f1f5f9;
  color: #0f172a;
}

.console-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.console-header span {
  color: #2563eb;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0;
}

h1,
p {
  margin: 0;
}

h1 {
  margin-top: 4px;
  font-size: 24px;
}

.console-header p {
  margin-top: 6px;
  color: #64748b;
  font-size: 13px;
}

.console-header button {
  height: 34px;
  padding: 0 14px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #fff;
  color: #0f172a;
  cursor: pointer;
}

.console-layout {
  display: grid;
  grid-template-columns: minmax(240px, 300px) minmax(0, 1fr) minmax(300px, 380px);
  gap: 14px;
  align-items: start;
}

.run-sidebar,
.console-main,
.console-side {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.filter-panel,
.run-list-head,
.run-item,
.error-message {
  border: 1px solid #dde4ef;
  border-radius: 8px;
  background: #fff;
}

.filter-panel {
  display: grid;
  gap: 10px;
  padding: 14px;
}

.filter-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

label {
  display: grid;
  gap: 5px;
}

label span {
  color: #334155;
  font-size: 12px;
  font-weight: 700;
}

select,
input {
  width: 100%;
  height: 32px;
  padding: 0 8px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #fff;
  color: #0f172a;
  font-size: 12px;
}

.run-list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
}

.run-list-head strong {
  font-size: 14px;
}

.run-list-head span,
.empty {
  color: #64748b;
  font-size: 12px;
}

.empty {
  padding: 12px;
}

.run-item {
  display: grid;
  gap: 6px;
  width: 100%;
  padding: 12px;
  text-align: left;
  cursor: pointer;
}

.run-item.active {
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.12);
}

.run-status {
  width: fit-content;
  padding: 3px 7px;
  border-radius: 999px;
  background: #e2e8f0;
  color: #334155;
  font-size: 11px;
  font-weight: 800;
}

.run-status.running,
.run-status.retrying {
  background: #dbeafe;
  color: #1d4ed8;
}

.run-status.waiting_review {
  background: #fef3c7;
  color: #b45309;
}

.run-status.completed {
  background: #dcfce7;
  color: #15803d;
}

.run-status.failed,
.run-status.cancelled {
  background: #fee2e2;
  color: #b91c1c;
}

.run-item strong,
.run-item small {
  overflow-wrap: anywhere;
}

.run-item strong {
  color: #111827;
  font-size: 13px;
}

.run-item small {
  color: #64748b;
  font-size: 11px;
}

.error-message {
  padding: 10px;
  color: #b91c1c;
  background: #fef2f2;
  border-color: #fecaca;
  font-size: 13px;
}

@media (max-width: 1180px) {
  .console-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .agentos-console {
    padding: 14px;
  }

  .console-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .filter-row {
    grid-template-columns: 1fr;
  }
}
</style>
