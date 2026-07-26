<!-- ACG 动态群体智能引擎页面 — 输入合同文本和任务目标，引擎进行解析、分类、风险分析、证据和建议生成 -->
<template>
  <div class="acg-view ui-shell" :class="{ 'has-progress': isSubmitting || progressTracker.progress.value || progressTracker.syncError.value, 'is-draft': !activeRunId }">
    <header class="ui-hero ui-hero--compact">
      <div class="hero-left">
        <div class="ui-icon-badge"><el-icon><Cpu /></el-icon></div>
        <h3>ACG 动态群体智能引擎</h3>
      </div>
      <div class="hero-right">
        <span class="hero-run-chip" :title="activeRunId || '尚未创建运行'">
          <span>RUN</span>
          <code>{{ activeRunId || '—' }}</code>
        </span>
        <button class="hero-icon-action" type="button" title="复制 Run ID" aria-label="复制 Run ID" :disabled="!activeRunId" @click="copyRunId">
          <el-icon><CopyDocument /></el-icon>
        </button>
        <button class="hero-operations" type="button" @click="openOperations">
          <el-icon><Monitor /></el-icon>
          <span>运维查看</span>
        </button>
        <el-tag :type="statusTagType" effect="plain">{{ statusLabel }}</el-tag>
        <el-tag class="hero-engine" effect="plain">engine: acg</el-tag>
      </div>
    </header>

    <!-- 控制台 -->
    <section class="ui-surface ui-surface--pad control-bar" :class="{ collapsed: inputPanelCompact }">
      <button
        class="input-panel-toggle"
        type="button"
        :title="inputPanelExpanded ? '收起合同文本与任务目标' : '展开合同文本与任务目标'"
        :aria-label="inputPanelExpanded ? '收起合同文本与任务目标' : '展开合同文本与任务目标'"
        :aria-expanded="inputPanelExpanded"
        @click="inputPanelExpanded = !inputPanelExpanded"
      >
        <el-icon><ArrowUp v-if="inputPanelExpanded" /><ArrowDown v-else /></el-icon>
      </button>
      <div v-if="inputPanelCompact" class="input-summary">
        <span class="input-summary__copy">
          <el-icon><Document /></el-icon>
          <strong>{{ taskName || '未命名 ACG 任务' }}</strong>
          <small>合同文本 · {{ contractText.length.toLocaleString('zh-CN') }} 字｜{{ planningModeSummary }}｜思考{{ thinkingModeSummary }}</small>
        </span>
      </div>
      <Transition
        :duration="380"
        @before-enter="beforeInputPanelEnter"
        @enter="enterInputPanel"
        @after-enter="afterInputPanelEnter"
        @before-leave="beforeInputPanelLeave"
        @leave="leaveInputPanel"
        @after-leave="afterInputPanelLeave"
      >
        <div v-show="inputPanelExpanded" class="input-panel-expandable">
      <div class="input-fields">
        <div class="input-pane contract-pane">
          <span class="pane-heading">任务资料</span>
          <div class="ctrl-row">
            <label class="ctrl-label">合同文本</label>
            <el-input class="contract-textarea" v-model="contractText" type="textarea" :autosize="{ minRows: 8, maxRows: 16 }" placeholder="输入合同文本，引擎将解析→分类→风险→证据→建议→报告" />
          </div>
          <div class="contract-upload" :class="{ dragging: uploadDragging, populated: selectedContractFile, loading: loading.upload }" @dragenter.prevent="uploadDragging = true" @dragover.prevent="uploadDragging = true" @dragleave.prevent="uploadDragging = false" @drop.prevent="handleContractDrop">
            <input ref="contractFileInput" class="contract-file-input" type="file" accept=".pdf,.docx,.txt,.md,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,text/markdown" @change="handleContractFileSelection" />
            <span class="contract-upload__icon" aria-hidden="true"><el-icon><Document v-if="selectedContractFile" /><UploadFilled v-else /></el-icon></span>
            <span class="contract-upload__copy">
              <strong>{{ selectedContractFile?.name || (loading.upload ? '正在解析合同文件' : '上传合同文件') }}</strong>
              <small v-if="selectedContractFile">{{ formatFileSize(selectedContractFile.size) }} · 已提取 {{ selectedContractFile.textLength.toLocaleString('zh-CN') }} 字</small>
              <small v-else>拖放到此处，或选择 PDF、DOCX、TXT、MD，最大 10MB</small>
            </span>
            <span class="contract-upload__actions">
              <el-button size="small" :loading="loading.upload" @click="openContractFilePicker"><el-icon><UploadFilled /></el-icon>{{ selectedContractFile ? '替换文件' : '选择文件' }}</el-button>
              <el-button v-if="selectedContractFile" circle size="small" title="移除合同文件" aria-label="移除合同文件" @click="clearContractFile"><el-icon><Delete /></el-icon></el-button>
            </span>
          </div>
        </div>
        <div class="input-pane definition-pane">
          <span class="pane-heading">任务定义</span>
          <div class="ctrl-row">
            <label class="ctrl-label">任务目标</label>
            <el-input class="intent-textarea" v-model="userIntent" type="textarea" :autosize="{ minRows: 8, maxRows: 16 }" placeholder="描述 ACG 需要完成的审查目标" />
          </div>
        </div>
      </div>
      <div v-if="advancedSettingsExpanded" class="advanced-settings">
        <label class="advanced-item"><span>故障注入</span><el-checkbox v-model="faultEnabled">启用故障演示与自愈</el-checkbox></label>
        <label class="advanced-item"><span>调试开关</span><el-checkbox v-model="debugTraceEnabled">记录详细调试轨迹</el-checkbox></label>
        <label class="advanced-item advanced-item--wide">
          <span>低熵通信实验项</span>
          <el-checkbox-group v-model="lowEntropyOptions" class="advanced-checks">
            <el-checkbox label="trace_provenance">记录通信血缘</el-checkbox>
            <el-checkbox label="strict_contracts">严格字段契约</el-checkbox>
          </el-checkbox-group>
        </label>
        <label class="advanced-item">
          <span>特殊策略项</span>
          <el-select v-model="specialStrategy" size="small">
            <el-option label="标准策略" value="standard" /><el-option label="证据优先" value="evidence_first" />
            <el-option label="风险并行" value="risk_parallel" /><el-option label="保守复核" value="conservative_review" />
          </el-select>
        </label>
        <template v-if="faultEnabled">
          <label class="advanced-item"><span>故障节点</span><el-select v-model="faultStep" size="small"><el-option v-for="s in faultStepOptions" :key="s" :label="s" :value="s" /></el-select></label>
          <label class="advanced-item"><span>故障类型</span><el-select v-model="faultType" size="small"><el-option label="模型超时" value="timeout" /><el-option label="Agent 崩溃" value="crash" /><el-option label="证据为空" value="empty_evidence" /></el-select></label>
        </template>
      </div>
        </div>
      </Transition>
      <div class="ctrl-options">
        <div v-show="inputPanelExpanded" class="primary-config"><span class="ctrl-label">编排模式</span><el-radio-group v-model="planningMode" size="small"><el-radio-button label="template">模板执行</el-radio-button><el-radio-button label="planner">智能规划</el-radio-button><el-radio-button label="dynamic">动态编排</el-radio-button></el-radio-group></div>
        <div v-show="inputPanelExpanded" class="primary-config"><span class="ctrl-label">思考强度</span><el-radio-group v-model="thinkingMode" size="small"><el-radio-button label="disabled">关闭</el-radio-button><el-radio-button label="standard">标准</el-radio-button><el-radio-button label="deep">深度</el-radio-button></el-radio-group></div>
        <button v-show="inputPanelExpanded" class="advanced-toggle" type="button" :aria-expanded="advancedSettingsExpanded" @click="advancedSettingsExpanded = !advancedSettingsExpanded"><span>高级设置</span><el-icon><ArrowUp v-if="advancedSettingsExpanded" /><ArrowDown v-else /></el-icon></button>
        <el-button :type="mainAction.type" :loading="mainAction.loading" :disabled="mainAction.disabled" @click="handleMainAction">{{ mainAction.label }}</el-button>
      </div>
    </section>

    <WorkflowProgressBar
      v-if="isSubmitting || progressTracker.progress.value || progressTracker.syncError.value"
      :progress="progressTracker.progress.value"
      :loading="isSubmitting || progressTracker.isLoading.value"
      :sync-error="progressTracker.syncError.value"
    />

    <p v-if="startError" class="run-error" role="alert">{{ startError }}</p>

    <WorkflowReviewPanel
      v-if="reviewPending"
      :run-id="activeRunId"
      :progress="progressTracker.progress.value"
      :run="activeRun"
      @reviewed="handleAcgReviewed"
      @conflict="handleAcgReviewConflict"
    />

    <!-- 主区：拓扑 + 指标/血缘 -->
    <div class="acg-grid" v-if="acgView">
      <div class="grid-main">
        <AcgTopologyGraph
          :blueprint="acgView.acgBlueprint"
          :completed-step-ids="acgView.completedStepIds"
          :step-states="acgView.stepStates"
        />
        <AcgDeliverables :deliverables="acgView.deliverables" :final-report="acgView.finalReport" />
        <div class="schedule-strip ui-surface" v-if="scheduleBatches.length">
          <h4>就绪集调度轨迹（动态拓扑）</h4>
          <div class="batch-row">
            <div v-for="b in scheduleBatches" :key="b.id" class="batch">
              <span class="batch-idx">第{{ b.round }}轮</span>
              <span v-for="sid in b.nodes" :key="sid" class="batch-node">{{ sid }}</span>
            </div>
          </div>
        </div>
      </div>
      <div class="grid-side">
        <AcgLowEntropyMetrics :metrics="acgView.lowEntropyMetrics" />
        <AcgProvenancePanel
          :consumptions="acgView.provenance.consumptions"
          :interactions="acgView.interactions"
          :recovery-trace="acgView.recoveryTrace"
          :contract-violations="acgView.contractViolations"
          @export-json="exportAudit('json')"
          @export-csv="exportAudit('csv')"
        />
      </div>
    </div>

    <div v-else class="ui-surface task-brief">
      <strong>ACG 动态智能体长程任务</strong>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch, type DeepReadonly } from 'vue'
