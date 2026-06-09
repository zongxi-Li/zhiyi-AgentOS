<template>
  <main class="contract-review-workbench ui-shell">
    <header class="workbench-header ui-hero">
      <div class="workbench-title">
        <span class="ui-icon-badge">
          <el-icon><DocumentChecked /></el-icon>
        </span>
        <div>
          <span class="ui-hero__eyebrow">Zhiyi AgentOS Legal</span>
          <h1 class="ui-hero__title">{{ modeConfig.title }}</h1>
          <p class="ui-hero__subtitle">{{ modeConfig.subtitle }}</p>
        </div>
      </div>
      <div class="header-controls">
        <div class="mode-switch" aria-label="法律任务模式">
          <button
            type="button"
            :class="{ active: workbenchMode === 'review' }"
            :disabled="loading.start"
            @click="switchWorkbenchMode('review')"
          >
            合同审查
          </button>
          <button
            type="button"
            :class="{ active: workbenchMode === 'draft' }"
            :disabled="loading.start"
            @click="switchWorkbenchMode('draft')"
          >
            合同起草
          </button>
        </div>
        <button class="header-action" type="button" :disabled="!selectedRun || loading.detail" @click="refreshSelectedRun">
          <el-icon><Refresh /></el-icon>
          <span>刷新</span>
        </button>
      </div>
    </header>

    <section class="workbench-layout" :class="{ 'is-pre-review': !selectedRun }">
      <section class="workbench-main">
        <section class="contract-input-panel ui-surface ui-surface--pad">
          <div class="section-head">
            <div class="section-title">
              <el-icon><DocumentChecked /></el-icon>
              <h3>{{ modeConfig.inputTitle }}</h3>
            </div>
            <span>{{ selectedWorkflowId }}</span>
          </div>
          <label class="workflow-select">
            <span>Workflow</span>
            <select v-model="selectedWorkflowId" :disabled="loading.start">
              <option v-for="item in workflowOptions" :key="item.value" :value="item.value">
                {{ item.label }}
              </option>
            </select>
          </label>
          <textarea
            v-model="contractText"
            :disabled="loading.start"
            :placeholder="modeConfig.placeholder"
            rows="9"
          />
          <div class="input-actions">
            <button type="button" class="primary-action" :disabled="loading.start || !contractText.trim()" @click="startLegalWorkflow">
              <el-icon><Check /></el-icon>
              <span>{{ loading.start ? '启动中...' : modeConfig.actionLabel }}</span>
            </button>
            <span v-if="selectedRun">当前运行：{{ selectedRun.runId }}</span>
          </div>
        </section>

        <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>

        <template v-if="selectedRun">
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

          <ContractRiskPanel :risks="contractArtifacts.risks" />
          <ContractEvidencePanel :evidences="contractArtifacts.evidences" />
          <ContractReportPreview :report-markdown="contractArtifacts.reportMarkdown" />
        </template>

        <template v-else>
          <section class="preflight-flow-panel ui-surface ui-surface--pad">
            <div class="section-head">
              <div class="section-title">
              <el-icon><DocumentChecked /></el-icon>
                <h3>{{ modeConfig.flowTitle }}</h3>
              </div>
              <span>待启动</span>
            </div>
            <div class="preflight-steps">
              <article v-for="step in preflightSteps" :key="step.id" class="preflight-step">
                <strong>{{ step.title }}</strong>
                <p>{{ step.agent }}</p>
                <span>{{ step.status }}</span>
              </article>
            </div>
          </section>

          <section class="preflight-output-panel ui-surface ui-surface--pad">
            <div class="section-head">
              <div class="section-title">
              <el-icon><DocumentChecked /></el-icon>
                <h3>{{ modeConfig.outputTitle }}</h3>
              </div>
              <span>等待生成</span>
            </div>
            <div class="preflight-output-grid">
              <article v-for="item in preflightOutputs" :key="item.id" class="preflight-output-item">
                <strong>{{ item.title }}</strong>
                <p>{{ item.path }}</p>
              </article>
            </div>
          </section>
        </template>
      </section>

      <aside class="workbench-side">
        <section class="artifact-path-panel ui-surface ui-surface--pad">
          <div class="section-head">
            <div class="section-title">
              <el-icon><DocumentChecked /></el-icon>
              <h3>Artifact 路径</h3>
            </div>
          </div>
          <dl>
            <div>
              <dt>risks</dt>
              <dd>{{ contractArtifacts.paths.risks }}</dd>
            </div>
            <div>
              <dt>evidences</dt>
              <dd>{{ contractArtifacts.paths.evidences }}</dd>
            </div>
            <div>
              <dt>report</dt>
              <dd>{{ contractArtifacts.paths.reportMarkdown }}</dd>
            </div>
          </dl>
        </section>

        <template v-if="selectedRun">
          <HumanReviewPanel
            :run="selectedRun"
            :reviews="reviews"
            :loading="loading.reviews"
            :submitting="loading.reviewSubmit"
            @submit="submitReview"
          />

          <CheckpointPanel
            :checkpoints="checkpoints"
            :loading="loading.checkpoints"
            @resume="resumeFromCheckpoint"
          />

          <TraceEventTimeline
            :events="traceEvents"
            :loading="loading.trace"
            @export-markdown="exportTrace"
          />

          <CallResultPanel
            :run="selectedRun"
            :events="traceEvents"
            :loading="loading.detail || loading.trace"
          />
        </template>

        <template v-else>
          <section class="preflight-config-panel ui-surface ui-surface--pad">
            <div class="section-head">
              <div class="section-title">
              <el-icon><DocumentChecked /></el-icon>
                <h3>{{ modeConfig.configTitle }}</h3>
              </div>
              <span>human_in_loop</span>
            </div>
            <dl>
              <div>
                <dt>workflow</dt>
                <dd>{{ selectedWorkflowId }}</dd>
              </div>
              <div>
                <dt>domain</dt>
                <dd>legal</dd>
              </div>
              <div>
                <dt>intent</dt>
                <dd>{{ modeConfig.intent }}</dd>
              </div>
            </dl>
          </section>

          <section class="preflight-monitor-panel ui-surface ui-surface--pad">
            <div class="section-head">
              <div class="section-title">
                <el-icon><Refresh /></el-icon>
                <h3>运行监控</h3>
              </div>
              <span>standby</span>
            </div>
            <div class="monitor-slots">
              <article v-for="item in preflightMonitors" :key="item.id">
                <strong>{{ item.title }}</strong>
                <p>{{ item.value }}</p>
              </article>
            </div>
          </section>
        </template>
      </aside>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Check, DocumentChecked, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import CallResultPanel from '@/components/agentos/CallResultPanel.vue'
