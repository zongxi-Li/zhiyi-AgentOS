<!-- ACG 动态群体智能引擎页面 — 输入合同文本和任务目标，引擎进行解析、分类、风险分析、证据和建议生成 -->
<template>
  <div class="acg-view ui-shell">
    <header class="ui-hero">
      <div class="hero-left">
        <div class="ui-icon-badge"><el-icon><Cpu /></el-icon></div>
        <div>
          <h1>ACG 动态群体智能引擎</h1>
          <p class="hero-sub">Core Native 自研 · 就绪集并行调度 · 低熵通信 · 故障自愈</p>
        </div>
      </div>
      <div class="hero-right">
        <div v-if="activeRunId" class="run-context">
          <span class="run-id" :title="activeRunId">
            <span>RUN</span>
            <code>{{ activeRunId }}</code>
          </span>
          <el-button circle size="small" title="复制 Run ID" aria-label="复制 Run ID" @click="copyRunId">
            <el-icon><CopyDocument /></el-icon>
          </el-button>
          <el-button size="small" title="在 AgentOS 运维页查看" @click="openInConsole">
            <el-icon><Monitor /></el-icon>
            运维查看
          </el-button>
          <el-button v-if="activeRunReference?.conversationId" size="small" title="返回关联对话" @click="openLinkedChat">
            <el-icon><ChatDotRound /></el-icon>
            返回 Chat
          </el-button>
        </div>
        <el-tag v-if="activeRunId" :type="statusTagType" effect="dark">{{ statusLabel }}</el-tag>
        <el-tag v-if="acgView" type="info" effect="plain">engine: {{ acgView.engine }}</el-tag>
      </div>
    </header>

    <!-- 控制台 -->
    <section class="ui-surface ui-surface--pad control-bar">
      <div class="ctrl-row">
        <label class="ctrl-label">合同文本</label>
        <el-input
          class="contract-textarea"
          v-model="contractText"
          type="textarea"
          :autosize="{ minRows: 5, maxRows: 12 }"
          placeholder="输入合同文本，引擎将解析→分类→风险→证据→建议→报告"
        />
        <div
          class="contract-upload"
          :class="{ dragging: uploadDragging, populated: selectedContractFile, loading: loading.upload }"
          @dragenter.prevent="uploadDragging = true"
          @dragover.prevent="uploadDragging = true"
          @dragleave.prevent="uploadDragging = false"
          @drop.prevent="handleContractDrop"
        >
          <input
            ref="contractFileInput"
            class="contract-file-input"
            type="file"
            accept=".pdf,.docx,.txt,.md,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,text/markdown"
            @change="handleContractFileSelection"
          />
          <span class="contract-upload__icon" aria-hidden="true">
            <el-icon><Document v-if="selectedContractFile" /><UploadFilled v-else /></el-icon>
          </span>
          <span class="contract-upload__copy">
            <strong>{{ selectedContractFile?.name || (loading.upload ? '正在解析合同文件' : '上传合同文件') }}</strong>
            <small v-if="selectedContractFile">
              {{ formatFileSize(selectedContractFile.size) }} · 已提取 {{ selectedContractFile.textLength.toLocaleString('zh-CN') }} 字
            </small>
            <small v-else>拖放到此处，或选择 PDF、DOCX、TXT、MD，最大 10MB</small>
          </span>
          <span class="contract-upload__actions">
            <el-button size="small" :loading="loading.upload" @click="openContractFilePicker">
              <el-icon><UploadFilled /></el-icon>
              {{ selectedContractFile ? '替换文件' : '选择文件' }}
            </el-button>
            <el-button
              v-if="selectedContractFile"
              circle
              size="small"
              title="移除合同文件"
              aria-label="移除合同文件"
              @click="clearContractFile"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </span>
        </div>
      </div>
      <div class="ctrl-row">
        <label class="ctrl-label">任务目标</label>
        <el-input
          class="intent-textarea"
          v-model="userIntent"
          type="textarea"
          :autosize="{ minRows: 5, maxRows: 14 }"
          placeholder="描述你希望 ACG 生成的任务图，例如：重点审查付款、验收、知识产权，并输出依据和修改建议"
        />
      </div>
      <div class="ctrl-row ctrl-options">
        <div class="planning-mode">
          <span class="ctrl-label">规划模式</span>
          <el-radio-group v-model="planningMode" size="small">
            <el-radio-button label="template">模板升格</el-radio-button>
            <el-radio-button label="planner">智能规划</el-radio-button>
            <el-radio-button label="dynamic">强制动态</el-radio-button>
          </el-radio-group>
          <el-tag size="small" type="success" effect="plain">{{ planningModeHint }}</el-tag>
          <span class="ctrl-label">思考强度</span>
          <el-radio-group v-model="thinkingMode" size="small">
            <el-radio-button label="disabled">快速</el-radio-button>
            <el-radio-button label="standard">标准</el-radio-button>
            <el-radio-button label="deep">深度</el-radio-button>
          </el-radio-group>
        </div>
        <el-checkbox v-model="faultEnabled">注入故障演示自愈</el-checkbox>
        <el-select v-if="faultEnabled" v-model="faultStep" size="small" style="width: 180px">
          <el-option v-for="s in faultStepOptions" :key="s" :label="s" :value="s" />
        </el-select>
        <el-select v-if="faultEnabled" v-model="faultType" size="small" style="width: 150px">
          <el-option label="模型超时" value="timeout" />
          <el-option label="Agent 崩溃" value="crash" />
          <el-option label="证据为空" value="empty_evidence" />
        </el-select>
        <el-button type="primary" :loading="isSubmitting" @click="startRun">启动 ACG 引擎</el-button>
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
      v-if="activeRunId && (progressTracker.progress.value?.phase === 'review' || progressTracker.progress.value?.status === 'waiting_review')"
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

    <div v-else class="ui-surface ui-surface--pad placeholder">
      <el-icon class="ph-icon" :class="{ restoring: isAcgLoading }"><Cpu /></el-icon>
      <p>{{ placeholderMessage }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch, type DeepReadonly } from 'vue'