import axios from 'axios'
import { ArrowDown, ArrowUp, CopyDocument, Cpu, Delete, Document, Monitor, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import {
  workflowApi,
  type AcgDeliverable,
  type AcgView,
  type WorkflowRun,
  type WorkflowProgress
} from '@/services/api/workflow'
import AcgTopologyGraph from '@/components/agentos/AcgTopologyGraph.vue'
import AcgLowEntropyMetrics from '@/components/agentos/AcgLowEntropyMetrics.vue'
import AcgProvenancePanel from '@/components/agentos/AcgProvenancePanel.vue'
import AcgDeliverables from '@/components/agentos/AcgDeliverables.vue'
import WorkflowProgressBar from '@/components/agentos/WorkflowProgressBar.vue'
import WorkflowReviewPanel from '@/components/agentos/WorkflowReviewPanel.vue'
import { useWorkflowProgress } from '@/composables/useWorkflowProgress'
import { useWorkflowRunsStore } from '@/stores/workflowRuns'
import type { ThinkingMode } from '@/config/modelSettings'
import { fileApi } from '@/services/api/file'
import { buildAcgAuditCsv, buildAcgAuditExport } from '@/utils/acgAuditExport'
import { isWorkflowReviewPending } from '@/utils/workflowReviewState'
import { resolveAcgTaskTitle } from '@/utils/acgTaskTitle'
import { DEFAULT_ACG_PROMPT_PRESET } from '@/test/fixtures/acgPromptPresets'

const WORKFLOW_ID = 'legal_contract_review_v1'
const TEMPLATE_FAULT_STEPS = ['parse_contract', 'classify_clauses', 'risk_detect', 'legal_evidence_match', 'suggestion_generate', 'human_review', 'report_generate']
const DYNAMIC_FAULT_STEPS = ['contract_parse', 'clause_classify', 'risk_detect', 'legal_evidence_match', 'revision_suggest', 'human_review', 'report_generate']

const taskName = ref(DEFAULT_ACG_PROMPT_PRESET.taskName)
const contractText = ref(DEFAULT_ACG_PROMPT_PRESET.contractText)
const userIntent = ref(DEFAULT_ACG_PROMPT_PRESET.userIntent)
const planningMode = ref<'template' | 'planner' | 'dynamic'>('dynamic')
// 快速模式是可验收的默认路径；深度推理由用户显式选择，不能和进度展示绑定。
const thinkingMode = ref<ThinkingMode>('disabled')
const advancedSettingsExpanded = ref(false)
const faultEnabled = ref(false)
const faultStep = ref('risk_detect')
const faultType = ref<'timeout' | 'crash' | 'empty_evidence'>('timeout')
const debugTraceEnabled = ref(false)
const lowEntropyOptions = ref(['trace_provenance', 'strict_contracts'])
const specialStrategy = ref<'standard' | 'evidence_first' | 'risk_parallel' | 'conservative_review'>('standard')
const faultStepOptions = computed(() =>
  planningMode.value === 'dynamic' ? DYNAMIC_FAULT_STEPS : TEMPLATE_FAULT_STEPS
)

watch(planningMode, () => {
  if (!faultStepOptions.value.includes(faultStep.value)) faultStep.value = 'risk_detect'
})

watch(userIntent, value => {
  if (!activeRunId.value) taskName.value = resolveAcgTaskTitle({ title: value })
})

const acgView = ref<AcgView | null>(null)
const activeRun = ref<WorkflowRun | null>(null)
const loading = reactive({ upload: false })
const isSubmitting = ref(false)
const isAcgLoading = ref(false)
const startError = ref<string | null>(null)
const route = useRoute()
const router = useRouter()
const workflowRunsStore = useWorkflowRunsStore()
const activeRunId = ref('')
const inputPanelExpanded = ref(true)
const inputPanelCompact = ref(false)
const loadedRunId = ref('')
const contractFileInput = ref<HTMLInputElement | null>(null)
const uploadDragging = ref(false)
const selectedContractFile = ref<{
  name: string
  size: number
  textLength: number
  extractedText: string
} | null>(null)

const resetDraftContent = () => {
  taskName.value = DEFAULT_ACG_PROMPT_PRESET.taskName
  contractText.value = DEFAULT_ACG_PROMPT_PRESET.contractText
  userIntent.value = DEFAULT_ACG_PROMPT_PRESET.userIntent
  selectedContractFile.value = null
}

const progressTracker = useWorkflowProgress({
  intervalMs: 2000,
  onProgressChanged: value => workflowRunsStore.updateObservedState(
    value.runId,
    value.status,
    value.phase,
    value.updatedAt
  ),
  onTerminal: handleTerminal
})
const reviewPending = computed(() => Boolean(
  activeRunId.value && isWorkflowReviewPending(progressTracker.progress.value, activeRun.value)
))

const CONTRACT_FILE_MAX_SIZE = 10 * 1024 * 1024
const CONTRACT_FILE_EXTENSIONS = ['pdf', 'docx', 'txt', 'md']

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

const openContractFilePicker = () => {
  if (!loading.upload) contractFileInput.value?.click()
}

const validateContractFile = (file: File) => {
  const extension = file.name.split('.').pop()?.toLowerCase() || ''
  if (!CONTRACT_FILE_EXTENSIONS.includes(extension)) {
    throw new Error('仅支持 PDF、DOCX、TXT、MD 格式')
  }
  if (file.size <= 0) throw new Error('文件内容为空')
  if (file.size > CONTRACT_FILE_MAX_SIZE) throw new Error('文件不能超过 10MB')
}

const processContractFile = async (file: File) => {
  if (loading.upload) return

  try {
    validateContractFile(file)
    loading.upload = true
    const result = await fileApi.extractDocumentText(file)
    const extractedText = (result.text || '').trim()
    if (!extractedText) throw new Error('未能从文件中提取到文本，请确认文档包含可复制文字')

    contractText.value = extractedText
    selectedContractFile.value = {
      name: file.name,
      size: file.size,
      textLength: extractedText.length,
      extractedText
    }
    ElMessage.success(`已载入合同文件：${file.name}`)
  } catch (error: any) {
    ElMessage.error(error?.message || '合同文件上传失败')
  } finally {
    loading.upload = false
    uploadDragging.value = false
    if (contractFileInput.value) contractFileInput.value.value = ''
  }
}

const handleContractFileSelection = (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) void processContractFile(file)
}