import CheckpointPanel from '@/components/agentos/CheckpointPanel.vue'
import ContractEvidencePanel from '@/components/agentos/ContractEvidencePanel.vue'
import ContractReportPreview from '@/components/agentos/ContractReportPreview.vue'
import ContractRiskPanel from '@/components/agentos/ContractRiskPanel.vue'
import HumanReviewPanel from '@/components/agentos/HumanReviewPanel.vue'
import TraceEventTimeline from '@/components/agentos/TraceEventTimeline.vue'
import WorkflowRunPanel from '@/components/agentos/WorkflowRunPanel.vue'
import WorkflowStepList from '@/components/agentos/WorkflowStepList.vue'
import { workflowApi, type Checkpoint, type EvaluationRun, type ReviewRecord, type ReviewRequest, type TraceEvent, type WorkflowRun } from '@/services/api/workflow'
import { extractContractReviewArtifacts } from '@/utils/agentos/contractReviewArtifactExtractor'

type WorkbenchMode = 'review' | 'draft'

const route = useRoute()
const router = useRouter()

const resolveRouteMode = (): WorkbenchMode => route.query.mode === 'draft' ? 'draft' : 'review'

const legalModes: Record<WorkbenchMode, {
  title: string
  subtitle: string
  inputTitle: string
  placeholder: string
  actionLabel: string
  flowTitle: string
  outputTitle: string
  configTitle: string
  successMessage: string
  intent: string
  workflowLabel: string
  defaultText: string
  steps: Array<{ id: string; title: string; agent: string; status: string }>
  outputs: Array<{ id: string; title: string; path: string }>
  monitors: Array<{ id: string; title: string; value: string }>
}> = {
  review: {
    title: '律师合同审查',
    subtitle: '基于 WorkflowRun、Trace、Artifacts 与 Human Review 的合同审查工作台。',
    inputTitle: '合同文本',
    placeholder: '粘贴待审查合同文本',
    actionLabel: '启动审查 Workflow',
    flowTitle: '审查流程',
    outputTitle: '结果区域',
    configTitle: '审查配置',
    successMessage: 'Workflow 已执行到 human_review:waiting_review',
    intent: 'contract_review',
    workflowLabel: '合同审查标准流程',
    defaultText: `甲方委托乙方开发 CRM 系统，合同约定签署后支付 30%，系统上线后支付 70%。
如无重大问题视为验收通过，项目源代码归双方共同所有。`,
    steps: [
      { id: 'risk', title: '风险识别', agent: 'legal_risk_detect', status: '待执行' },
      { id: 'evidence', title: '依据匹配', agent: 'legal_evidence_match', status: '待执行' },
      { id: 'review', title: '人工审核', agent: 'human_review', status: '审核门控' },
      { id: 'report', title: '报告生成', agent: 'report_generate', status: '待执行' }
    ],
    outputs: [
      { id: 'risks', title: '风险点', path: 'output.artifacts.risk_detect.risks' },
      { id: 'evidences', title: 'Evidence 依据链', path: 'output.artifacts.legal_evidence_match.evidences' },
      { id: 'report', title: '报告预览', path: 'output.artifacts.report_generate.report_markdown' }
    ],
    monitors: [
      { id: 'trace', title: 'Trace 事件', value: '0 条' },
      { id: 'checkpoint', title: '恢复点', value: '0 个' },
      { id: 'call-result', title: '调用结果', value: '0 条' }
    ]
  },
  draft: {
    title: '合同起草规划',
    subtitle: '在 AgentOS Legal 中完成需求理解、条款骨架、风险校验与正式草案输出。',
    inputTitle: '起草需求',
    placeholder: '描述合同类型、交易背景、交付物、付款节点和重点约束',
    actionLabel: '启动起草 Workflow',
    flowTitle: '起草流程',
    outputTitle: '草案输出',
    configTitle: '起草配置',
    successMessage: '合同起草 Workflow 已进入人工确认节点',
    intent: 'contract_drafting',
    workflowLabel: '合同起草规划流程',
    defaultText: `为软件开发项目起草正式合同。甲方需要 CRM 系统，乙方负责需求确认、开发、测试、部署和交付。
请重点规划验收标准、付款节点、知识产权归属、源代码交付、保密义务和违约责任。`,
    steps: [
      { id: 'requirements', title: '需求理解', agent: 'legal_requirement_parser', status: '待执行' },
      { id: 'clause-plan', title: '条款骨架', agent: 'contract_clause_planner', status: '待执行' },
      { id: 'risk-guard', title: '风险校验', agent: 'legal_risk_detect', status: '待执行' },
      { id: 'draft', title: '草案生成', agent: 'contract_draft_generate', status: '待执行' }
    ],
    outputs: [
      { id: 'outline', title: '条款骨架', path: 'output.artifacts.clause_plan.outline' },
      { id: 'risks', title: '起草风险', path: 'output.artifacts.risk_detect.risks' },
      { id: 'draft', title: '正式草案', path: 'output.artifacts.contract_draft.markdown' }
    ],
    monitors: [
      { id: 'trace', title: 'Trace 事件', value: '0 条' },
      { id: 'draft-version', title: '草案版本', value: 'v0.1' },
      { id: 'review-gate', title: '确认节点', value: '待启动' }
    ]
  }
}