import axios from 'axios'
import { ChatDotRound, CopyDocument, Cpu, Delete, Document, Monitor, UploadFilled } from '@element-plus/icons-vue'
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

const WORKFLOW_ID = 'legal_contract_review_v1'
const TEMPLATE_FAULT_STEPS = ['parse_contract', 'classify_clauses', 'risk_detect', 'legal_evidence_match', 'suggestion_generate', 'human_review', 'report_generate']
const DYNAMIC_FAULT_STEPS = ['contract_parse', 'clause_classify', 'risk_detect', 'legal_evidence_match', 'revision_suggest', 'human_review', 'report_generate']

const contractText = ref(`甲方：星河科技有限公司。乙方：知弈软件工作室。甲方委托乙方开发客户关系管理 CRM 系统，乙方负责需求梳理、原型设计、系统开发、测试部署和上线支持。

项目总价为人民币 80 万元。甲方在合同签署后 5 个工作日内支付 30%，系统上线后一次性支付剩余 70%。合同未明确阶段性验收、缺陷修复期、发票开具条件和上线失败后的付款处理方式。

乙方应在 60 日内完成交付。验收标准为“系统无重大问题即视为验收通过”，甲方收到交付物后 5 日内未提出书面异议的，也视为验收通过。合同未列明功能清单、性能指标、测试用例、整改次数和最终确认流程。

项目源代码、接口文档、数据库设计、UI 设计稿及相关成果归甲乙双方共同所有。乙方可在后续项目中复用通用模块，涉及第三方开源组件的授权合规由双方另行协商。

任一方逾期履行义务，应按合同总价每日万分之五支付违约金。合同未明确延期交付、质量缺陷、数据泄露、逾期付款、知识产权侵权和保密违约的责任边界及赔偿上限。

双方应对项目资料、客户数据和商业信息承担保密义务，但合同未约定保密期限、数据删除、日志留存、权限控制和安全事件通知机制。争议解决条款仅写明“双方友好协商，协商不成另行处理”。`)
const userIntent = ref(`请以 ACG 多智能体协作方式审查这份软件开发合同，强制生成差异化任务图，并完整执行合同文本解析、条款分类、风险识别、证据/依据匹配、修改建议生成、人工审核要点提取和最终 Markdown 审查报告生成。

重点审查付款条款、验收标准、知识产权归属、开源组件合规、违约责任、保密义务、数据安全、交付范围和争议解决。请尽量并行分析付款、验收、知识产权、违约责任和数据安全五类风险，再汇聚为统一风险结论。

请用低熵通信方式组织上下文：解析节点只投递合同类型、主体、范围、付款、验收、知识产权和争议解决字段；条款分类节点只投递 clauses；风险识别节点只投递 risks、risk_level、risk_score；证据匹配节点只投递 evidences、citations；修改建议节点只投递 revision_suggestions、manual_review_focus。

最终报告必须包含合同基本信息、条款分类摘要、高中低风险清单、每个风险点的条款位置、风险原因、可能后果、证据依据、修改建议、人工复核关注点和签署前处理结论。`)
const planningMode = ref<'template' | 'planner' | 'dynamic'>('dynamic')
// 快速模式是可验收的默认路径；深度推理由用户显式选择，不能和进度展示绑定。
const thinkingMode = ref<ThinkingMode>('disabled')
const faultEnabled = ref(false)
const faultStep = ref('risk_detect')
const faultType = ref<'timeout' | 'crash' | 'empty_evidence'>('timeout')
const faultStepOptions = computed(() =>
  planningMode.value === 'dynamic' ? DYNAMIC_FAULT_STEPS : TEMPLATE_FAULT_STEPS
)