const handleContractDrop = (event: DragEvent) => {
  uploadDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) void processContractFile(file)
}

const clearContractFile = () => {
  const selected = selectedContractFile.value
  if (selected && contractText.value === selected.extractedText) contractText.value = ''
  selectedContractFile.value = null
  if (contractFileInput.value) contractFileInput.value.value = ''
}

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    completed: '已完成', failed: '失败', running: '执行中',
    waiting_review: '待审核', cancelled: '已取消', retrying: '重试中', planning: '规划中', pending: '待启动'
  }
  const status = progressTracker.progress.value?.status || acgView.value?.status
  return status ? (map[status] || status) : '准备中'
})
const statusTagType = computed(() => {
  const phase = progressTracker.progress.value?.phase
  const s = progressTracker.progress.value?.status || acgView.value?.status
  if (s === 'completed') return 'success'
  if (s === 'failed') return 'danger'
  if (s === 'waiting_review' || phase === 'review' || phase === 'recovery') return 'warning'
  return 'info'
})
const effectiveStatus = computed(() => progressTracker.progress.value?.status || acgView.value?.status || '')
const effectivePhase = computed(() => progressTracker.progress.value?.phase || '')
const planningModeSummary = computed(() => ({ template: '模板执行', planner: '智能规划', dynamic: '动态编排' })[planningMode.value])
const thinkingModeSummary = computed(() => ({ disabled: '关闭', standard: '标准', deep: '深度' })[thinkingMode.value])
const mainAction = computed<{
  action: 'start' | 'planning' | 'view' | 'review' | 'rerun' | 'retry'
  label: string
  type: 'primary' | 'warning' | 'danger' | 'info'
  loading: boolean
  disabled: boolean
}>(() => {
  const status = effectiveStatus.value
  const phase = effectivePhase.value
  if (isSubmitting.value || (activeRunId.value && ['understanding', 'planning', 'graph_building'].includes(phase))) {
    return { action: 'planning', label: '正在生成编排', type: 'info', loading: true, disabled: true }
  }
  if (!activeRunId.value) return { action: 'start', label: '启动 ACG', type: 'primary', loading: false, disabled: false }
  if (status === 'waiting_review' || phase === 'review') return { action: 'review', label: '进入人工审核', type: 'warning', loading: false, disabled: false }
  if (status === 'completed' || phase === 'completed') return { action: 'rerun', label: '基于当前配置重新运行', type: 'primary', loading: false, disabled: false }
  if (status === 'failed' || phase === 'failed') return { action: 'retry', label: '修改配置并重试', type: 'danger', loading: false, disabled: false }
  if (status === 'cancelled' || phase === 'cancelled') return { action: 'retry', label: '重新运行', type: 'primary', loading: false, disabled: false }
  if (status === 'pending' || status === 'planning') return { action: 'planning', label: '正在生成编排', type: 'info', loading: true, disabled: true }
  return { action: 'view', label: '查看运行', type: 'primary', loading: false, disabled: false }
})
// 从调度 trace 还原"每轮就绪集批次"，可视化并行调度
const scheduleBatches = computed(() => {
  const events = acgView.value?.scheduleTrace || []
  const batches = new Map<string, { id: string; round: number; nodes: string[] }>()
  for (const e of events) {
    const batch = (e.payload?.batch as string[]) || (e.stepId ? [e.stepId] : [])
    const round = Number(e.payload?.round || batches.size + 1)
    const id = String(e.payload?.batchId || `${round}:${e.eventId}`)
    if (batch.length && !batches.has(id)) {
      batches.set(id, { id, round, nodes: batch })
    }
  }
  return Array.from(batches.values()).sort((a, b) => a.round - b.round)
})