const workbenchMode = ref<WorkbenchMode>(resolveRouteMode())
const modeConfig = computed(() => legalModes[workbenchMode.value])

const workflowOptions = computed(() => [
  { label: modeConfig.value.workflowLabel, value: 'legal_contract_review_v1' }
])

const preflightSteps = computed(() => modeConfig.value.steps)
const preflightOutputs = computed(() => modeConfig.value.outputs)
const preflightMonitors = computed(() => modeConfig.value.monitors)

const contractText = ref(modeConfig.value.defaultText)
const selectedWorkflowId = ref(workflowOptions.value[0].value)
const selectedRun = ref<WorkflowRun | null>(null)
const traceEvents = ref<TraceEvent[]>([])
const checkpoints = ref<Checkpoint[]>([])
const reviews = ref<ReviewRecord[]>([])
const metrics = ref<EvaluationRun | null>(null)
const errorMessage = ref('')

const loading = reactive({
  start: false,
  detail: false,
  trace: false,
  checkpoints: false,
  reviews: false,
  reviewSubmit: false
})

const contractArtifacts = computed(() => extractContractReviewArtifacts(selectedRun.value))

const resetRunState = () => {
  selectedRun.value = null
  traceEvents.value = []
  checkpoints.value = []
  reviews.value = []
  metrics.value = null
  errorMessage.value = ''
}

