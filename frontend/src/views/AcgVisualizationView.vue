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
        <div v-if="acgView" class="run-context">
          <span class="run-id" :title="acgView.runId">
            <span>RUN</span>
            <code>{{ acgView.runId }}</code>
          </span>
          <el-button circle size="small" title="复制 Run ID" aria-label="复制 Run ID" @click="copyRunId">
            <el-icon><CopyDocument /></el-icon>
          </el-button>
          <el-button size="small" title="在 AgentOS 运维页查看" @click="openInConsole">
            <el-icon><Monitor /></el-icon>
            运维查看
          </el-button>
        </div>
        <el-tag v-if="acgView" :type="statusTagType" effect="dark">{{ statusLabel }}</el-tag>
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
          <el-tag size="small" type="info" effect="plain">深度思考</el-tag>
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
        <el-button type="primary" :loading="loading.start" @click="startRun">启动 ACG 引擎</el-button>
      </div>
    </section>

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
      <el-icon class="ph-icon" :class="{ restoring: loading.restore }"><Cpu /></el-icon>
      <p>{{ loading.restore ? '正在恢复 ACG 运行上下文...' : '启动一个 ACG 引擎工作流，观察动态拓扑、Token 节省率、数据血缘与故障自愈。' }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { CopyDocument, Cpu, Monitor } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import {
  workflowApi,
  type AcgDeliverable,
  type AcgView,
  type WorkflowRun,
  type WorkflowStatus
} from '@/services/api/workflow'
import AcgTopologyGraph from '@/components/agentos/AcgTopologyGraph.vue'
import AcgLowEntropyMetrics from '@/components/agentos/AcgLowEntropyMetrics.vue'
import AcgProvenancePanel from '@/components/agentos/AcgProvenancePanel.vue'
import AcgDeliverables from '@/components/agentos/AcgDeliverables.vue'
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
const thinkingMode = 'deep'
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
const loading = reactive({ start: false, restore: false })
const route = useRoute()
const router = useRouter()
const loadedRunId = ref('')

const STABLE: WorkflowStatus[] = ['completed', 'failed', 'cancelled', 'waiting_review']

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    completed: '已完成', failed: '失败', running: '执行中',
    waiting_review: '待审核', cancelled: '已取消', retrying: '重试中', planning: '规划中', pending: '待启动'
  }
  return acgView.value ? (map[acgView.value.status] || acgView.value.status) : ''
})
const statusTagType = computed(() => {
  const s = acgView.value?.status
  if (s === 'completed') return 'success'
  if (s === 'failed') return 'danger'
  if (s === 'waiting_review') return 'warning'
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

const restoreRun = async (runId: string) => {
  if (!runId || (loadedRunId.value === runId && acgView.value)) return
  loading.restore = true
  try {
    const [run, view] = await Promise.all([
      workflowApi.getRun(runId),
      workflowApi.getAcgView(runId)
    ])
    acgView.value = hydrateAcgView(view, run)
    loadedRunId.value = runId
  } catch (err: any) {
    acgView.value = null
    loadedRunId.value = ''
    ElMessage.error(`恢复运行失败：${err?.message || err}`)
  } finally {
    loading.restore = false
  }
}

watch(
  () => route.query.runId,
  (value) => {
    if (typeof value === 'string' && value.trim()) void restoreRun(value.trim())
  },
  { immediate: true }
)

const copyRunId = async () => {
  if (!acgView.value) return
  try {
    await navigator.clipboard.writeText(acgView.value.runId)
    ElMessage.success('Run ID 已复制')
  } catch {
    ElMessage.warning('浏览器未授权剪贴板，请直接选择 Run ID')
  }
}

const openInConsole = () => {
  if (!acgView.value) return
  void router.push({ path: '/agentos-console', query: { runId: acgView.value.runId } })
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
  if (!contractText.value.trim()) {
    ElMessage.warning('请输入合同文本')
    return
  }
  loading.start = true
  acgView.value = null
  try {
    const intentText = userIntent.value.trim() || '审查合同风险并生成报告'
    const input: Record<string, any> = {
      contractText: contractText.value,
      userIntent: intentText,
      planningMode: planningMode.value,
      thinkingMode
    }
    if (planningMode.value !== 'template') input.usePlanner = true
    if (planningMode.value === 'dynamic') input.forceDynamicPlanning = true
    if (faultEnabled.value) {
      input.faultInjection = { step_id: faultStep.value, fault_type: faultType.value, max_triggers: 1 }
    }
    const res = await workflowApi.startWorkflow({
      title: intentText,
      domain: 'legal',
      intent: 'contract_review_acg',
      workflowId: WORKFLOW_ID,
      input
    })
    const latest = await pollUntilStable(res.run.runId)
    const view = await workflowApi.getAcgView(res.run.runId)
    acgView.value = hydrateAcgView(view, latest)
    loadedRunId.value = res.run.runId
    await router.replace({ query: { ...route.query, runId: res.run.runId } })
    ElMessage.success('ACG 引擎执行完成')
  } catch (err: any) {
    ElMessage.error(`启动失败：${err?.message || err}`)
  } finally {
    loading.start = false
  }
}

const pollUntilStable = async (runId: string): Promise<WorkflowRun> => {
  let latest = await workflowApi.getRun(runId)
  let tries = 0
  while (!STABLE.includes(latest.status) && tries < 6) {
    await new Promise((r) => window.setTimeout(r, 800))
    latest = await workflowApi.getRun(runId)
    tries += 1
  }
  return latest
}
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
}
</style>