const hasStepOutput = (output?: Record<string, any>) => {
  return !!output && Object.keys(output).length > 0
}

const deliverablesFromRun = (run: WorkflowRun): AcgDeliverable[] => {
  return (run.steps || [])
    .filter((step) => hasStepOutput(step.output))
    .map((step) => ({
      stepId: step.stepId,
      name: step.name,
      status: step.status,
      output: step.output || {}
    }))
}

const asMarkdown = (value: unknown): string | null => {
  return typeof value === 'string' && value.trim().length > 0 ? value : null
}

const finalReportFromRun = (run: WorkflowRun): string | null => {
  let finalReport: string | null = null
  for (const step of run.steps || []) {
    const output = step.output || {}
    const markdown = asMarkdown(output.final_answer) || asMarkdown(output.report_markdown) || asMarkdown(output.report) || asMarkdown(output.final_report)
    if (markdown) finalReport = markdown
  }

  if (finalReport) return finalReport

  const runOutput = run.output || {}
  const direct = asMarkdown(runOutput.final_answer) || asMarkdown(runOutput.report_markdown) || asMarkdown(runOutput.report) || asMarkdown(runOutput.final_report)
  if (direct) return direct

  const artifacts = runOutput.artifacts
  if (artifacts && typeof artifacts === 'object') {
    for (const artifact of Object.values(artifacts as Record<string, any>)) {
      if (!artifact || typeof artifact !== 'object') continue
      const markdown = asMarkdown(artifact.final_answer) || asMarkdown(artifact.report_markdown) || asMarkdown(artifact.report) || asMarkdown(artifact.final_report)
      if (markdown) finalReport = markdown
    }
  }

  return finalReport
}

const hydrateAcgView = (view: AcgView, run: WorkflowRun): AcgView => {
  return {
    ...view,
    deliverables: view.deliverables.length ? view.deliverables : deliverablesFromRun(run),
    finalReport: view.finalReport || finalReportFromRun(run)
  }
}

const ACTIVE_TOPOLOGY_PHASES = new Set(['executing', 'recovery', 'review'])
const TOPOLOGY_REFRESH_MS = 8000
let topologyController: AbortController | null = null
let topologyTimer: ReturnType<typeof setTimeout> | null = null
let topologyGeneration = 0
let lastTopologyRefreshAt = 0
let lastTopologyUpdatedAt: string | null = null
let submitController: AbortController | null = null
let inputCollapseTimer: ReturnType<typeof setTimeout> | null = null
let inputPanelCompactTimer: ReturnType<typeof setTimeout> | null = null

const clearInputCollapseTimer = () => {
  if (inputCollapseTimer !== null) window.clearTimeout(inputCollapseTimer)
  inputCollapseTimer = null
}

const clearInputPanelCompactTimer = () => {
  if (inputPanelCompactTimer !== null) window.clearTimeout(inputPanelCompactTimer)
  inputPanelCompactTimer = null
}

const inputPanelElement = (element: Element) => element as HTMLElement

const beforeInputPanelEnter = (element: Element) => {
  const panel = inputPanelElement(element)
  inputPanelCompact.value = false
  panel.style.height = '0'
  panel.style.opacity = '0'
  panel.style.transform = 'translateY(-8px)'
}

const enterInputPanel = (element: Element) => {
  const panel = inputPanelElement(element)
  window.requestAnimationFrame(() => {
    panel.style.height = `${panel.scrollHeight}px`
    panel.style.opacity = '1'
    panel.style.transform = 'translateY(0)'
  })
}