const applyModeDefaults = (mode: WorkbenchMode) => {
  workbenchMode.value = mode
  selectedWorkflowId.value = workflowOptions.value[0].value
  contractText.value = legalModes[mode].defaultText
  resetRunState()
}

const switchWorkbenchMode = (mode: WorkbenchMode) => {
  if (workbenchMode.value === mode) return
  applyModeDefaults(mode)
  router.replace({
    path: route.path,
    query: mode === 'draft' ? { ...route.query, mode: 'draft' } : Object.fromEntries(Object.entries(route.query).filter(([key]) => key !== 'mode'))
  })
}

watch(
  () => route.query.mode,
  () => {
    const nextMode = resolveRouteMode()
    if (nextMode !== workbenchMode.value) {
      applyModeDefaults(nextMode)
    }
  }
)

const loadRunAuxiliaryData = async (run: WorkflowRun) => {
  await Promise.allSettled([
    loadTrace(run.runId),
    loadCheckpoints(run.runId),
    loadReviews(run.runId),
    loadMetrics(run)
  ])
}

const refreshRunUntilStable = async (runId: string) => {
  let latest = await workflowApi.getRun(runId)
  selectedRun.value = latest

  for (let index = 0; index < 4 && ['pending', 'planning', 'running'].includes(latest.status); index += 1) {
    await new Promise(resolve => window.setTimeout(resolve, 800))
    latest = await workflowApi.getRun(runId)
    selectedRun.value = latest
  }

  await loadRunAuxiliaryData(latest)
}

const startLegalWorkflow = async () => {
  if (!contractText.value.trim()) return
  loading.start = true
  errorMessage.value = ''
  try {
    const response = await workflowApi.startWorkflow({
      title: modeConfig.value.title,
      domain: 'legal',
      intent: modeConfig.value.intent,
      workflowId: selectedWorkflowId.value,
      reviewMode: 'human_in_loop',
      input: {
        source: 'workbench',
        mode: workbenchMode.value,
        contractText: contractText.value.trim()
      }
    })
    selectedRun.value = response.run
    await refreshRunUntilStable(response.run.runId)
    if (selectedRun.value?.status === 'waiting_review' && selectedRun.value.currentStepId === 'human_review') {
      ElMessage.success(modeConfig.value.successMessage)
    }
  } catch (error: any) {
    errorMessage.value = error?.message || `启动${modeConfig.value.title} Workflow 失败`
  } finally {
    loading.start = false
  }
}