watch(planningMode, () => {
  if (!faultStepOptions.value.includes(faultStep.value)) faultStep.value = 'risk_detect'
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
const loadedRunId = ref('')
const contractFileInput = ref<HTMLInputElement | null>(null)
const uploadDragging = ref(false)
const selectedContractFile = ref<{
  name: string
  size: number
  textLength: number
  extractedText: string
} | null>(null)

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
const activeRunReference = computed(() => workflowRunsStore.getReference(activeRunId.value))

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
const planningModeHint = computed(() => {
  if (planningMode.value === 'dynamic') return '按输入意图生成差异化 ACG'
  if (planningMode.value === 'planner') return '命中模板则复用，未命中自动生成'
  return '线性工作流升格为 ACG'
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
  (value) => {
    if (value) scheduleTopologyRefresh(value)
  }
)

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

const openInConsole = () => {
  if (!activeRunId.value) return
  void router.push({ path: '/agentos-console', query: { runId: activeRunId.value } })
}

const openLinkedChat = () => {
  const conversationId = activeRunReference.value?.conversationId
  if (!conversationId || !activeRunId.value) return
  void router.push({ path: '/chat', query: { workspace: 'agent', contextId: conversationId, runId: activeRunId.value } })
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
      contractText: contractText.value,
      userIntent: intentText,
      planningMode: planningMode.value,
      thinkingMode: thinkingMode.value
    }
    if (planningMode.value !== 'template') input.usePlanner = true
    if (planningMode.value === 'dynamic') input.forceDynamicPlanning = true
    if (faultEnabled.value) {
      input.faultInjection = { step_id: faultStep.value, fault_type: faultType.value, max_triggers: 1 }
    }
    const clientRequestId = createClientRequestId()
    const res = await workflowApi.startWorkflowAsync({
      title: intentText,
      domain: 'legal',
      intent: 'contract_review_acg',
      workflowId: WORKFLOW_ID,
      input,
      clientRequestId
    }, { signal: submitController.signal })
    activeRunId.value = res.run.runId
    workflowRunsStore.register({
      runId: res.run.runId,
      taskId: res.task.taskId,
      workflowId: res.run.workflowId || WORKFLOW_ID,
      source: 'acg',
      status: res.run.status,
      phase: res.run.lifecyclePhase
    })
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

const placeholderMessage = computed(() => {
  if (isSubmitting.value) return '正在创建 ACG 运行...'
  if (progressTracker.syncError.value === '该运行记录不存在或当前账户无权访问') {
    return progressTracker.syncError.value
  }
  if (progressTracker.progress.value && !acgView.value) {
    const phase = progressTracker.progress.value.phase
    if (phase === 'understanding' || phase === 'planning') return '任务正在规划，ACG 拓扑将在构建后显示。'
    if (phase === 'graph_building') return '正在构建 ACG 拓扑...'
    return isAcgLoading.value ? '正在加载 ACG 拓扑与审查数据...' : '等待 ACG 数据刷新...'
  }
  return '启动一个 ACG 引擎工作流，观察动态拓扑、Token 节省率、数据血缘与故障自愈。'
})

onBeforeUnmount(() => {
  submitController?.abort()
  clearTopologyTimer()
  topologyGeneration += 1
  topologyController?.abort()
})
</script>

<style scoped>
.acg-view { display: flex; flex-direction: column; gap: var(--space-lg); }
.hero-left { display: flex; align-items: center; gap: var(--space-md); }
.ui-hero h1 { margin: 0; font-size: 20px; font-weight: 800; color: var(--text-primary); }
.hero-sub { margin: 2px 0 0; font-size: 12px; color: var(--text-secondary); }
.hero-right { display: flex; gap: 8px; align-items: center; justify-content: flex-end; flex-wrap: wrap; }
.run-context { display: flex; align-items: center; gap: 6px; }
.run-id {
  display: inline-flex; align-items: center; gap: 6px; min-width: 0;
  padding: 5px 8px; border: 1px solid var(--border-light); border-radius: 6px;
  background: var(--bg-input); color: var(--text-secondary); font-size: 10px;
}
.run-id code { color: var(--text-primary); font-size: 11px; white-space: nowrap; }

.control-bar { display: flex; flex-direction: column; gap: var(--space-md); }
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
.ctrl-options { flex-direction: row; align-items: center; gap: var(--space-md); flex-wrap: wrap; }
.planning-mode { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.contract-textarea :deep(.el-textarea__inner),
.intent-textarea :deep(.el-textarea__inner) {
  line-height: 1.72;
  font-size: 14px;
  padding: 12px 14px;
  resize: vertical;
}
.contract-textarea :deep(.el-textarea__inner) { min-height: 132px !important; }
.intent-textarea :deep(.el-textarea__inner) { min-height: 132px !important; }

.contract-file-input { display: none; }
.contract-upload {
  min-height: 52px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border: 1px dashed var(--border-light);
  border-radius: 8px;
  background: color-mix(in srgb, var(--bg-input) 72%, transparent);
  transition: border-color 0.16s ease, background-color 0.16s ease;
}
.contract-upload.dragging {
  border-color: var(--primary-color);
  background: var(--primary-fade);
}
.contract-upload.populated { border-style: solid; }
.contract-upload.loading { opacity: 0.72; }
.contract-upload__icon {
  width: 32px;
  height: 32px;
  flex: 0 0 32px;
  display: inline-grid;
  place-items: center;
  border-radius: 7px;
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
.contract-upload__copy strong { color: var(--text-primary); font-size: 12px; font-weight: 700; }
.contract-upload__copy small { color: var(--text-secondary); font-size: 11px; }
.contract-upload__actions { flex: 0 0 auto; display: inline-flex; align-items: center; gap: 6px; }

.acg-grid { display: grid; grid-template-columns: minmax(0, 1fr) 380px; gap: var(--space-lg); align-items: stretch; min-width: 0; }
.grid-main { display: flex; flex-direction: column; gap: var(--space-lg); min-width: 0; }
.grid-side { display: flex; flex-direction: column; gap: var(--space-lg); min-width: 0; min-height: 0; }
.grid-side :deep(.acg-provenance) { flex: 1 1 auto; min-height: 0; }

.schedule-strip { padding: var(--space-md); }
.schedule-strip h4 { margin: 0 0 var(--space-sm); font-size: 13px; font-weight: 700; color: var(--text-primary); }
.batch-row { display: flex; gap: var(--space-md); flex-wrap: wrap; }
.batch { display: flex; align-items: center; gap: 4px; padding: 4px 8px; background: var(--bg-input); border-radius: var(--radius-md); }
.batch-idx { font-size: 11px; color: var(--text-secondary); font-weight: 600; margin-right: 4px; }
.batch-node { font-size: 11px; padding: 2px 8px; background: var(--primary-fade); color: var(--primary-color); border-radius: 10px; font-family: monospace; }

.placeholder { display: flex; flex-direction: column; align-items: center; gap: var(--space-md); padding: 48px; text-align: center; color: var(--text-secondary); }
.ph-icon { font-size: 40px; color: var(--primary-color); opacity: .5; }
.ph-icon.restoring { animation: restore-pulse 1s ease-in-out infinite alternate; }

@keyframes restore-pulse {
  to { opacity: 1; }
}

@media (max-width: 1160px) {
  .acg-grid { grid-template-columns: minmax(0, 1fr); }
}

@media (max-width: 720px) {
  .ui-hero { flex-wrap: wrap; align-items: flex-start; }
  .hero-left { width: 100%; }
  .hero-right { justify-content: flex-start; width: 100%; }
  .run-context { width: 100%; flex-wrap: wrap; }
  .run-id { max-width: 100%; }
  .run-id code { overflow: hidden; text-overflow: ellipsis; }
  .contract-upload { align-items: flex-start; flex-wrap: wrap; }
  .contract-upload__copy { width: calc(100% - 42px); }
  .contract-upload__actions { width: 100%; padding-left: 42px; }
}
</style>