const afterInputPanelEnter = (element: Element) => {
  clearInputPanelCompactTimer()
  const panel = inputPanelElement(element)
  panel.style.height = 'auto'
  panel.style.opacity = ''
  panel.style.transform = ''
}

const beforeInputPanelLeave = (element: Element) => {
  const panel = inputPanelElement(element)
  panel.style.height = `${panel.scrollHeight}px`
  panel.style.opacity = '1'
  panel.style.transform = 'translateY(0)'
}

const leaveInputPanel = (element: Element) => {
  const panel = inputPanelElement(element)
  void panel.offsetHeight
  window.requestAnimationFrame(() => {
    panel.style.height = '0'
    panel.style.opacity = '0'
    panel.style.transform = 'translateY(-8px)'
  })
}

const afterInputPanelLeave = (element: Element) => {
  clearInputPanelCompactTimer()
  const panel = inputPanelElement(element)
  panel.style.height = ''
  panel.style.opacity = ''
  panel.style.transform = ''
  if (!inputPanelExpanded.value) inputPanelCompact.value = true
}

const scheduleInputCollapse = (delayMs = 1400) => {
  clearInputCollapseTimer()
  inputCollapseTimer = window.setTimeout(() => {
    inputCollapseTimer = null
    inputPanelExpanded.value = false
  }, delayMs)
}

const clearTopologyTimer = () => {
  if (topologyTimer !== null) {
    window.clearTimeout(topologyTimer)
    topologyTimer = null
  }
}

const clearRunData = () => {
  clearTopologyTimer()
  topologyGeneration += 1
  topologyController?.abort()
  topologyController = null
  acgView.value = null
  activeRun.value = null
  loadedRunId.value = ''
  isAcgLoading.value = false
  lastTopologyRefreshAt = 0
  lastTopologyUpdatedAt = null
}

const enterNewAcgDraft = () => {
  submitController?.abort()
  progressTracker.reset()
  clearRunData()
  clearInputCollapseTimer()
  clearInputPanelCompactTimer()
  activeRunId.value = ''
  startError.value = null
  inputPanelExpanded.value = true
  inputPanelCompact.value = false
  advancedSettingsExpanded.value = false
  resetDraftContent()
}

async function refreshAcgForRun(runId: string, force = false): Promise<void> {
  if (!runId || runId !== activeRunId.value) return
  if (!force && progressTracker.progress.value?.updatedAt === lastTopologyUpdatedAt) return

  const requestGeneration = ++topologyGeneration
  topologyController?.abort()
  topologyController = new AbortController()
  const signal = topologyController.signal
  isAcgLoading.value = true
  try {
    const [run, view] = await Promise.all([
      workflowApi.getRun(runId, { signal }),
      workflowApi.getAcgView(runId, { signal })
    ])
    if (requestGeneration !== topologyGeneration || runId !== activeRunId.value) return
    acgView.value = hydrateAcgView(view, run)
    activeRun.value = run
    taskName.value = resolveAcgTaskTitle(run)
    if (typeof run.input?.contractText === 'string') contractText.value = run.input.contractText
    if (typeof run.input?.userIntent === 'string') userIntent.value = run.input.userIntent
    loadedRunId.value = runId
    lastTopologyRefreshAt = Date.now()
    lastTopologyUpdatedAt = progressTracker.progress.value?.updatedAt ?? null
  } catch (error: unknown) {
    if (!axios.isCancel(error) && requestGeneration === topologyGeneration && force) {
      ElMessage.warning('最终 ACG 数据暂时未能加载，请稍后刷新')
    }
  } finally {
    if (requestGeneration === topologyGeneration) {
      topologyController = null
      isAcgLoading.value = false
    }
  }
}

const scheduleTopologyRefresh = (value: DeepReadonly<WorkflowProgress>) => {
  if (!ACTIVE_TOPOLOGY_PHASES.has(value.phase) || value.runId !== activeRunId.value) return
  if (value.updatedAt === lastTopologyUpdatedAt) return
  clearTopologyTimer()
  const remaining = Math.max(0, TOPOLOGY_REFRESH_MS - (Date.now() - lastTopologyRefreshAt))
  topologyTimer = window.setTimeout(() => {
    topologyTimer = null
    void refreshAcgForRun(value.runId)
  }, remaining)
}

async function handleTerminal(value: WorkflowProgress): Promise<void> {
  clearTopologyTimer()
  await refreshAcgForRun(value.runId, true)
  if (value.phase === 'completed') ElMessage.success('ACG 引擎执行完成')
  if (value.phase === 'failed') ElMessage.error('ACG 工作流执行失败')
  if (value.phase === 'cancelled') ElMessage.info('ACG 工作流已取消')
}

watch(
  () => progressTracker.progress.value,
  (value, previous) => {
    if (!value) return
    const stateChanged = value.status !== previous?.status || value.phase !== previous?.phase
    if (value.status === 'failed' || value.phase === 'failed') {
      clearInputCollapseTimer()
      inputPanelExpanded.value = true
    } else if (stateChanged && (value.status === 'waiting_review' || ['review', 'completed', 'cancelled'].includes(value.phase))) {
      scheduleInputCollapse(0)
    }
    if (isWorkflowReviewPending(value, activeRun.value) && !isWorkflowReviewPending(previous, activeRun.value)) {
      clearTopologyTimer()
      void refreshAcgForRun(value.runId, true)
      return
    }
    scheduleTopologyRefresh(value)
  }
)

watch(inputPanelExpanded, value => {
  clearInputPanelCompactTimer()
  if (value) {
    inputPanelCompact.value = false
    return
  }
  advancedSettingsExpanded.value = false
  inputPanelCompactTimer = window.setTimeout(() => {
    inputPanelCompactTimer = null
    if (!inputPanelExpanded.value) inputPanelCompact.value = true
  }, 380)
})