const refreshSelectedRun = async () => {
  if (!selectedRun.value) return
  loading.detail = true
  errorMessage.value = ''
  try {
    await refreshRunUntilStable(selectedRun.value.runId)
  } catch (error: any) {
    errorMessage.value = error?.message || '刷新 WorkflowRun 失败'
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
  metrics.value = await workflowApi.getMetrics({
    domain: 'legal',
    workflowId: run.workflowId,
    source: 'workbench'
  })
}

const submitReview = async (payload: ReviewRequest) => {
  if (!selectedRun.value) return
  loading.reviewSubmit = true
  errorMessage.value = ''
  try {
    const reviewed = await workflowApi.submitReview(selectedRun.value.runId, payload)
    selectedRun.value = reviewed
    await refreshRunUntilStable(reviewed.runId)
    if (contractArtifacts.value.reportMarkdown) {
      ElMessage.success('审核已提交，报告已生成')
    }
  } catch (error: any) {
    errorMessage.value = error?.message || '提交人工审核失败'
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
    await refreshRunUntilStable(resumed.runId)
  } catch (error: any) {
    errorMessage.value = error?.message || '恢复 WorkflowRun 失败'
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
  link.download = `contract-review-trace-${selectedRun.value.runId}.md`
  link.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.contract-review-workbench {
  min-height: 100%;
  color: var(--text-primary);
  overflow: visible;
}

.workbench-header {
  flex-shrink: 0;
}

.workbench-title {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.header-controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.mode-switch {
  display: inline-grid;
  grid-template-columns: repeat(2, minmax(82px, 1fr));
  gap: 4px;
  padding: 4px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  background: var(--bg-input);
}

.mode-switch button {
  min-height: 32px;
  padding: 0 12px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  font-weight: 750;
  cursor: pointer;
  transition: var(--transition);
}

.mode-switch button:hover:not(:disabled) {
  color: var(--primary-color);
}

.mode-switch button.active {
  background: #fff;
  color: var(--primary-color);
  box-shadow: var(--shadow-sm);
}

.mode-switch button:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

h1,
h3,
p,
dl,
dd {
  margin: 0;
}

.header-action,
.primary-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border-radius: 8px;
  cursor: pointer;
  transition: var(--transition);
}

.header-action {
  height: 36px;
  padding: 0 14px;
  border: 1px solid var(--border-light);
  background: #fff;
  color: var(--text-primary);
}

.header-action:hover:not(:disabled) {
  border-color: var(--border-hover);
  color: var(--primary-color);
  transform: translateY(-1px);
}

.header-action:disabled,
.primary-action:disabled {
  cursor: not-allowed;
}

.workbench-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 390px);
  gap: 16px;
  align-items: stretch;
}

.workbench-layout.is-pre-review {
  min-height: min(720px, calc(100vh - 188px));
}

.workbench-layout.is-pre-review .preflight-output-panel,
.workbench-layout.is-pre-review .preflight-monitor-panel {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
}

.workbench-main,
.workbench-side {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
  height: 100%;
}

.workbench-main :deep(.contract-report-preview),
.workbench-side :deep(.call-result-panel) {
  flex: 1 1 auto;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.section-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--primary-color);
}

h3 {
  color: var(--text-primary);
  font-size: 15px;
}

.section-head span,
.input-actions span,
dt,
dd {
  color: var(--text-secondary);
  font-size: 12px;
}

textarea {
  width: 100%;
  min-height: 190px;
  padding: 12px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: var(--bg-input);
  color: var(--text-primary);
  font-size: 13px;
  line-height: 1.6;
  outline: none;
  resize: vertical;
  transition: var(--transition);
}

select {
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

.workflow-select {
  display: grid;
  gap: 5px;
  margin-bottom: 12px;
}

.workflow-select span {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 700;
}

textarea:focus {
  background: #fff;
  border-color: var(--primary-line);
  box-shadow: 0 0 0 3px var(--primary-fade);
}

select:focus {
  background: #fff;
  border-color: var(--primary-line);
  box-shadow: 0 0 0 3px var(--primary-fade);
}

.input-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
}

.primary-action {
  min-height: 42px;
  padding: 0 18px;
  border: 1px solid rgba(255, 255, 255, 0.28);
  background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
  color: #fff;
  font-size: 14px;
  font-weight: 750;
  letter-spacing: 0;
  box-shadow: 0 10px 22px rgba(63, 107, 99, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.18);
  text-shadow: 0 1px 1px rgba(23, 36, 34, 0.18);
}

.primary-action :deep(.el-icon) {
  width: 18px;
  height: 18px;
  font-size: 18px;
  color: currentColor;
}

