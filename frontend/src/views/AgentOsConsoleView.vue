<template>
  <main class="agentos-console ui-shell">
    <header class="console-header ui-hero">
      <div class="console-title">
        <span class="ui-icon-badge">
          <el-icon><Monitor /></el-icon>
        </span>
        <div>
          <span class="ui-hero__eyebrow">Zhiyi AgentOS</span>
          <h1 class="ui-hero__title">AgentOS Console</h1>
          <p class="ui-hero__subtitle">统一查看 WorkflowRun 生命周期、审核记录、恢复点和治理指标。</p>
        </div>
      </div>
      <button class="console-refresh" type="button" @click="refreshAll" :disabled="loading.runs || loading.detail">
        <el-icon><Refresh /></el-icon>
        <span>刷新</span>
      </button>
    </header>

    <section class="console-layout">
      <aside class="run-sidebar ui-surface ui-surface--pad">
        <div class="filter-panel">
          <div class="filter-title">
            <el-icon><Search /></el-icon>
            <span>筛选运行</span>
          </div>
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
          <span class="ui-chip">{{ totalRuns }} 条</span>
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
import { Monitor, Refresh, Search } from '@element-plus/icons-vue'
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
  { value: 'planning', label: '规划中' },
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
  height: 100%;
  color: var(--text-primary);
  overflow: auto;
}

.console-header {
  flex-shrink: 0;
}

.console-title {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

h1,
p {
  margin: 0;
}

.console-refresh {
  height: 36px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 14px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  background: #fff;
  color: var(--text-primary);
  cursor: pointer;
  transition: var(--transition);
}

.console-refresh:hover:not(:disabled) {
  border-color: var(--border-hover);
  color: var(--primary-color);
  transform: translateY(-1px);
}

.console-refresh:disabled {
  cursor: not-allowed;
  opacity: 0.56;
}

.console-layout {
  display: grid;
  grid-template-columns: minmax(250px, 300px) minmax(0, 1fr) minmax(310px, 380px);
  gap: 16px;
  align-items: stretch;
}

.run-sidebar,
.console-main,
.console-side {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.run-sidebar {
  position: sticky;
  top: 16px;
}

.filter-panel {
  display: grid;
  gap: 12px;
}

.filter-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 650;
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
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 700;
}

select,
input {
  width: 100%;
  height: 34px;
  padding: 0 10px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: var(--bg-input);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
  transition: var(--transition);
}

select:focus,
input:focus {
  background: #fff;
  border-color: var(--primary-line);
  box-shadow: 0 0 0 3px var(--primary-fade);
}

.run-list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0 4px;
  border-top: 1px solid var(--border-light);
}

.run-list-head strong {
  font-size: 14px;
}

.run-list-head span,
.empty {
  color: var(--text-secondary);
  font-size: 12px;
}

.empty {
  padding: 12px 0;
}

.run-item {
  display: grid;
  gap: 6px;
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.72);
  text-align: left;
  cursor: pointer;
  transition: var(--transition);
}

.run-item.active {
  border-color: var(--primary-line);
  background: #fff;
  box-shadow: inset 2px 0 0 var(--primary-color), var(--shadow-sm);
}

.run-item:hover {
  border-color: var(--border-hover);
  transform: translateY(-1px);
}

.run-status {
  width: fit-content;
  padding: 3px 7px;
  border-radius: 999px;
  background: var(--bg-input);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 800;
}

.run-status.running,
.run-status.retrying {
  background: rgba(73, 107, 143, 0.12);
  color: var(--info);
}

.run-status.waiting_review {
  background: rgba(154, 116, 50, 0.12);
  color: var(--warning);
}

.run-status.completed {
  background: rgba(61, 118, 86, 0.12);
  color: var(--success);
}

.run-status.failed,
.run-status.cancelled {
  background: rgba(178, 74, 74, 0.12);
  color: var(--danger);
}

.run-item strong,
.run-item small {
  overflow-wrap: anywhere;
}

.run-item strong {
  color: var(--text-primary);
  font-size: 13px;
}

.run-item small {
  color: var(--text-secondary);
  font-size: 11px;
}

.error-message {
  padding: 10px;
  border: 1px solid rgba(178, 74, 74, 0.18);
  border-radius: 8px;
  color: var(--danger);
  background: rgba(178, 74, 74, 0.08);
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