watch(
  () => route.query.runId,
  (value) => {
    if (typeof value !== 'string' || !value.trim()) return
    const runId = value.trim()
    if (runId === activeRunId.value && progressTracker.runId.value === runId) return
    progressTracker.reset()
    clearRunData()
    startError.value = null
    activeRunId.value = runId
    inputPanelExpanded.value = false
    inputPanelCompact.value = true
    advancedSettingsExpanded.value = false
    workflowRunsStore.register({ runId, source: 'restored' })
    void progressTracker.start(runId, { fresh: false })
  },
  { immediate: true }
)

const copyRunId = async () => {
  if (!activeRunId.value) return
  try {
    await navigator.clipboard.writeText(activeRunId.value)
    ElMessage.success('Run ID 已复制')
  } catch {
    ElMessage.warning('浏览器未授权剪贴板，请直接选择 Run ID')
  }
}

const openOperations = () => {
  void router.push({
    path: '/agentos-console',
    query: activeRunId.value ? { runId: activeRunId.value, source: 'acg' } : { source: 'acg' }
  })
}

const scrollToSection = (selector: string) => {
  const target = document.querySelector<HTMLElement>(selector)
  if (!target) return
  const top = target.getBoundingClientRect().top + window.scrollY - 16
  window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' })
}

const handleMainAction = () => {
  if (mainAction.value.action === 'start' || mainAction.value.action === 'rerun' || mainAction.value.action === 'retry') {
    void startRun()
    return
  }
  if (mainAction.value.action === 'review') {
    scrollToSection('.workflow-review')
    return
  }
  if (mainAction.value.action === 'view') scrollToSection('.workflow-progress')
}

const handleAcgReviewed = async (run: WorkflowRun) => {
  if (run.runId !== activeRunId.value) return
  activeRun.value = run
  await progressTracker.refresh()
  await refreshAcgForRun(run.runId, true)
}

const handleAcgReviewConflict = async () => {
  await progressTracker.refresh()
  if (activeRunId.value) await refreshAcgForRun(activeRunId.value, true)
}

const downloadText = (content: string, filename: string, type: string) => {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

const exportAudit = (format: 'json' | 'csv') => {
  if (!acgView.value) return
  const filename = `acg-audit-${acgView.value.runId}.${format}`
  if (format === 'json') {
    downloadText(
      JSON.stringify(buildAcgAuditExport(acgView.value), null, 2),
      filename,
      'application/json;charset=utf-8'
    )
  } else {
    downloadText(`\ufeff${buildAcgAuditCsv(acgView.value)}`, filename, 'text/csv;charset=utf-8')
  }
  ElMessage.success(`ACG 审计 ${format.toUpperCase()} 已导出`)
}

const startRun = async () => {
  if (isSubmitting.value) return
  if (!contractText.value.trim()) {
    ElMessage.warning('请输入合同文本')
    return
  }
  if (!taskName.value.trim()) {
    ElMessage.warning('请输入任务名称')
    return
  }
  isSubmitting.value = true
  startError.value = null
  submitController?.abort()
  submitController = new AbortController()
  progressTracker.reset()
  clearRunData()
  activeRunId.value = ''
  try {
    const intentText = userIntent.value.trim() || '审查合同风险并生成报告'
    const input: Record<string, unknown> = {
      source: 'acg',
      taskName: taskName.value.trim(),
      contractText: contractText.value,
      userIntent: intentText,
      planningMode: planningMode.value,
      thinkingMode: thinkingMode.value,
      debugTrace: debugTraceEnabled.value,
      lowEntropyOptions: [...lowEntropyOptions.value],
      specialStrategy: specialStrategy.value
    }
    if (planningMode.value !== 'template') input.usePlanner = true
    if (planningMode.value === 'dynamic') input.forceDynamicPlanning = true
    if (faultEnabled.value) {
      input.faultInjection = { step_id: faultStep.value, fault_type: faultType.value, max_triggers: 1 }
    }
    const clientRequestId = createClientRequestId()
    const res = await workflowApi.startWorkflowAsync({
      title: taskName.value.trim(),
      domain: 'legal',
      intent: 'contract_review_acg',
      workflowId: WORKFLOW_ID,
      reviewMode: 'human_in_loop',
      input,
      clientRequestId
    }, { signal: submitController.signal })
    activeRunId.value = res.run.runId
    scheduleInputCollapse()
    advancedSettingsExpanded.value = false
    workflowRunsStore.register({
      runId: res.run.runId,
      taskId: res.task.taskId,
      workflowId: res.run.workflowId || WORKFLOW_ID,
      source: 'acg',
      status: res.run.status,
      phase: res.run.lifecyclePhase
    })
    window.dispatchEvent(new Event('acg-runs-refresh'))
    void progressTracker.start(res.run.runId, { fresh: true })
    await router.replace({ query: { ...route.query, runId: res.run.runId } })
  } catch (error: unknown) {
    if (axios.isCancel(error)) return
    startError.value = startErrorMessage(error)
  } finally {
    isSubmitting.value = false
    submitController = null
  }
}

const createClientRequestId = (): string => {
  if (typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  const bytes = crypto.getRandomValues(new Uint8Array(16))
  bytes[6] = (bytes[6] & 0x0f) | 0x40
  bytes[8] = (bytes[8] & 0x3f) | 0x80
  const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0'))
  return `${hex.slice(0, 4).join('')}-${hex.slice(4, 6).join('')}-${hex.slice(6, 8).join('')}-${hex.slice(8, 10).join('')}-${hex.slice(10).join('')}`
}

const startErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 409) {
      return '相同请求标识已用于不同参数，请重新发起任务'
    }
    if (!error.response) return '任务未能启动：网络连接暂时不可用'
  }
  return '任务未能启动'
}

onMounted(() => {
  window.addEventListener('acg-new-task', enterNewAcgDraft)
})

onBeforeUnmount(() => {
  submitController?.abort()
  clearTopologyTimer()
  topologyGeneration += 1
  topologyController?.abort()
  clearInputCollapseTimer()
  clearInputPanelCompactTimer()
  window.removeEventListener('acg-new-task', enterNewAcgDraft)
})
</script>