.primary-action span {
  color: currentColor;
  line-height: 1;
}

.primary-action:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--primary-hover), #2f5a52);
  box-shadow: 0 14px 28px rgba(63, 107, 99, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.primary-action:active:not(:disabled) {
  box-shadow: 0 6px 14px rgba(63, 107, 99, 0.18), inset 0 1px 2px rgba(24, 39, 35, 0.16);
  transform: translateY(0);
}

.primary-action:focus-visible {
  outline: 3px solid var(--primary-fade);
  outline-offset: 2px;
}

.primary-action:disabled {
  border-color: rgba(255, 255, 255, 0.34);
  background: linear-gradient(135deg, #7b84dc, #5f68c9);
  color: rgba(255, 255, 255, 0.96);
  box-shadow: 0 8px 18px rgba(95, 104, 201, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.18);
  text-shadow: 0 1px 1px rgba(31, 39, 102, 0.22);
}

.error-message {
  padding: 10px;
  border: 1px solid rgba(178, 74, 74, 0.18);
  border-radius: 8px;
  color: var(--danger);
  background: rgba(178, 74, 74, 0.08);
  font-size: 13px;
}

.artifact-path-panel dl {
  display: grid;
  gap: 8px;
}

.artifact-path-panel div,
.preflight-config-panel dl > div {
  display: grid;
  gap: 4px;
  padding: 9px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  background: var(--bg-panel);
}

.preflight-flow-panel,
.preflight-output-panel,
.preflight-config-panel,
.preflight-monitor-panel {
  min-width: 0;
}

.preflight-output-panel,
.preflight-monitor-panel {
  min-height: 220px;
}

.preflight-steps,
.preflight-output-grid,
.monitor-slots,
.preflight-config-panel dl {
  display: grid;
  gap: 10px;
}

.preflight-steps {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.preflight-step,
.preflight-output-item,
.monitor-slots article {
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  background: var(--bg-panel);
}

.preflight-step {
  display: grid;
  gap: 8px;
}

.preflight-output-item,
.monitor-slots article {
  display: grid;
  gap: 6px;
}

.preflight-step strong,
.preflight-output-item strong,
.monitor-slots strong {
  color: var(--text-primary);
  font-size: 13px;
  overflow-wrap: anywhere;
}

.preflight-step p,
.preflight-output-item p,
.monitor-slots p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 12px;
  overflow-wrap: anywhere;
}

.preflight-step span {
  justify-self: start;
  padding: 3px 7px;
  border-radius: 999px;
  background: rgba(73, 107, 143, 0.1);
  color: var(--info);
  font-size: 11px;
  font-weight: 800;
}

.preflight-output-grid,
.monitor-slots {
  flex: 1 1 auto;
  max-height: clamp(220px, 34vh, 420px);
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 4px;
  scrollbar-gutter: stable;
}

.preflight-output-grid::-webkit-scrollbar,
.monitor-slots::-webkit-scrollbar {
  width: 5px;
}

.preflight-output-grid::-webkit-scrollbar-track,
.monitor-slots::-webkit-scrollbar-track {
  background: transparent;
}

.preflight-output-grid::-webkit-scrollbar-thumb,
.monitor-slots::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: var(--scrollbar-thumb);
}

dt {
  font-weight: 800;
}

dd {
  overflow-wrap: anywhere;
}

@media (max-width: 1160px) {
  .workbench-layout {
    grid-template-columns: 1fr;
    align-items: start;
    min-height: 0;
  }

  .workbench-side {
    align-self: auto;
    height: auto;
  }

  .workbench-main :deep(.contract-report-preview),
  .workbench-side :deep(.call-result-panel),
  .workbench-layout.is-pre-review .preflight-output-panel,
  .workbench-layout.is-pre-review .preflight-monitor-panel {
    flex: initial;
  }

  .preflight-steps {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .contract-review-workbench {
    padding: 14px;
  }

  .workbench-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .header-controls,
  .mode-switch {
    width: 100%;
  }

  .preflight-steps {
    grid-template-columns: 1fr;
  }
}
</style>