<style scoped>
.acg-view.ui-shell { display: flex; flex-direction: column; gap: 0; padding: var(--space-sm) var(--space-md); }
.acg-view.is-draft { min-height: calc(100dvh + 15px); }
.acg-view > .ui-hero { border-bottom: 0; border-radius: 8px 8px 0 0; }
.acg-view > .control-bar { border-top: 0; border-radius: 0 0 8px 8px; }
.acg-view.is-draft > .control-bar { flex: 1 1 auto; }
.acg-view.has-progress > .control-bar { border-bottom: 0; border-radius: 0; box-shadow: none; }
.acg-view.has-progress > :deep(.workflow-progress) { border-top: 0; border-radius: 0 0 8px 8px; }
.hero-left { display: flex; align-items: center; gap: 10px; min-width: 0; }
.ui-hero h3 { overflow: hidden; margin: 0; color: var(--text-primary); font-size: 18px; font-weight: 800; line-height: 1.2; text-overflow: ellipsis; white-space: nowrap; }
.hero-right { display: flex; gap: 8px; align-items: center; justify-content: flex-end; flex-wrap: nowrap; }
.hero-run-chip { min-width: 0; height: 30px; display: inline-flex; align-items: center; gap: 5px; padding: 0 9px; border: 1px solid var(--border-light); border-radius: 6px; background: var(--bg-input); color: var(--text-muted); font-size: 10px; }
.hero-run-chip code { overflow: hidden; max-width: 150px; color: var(--text-secondary); font-family: var(--font-mono, ui-monospace, SFMono-Regular, Consolas, monospace); font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.hero-icon-action, .hero-operations { height: 32px; display: inline-flex; align-items: center; justify-content: center; border: 1px solid var(--border-light); background: var(--surface-solid); color: var(--text-secondary); cursor: pointer; transition: var(--transition); }
.hero-icon-action { width: 32px; padding: 0; border-radius: 50%; }
.hero-operations { gap: 5px; padding: 0 11px; border-radius: 7px; font: inherit; font-size: 11px; }
.hero-icon-action:hover:not(:disabled), .hero-operations:hover { border-color: var(--primary-line); background: var(--primary-fade); color: var(--primary-color); }
.hero-icon-action:disabled { cursor: not-allowed; opacity: .5; }
.hero-icon-action:focus-visible, .hero-operations:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }
.hero-engine { color: var(--primary-color); }

.control-bar { position: relative; display: flex; flex-direction: column; gap: var(--space-md); padding-right: 52px; padding-bottom: 10px; }
.control-bar.collapsed { flex-direction: row; align-items: center; gap: 12px; padding: 9px 52px 9px 14px; }
.control-bar.collapsed .input-summary { flex: 1 1 auto; }
.control-bar.collapsed .ctrl-options { flex: 0 0 auto; padding: 0; border: 0; }
.input-panel-expandable {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  min-width: 0;
  overflow: hidden;
  transform-origin: top center;
  transition:
    height 380ms cubic-bezier(0.22, 1, 0.36, 1),
    opacity 220ms ease,
    transform 380ms cubic-bezier(0.22, 1, 0.36, 1);
  will-change: height, opacity, transform;
}
.input-panel-toggle {
  position: absolute; top: 10px; right: 12px; z-index: 1;
  width: 28px; height: 28px; display: inline-grid; place-items: center;
  padding: 0; border: 1px solid var(--border-light); border-radius: 6px;
  background: var(--surface-solid); color: var(--text-secondary); cursor: pointer;
  transition: var(--transition);
}
.input-panel-toggle:hover { border-color: var(--primary-line); color: var(--primary-color); background: var(--primary-fade); }
.input-panel-toggle:focus-visible { outline: none; box-shadow: 0 0 0 3px var(--primary-fade); }
.input-fields { display: grid; grid-template-columns: minmax(0, 13fr) minmax(280px, 7fr); align-items: stretch; gap: 24px; min-width: 0; }
.input-pane { display: flex; flex-direction: column; gap: 10px; min-width: 0; }
.contract-pane .ctrl-row { flex: 1 1 auto; min-height: 0; }
.contract-pane .contract-textarea { flex: 1 1 auto; min-height: 0; }
.definition-pane { min-width: 0; gap: 12px; }
.pane-heading { color: var(--text-primary); font-size: 13px; font-weight: 750; }
.pane-heading small { margin-left: 4px; color: var(--text-disabled); font-size: 10px; font-weight: 600; }
.input-summary { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-width: 0; }
.input-summary__copy { display: flex; align-items: center; gap: 7px; min-width: 0; color: var(--text-secondary); }
.input-summary__copy .el-icon { flex: 0 0 auto; color: var(--primary-color); }
.input-summary__copy strong { flex: 0 1 auto; overflow: hidden; max-width: min(320px, 34vw); color: var(--text-primary); font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.input-summary__copy small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 11px; }
.run-error {
  margin: 0;
  padding: 10px 12px;
  border: 1px solid color-mix(in srgb, var(--danger) 38%, var(--border-light));
  border-radius: 6px;
  background: var(--danger-fade);
  color: var(--danger);
  font-size: 12px;
}
.ctrl-row { display: flex; flex-direction: column; gap: 6px; }
.ctrl-label { font-size: 12px; font-weight: 600; color: var(--text-secondary); }
.ctrl-options { order: 2; display: flex; align-items: center; gap: 18px; flex-wrap: wrap; padding-top: 4px; }
.primary-config { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.primary-config :deep(.el-radio-button__inner) { border-color: transparent; background: transparent; box-shadow: none; }
.primary-config :deep(.el-radio-button.is-active .el-radio-button__inner) { border-color: var(--primary-line); background: var(--primary-fade); color: var(--primary-color); }
.advanced-toggle {
  min-height: 30px; display: inline-flex; align-items: center; gap: 5px; padding: 0 9px;
  border: 1px solid var(--border-light); border-radius: 6px; background: var(--surface-solid);
  color: var(--text-secondary); cursor: pointer; transition: var(--transition);
}
.advanced-toggle:hover { border-color: var(--primary-line); color: var(--primary-color); }
.ctrl-options > :deep(.el-button:last-child) { margin-left: auto; }
.advanced-settings {
  order: 3;
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px;
  padding: 12px; border: 1px solid var(--border-light); border-radius: 7px; background: var(--bg-input);
}
.advanced-item { display: flex; flex-direction: column; gap: 7px; min-width: 0; }
.advanced-item > span { color: var(--text-secondary); font-size: 11px; font-weight: 700; }
.advanced-item--wide { grid-column: span 2; }
.advanced-checks { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.contract-textarea :deep(.el-textarea__inner),
.intent-textarea :deep(.el-textarea__inner) {
  line-height: 1.72;
  font-size: 14px;
  padding: 12px 14px;
  resize: vertical;
}
.contract-pane .contract-textarea :deep(.el-textarea__inner) { height: 100% !important; }
.acg-view.is-draft .input-panel-expandable,
.acg-view.is-draft .input-fields,
.acg-view.is-draft .definition-pane .ctrl-row,
.acg-view.is-draft .contract-textarea,
.acg-view.is-draft .intent-textarea { flex: 1 1 auto; min-height: 0; }
.acg-view.is-draft .contract-textarea :deep(.el-textarea__inner),
.acg-view.is-draft .intent-textarea :deep(.el-textarea__inner) { height: 100% !important; }
.acg-view.is-draft .ctrl-options { margin-top: auto; }
.contract-textarea :deep(.el-textarea__inner),
.intent-textarea :deep(.el-textarea__inner) {
  height: clamp(330px, 43vh, 480px) !important;
  min-height: clamp(330px, 43vh, 480px) !important;
}

.contract-file-input { display: none; }
.contract-upload {
  min-height: 42px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 8px;
  border: 0;
  border-radius: 0;
  background: var(--bg-input);
  transition: border-color 0.16s ease, background-color 0.16s ease;
}
.contract-upload.dragging {
  border-color: var(--primary-color);
  background: var(--primary-fade);
}
.contract-upload.loading { opacity: 0.72; }
.contract-upload__icon {
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
  display: inline-grid;
  place-items: center;
  border-radius: 5px;
  background: var(--surface-solid);
  color: var(--primary-color);
  box-shadow: 0 0 0 1px var(--border-light);
}
.contract-upload__copy {
  min-width: 0;
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.contract-upload__copy strong,
.contract-upload__copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.contract-upload__copy strong { color: var(--text-primary); font-size: 11px; font-weight: 700; }
.contract-upload__copy small { color: var(--text-secondary); font-size: 10px; }
.contract-upload__actions { flex: 0 0 auto; display: inline-flex; align-items: center; gap: 6px; }

.acg-view > :deep(.workflow-review) { margin-top: var(--space-lg); }
.acg-grid { display: grid; grid-template-columns: minmax(0, 1fr) 380px; gap: 11px; margin-top: 11px; align-items: stretch; min-width: 0; }
.grid-main { display: flex; flex-direction: column; gap: var(--space-lg); min-width: 0; }
.grid-side { display: flex; flex-direction: column; gap: var(--space-lg); min-width: 0; min-height: 0; }
.grid-side :deep(.acg-provenance) { flex: 1 1 auto; min-height: 0; }

.schedule-strip { padding: var(--space-md); }
.schedule-strip h4 { margin: 0 0 var(--space-sm); font-size: 13px; font-weight: 700; color: var(--text-primary); }
.batch-row { display: flex; gap: var(--space-md); flex-wrap: wrap; }
.batch { display: flex; align-items: center; gap: 4px; padding: 4px 8px; background: var(--bg-input); border-radius: var(--radius-md); }
.batch-idx { font-size: 11px; color: var(--text-secondary); font-weight: 600; margin-right: 4px; }
.batch-node { font-size: 11px; padding: 2px 8px; background: var(--primary-fade); color: var(--primary-color); border-radius: 10px; font-family: monospace; }

.task-brief {
  min-height: 62px;
  display: grid;
  place-items: center;
  margin-top: var(--space-md);
  padding: 12px 20px;
  border-radius: var(--radius-lg);
}
.acg-view.is-draft > .task-brief { flex: 0 0 62px; margin-bottom: var(--space-md); }
.task-brief strong { color: var(--text-secondary); font-size: 13px; font-weight: 700; letter-spacing: .02em; }

@keyframes restore-pulse {
  to { opacity: 1; }
}

@media (max-width: 1160px) {
  .acg-grid { grid-template-columns: minmax(0, 1fr); }
  .advanced-settings { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 720px) {
  .ui-hero { flex-wrap: wrap; align-items: flex-start; }
  .hero-left { width: 100%; }
  .hero-right { justify-content: flex-start; width: 100%; flex-wrap: wrap; }
  .hero-run-chip code { max-width: 120px; }
  .contract-upload { align-items: flex-start; flex-wrap: wrap; }
  .contract-upload__copy { width: calc(100% - 34px); }
  .contract-upload__actions { width: 100%; padding-left: 34px; }
  .input-fields { grid-template-columns: 1fr; }
  .definition-pane { padding-top: 14px; }
  .advanced-settings { grid-template-columns: 1fr; }
  .advanced-item--wide { grid-column: auto; }
  .ctrl-options > :deep(.el-button:last-child) { width: 100%; margin-left: 0; }
  .input-summary__copy { align-items: flex-start; flex-wrap: wrap; }
  .input-summary__copy small { width: 100%; white-space: normal; }
  .control-bar.collapsed { align-items: stretch; flex-direction: column; }
  .control-bar.collapsed .ctrl-options { width: 100%; }
}

@media (prefers-reduced-motion: reduce) {
  .input-panel-expandable { transition-duration: 1ms; }
}
</style>
