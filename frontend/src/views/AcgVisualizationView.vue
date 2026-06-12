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
        <el-tag v-if="acgView" :type="statusTagType" effect="dark">{{ statusLabel }}</el-tag>
        <el-tag v-if="acgView" type="info" effect="plain">engine: {{ acgView.engine }}</el-tag>
      </div>
    </header>

    <!-- 控制台 -->
    <section class="ui-surface ui-surface--pad control-bar">
      <div class="ctrl-row">
        <label class="ctrl-label">合同文本</label>
        <el-input
          v-model="contractText"
          type="textarea"
          :rows="3"
          placeholder="输入合同文本，引擎将解析→分类→风险→证据→建议→报告"
        />
      </div>
      <div class="ctrl-row ctrl-options">
        <el-checkbox v-model="usePlanner">启用认知规划器（意图解析 + ACG 构建）</el-checkbox>
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
        <AcgTopologyGraph :blueprint="acgView.acgBlueprint" :completed-step-ids="acgView.completedStepIds" />
        <div class="schedule-strip ui-surface" v-if="scheduleBatches.length">
          <h4>就绪集调度轨迹（动态拓扑）</h4>
          <div class="batch-row">
            <div v-for="(b, i) in scheduleBatches" :key="i" class="batch">
              <span class="batch-idx">第{{ i + 1 }}轮</span>
              <span v-for="sid in b" :key="sid" class="batch-node">{{ sid }}</span>
            </div>
          </div>
        </div>
      </div>
      <div class="grid-side">
        <AcgLowEntropyMetrics :metrics="acgView.lowEntropyMetrics" />
        <AcgProvenancePanel
          :consumptions="acgView.provenance.consumptions"
          :recovery-trace="acgView.recoveryTrace"
        />
      </div>
    </div>

    <div v-else class="ui-surface ui-surface--pad placeholder">
      <el-icon class="ph-icon"><Cpu /></el-icon>
      <p>启动一个 ACG 引擎工作流，实时观察动态拓扑、Token 节省率、数据血缘与故障自愈。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { Cpu } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { workflowApi, type AcgView, type WorkflowStatus } from '@/services/api/workflow'
import AcgTopologyGraph from '@/components/agentos/AcgTopologyGraph.vue'
import AcgLowEntropyMetrics from '@/components/agentos/AcgLowEntropyMetrics.vue'
import AcgProvenancePanel from '@/components/agentos/AcgProvenancePanel.vue'

const WORKFLOW_ID = 'legal_contract_review_acg_v1'
const faultStepOptions = ['contract_parse', 'clause_classify', 'risk_detect', 'legal_evidence_match', 'revision_suggest', 'report_generate']

const contractText = ref('甲方应在交付后30日内付款，逾期按日万分之五支付违约金；本合同未尽事宜双方另行协商。')
const usePlanner = ref(false)
const faultEnabled = ref(false)
const faultStep = ref('risk_detect')
const faultType = ref<'timeout' | 'crash' | 'empty_evidence'>('timeout')

const acgView = ref<AcgView | null>(null)
const loading = reactive({ start: false })

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

// 从调度 trace 还原"每轮就绪集批次"，可视化并行调度
const scheduleBatches = computed<string[][]>(() => {
  const events = acgView.value?.scheduleTrace || []
  const seen = new Set<string>()
  const batches: string[][] = []
  for (const e of events) {
    const batch = (e.payload?.batch as string[]) || (e.stepId ? [e.stepId] : [])
    const key = batch.join(',')
    if (batch.length && !seen.has(key)) {
      seen.add(key)
      batches.push(batch)
    }
  }
  return batches
})

const startRun = async () => {
  if (!contractText.value.trim()) {
    ElMessage.warning('请输入合同文本')
    return
  }
  loading.start = true
  acgView.value = null
  try {
    const input: Record<string, any> = { contractText: contractText.value }
    if (usePlanner.value) input.usePlanner = true
    if (faultEnabled.value) {
      input.faultInjection = { step_id: faultStep.value, fault_type: faultType.value, max_triggers: 1 }
    }
    const res = await workflowApi.startWorkflow({
      title: '合同审查 ACG 演示',
      domain: 'legal',
      intent: 'contract_review_acg',
      workflowId: WORKFLOW_ID,
      input
    })
    await pollUntilStable(res.run.runId)
    acgView.value = await workflowApi.getAcgView(res.run.runId)
    ElMessage.success('ACG 引擎执行完成')
  } catch (err: any) {
    ElMessage.error(`启动失败：${err?.message || err}`)
  } finally {
    loading.start = false
  }
}

const pollUntilStable = async (runId: string) => {
  let latest = await workflowApi.getRun(runId)
  let tries = 0
  while (!STABLE.includes(latest.status) && tries < 6) {
    await new Promise((r) => window.setTimeout(r, 800))
    latest = await workflowApi.getRun(runId)
    tries += 1
  }
}
</script>

<style scoped>
.acg-view { display: flex; flex-direction: column; gap: var(--space-lg); }
.hero-left { display: flex; align-items: center; gap: var(--space-md); }
.ui-hero h1 { margin: 0; font-size: 20px; font-weight: 800; color: var(--text-primary); }
.hero-sub { margin: 2px 0 0; font-size: 12px; color: var(--text-secondary); }
.hero-right { display: flex; gap: 8px; align-items: center; }

.control-bar { display: flex; flex-direction: column; gap: var(--space-md); }
.ctrl-row { display: flex; flex-direction: column; gap: 6px; }
.ctrl-label { font-size: 12px; font-weight: 600; color: var(--text-secondary); }
.ctrl-options { flex-direction: row; align-items: center; gap: var(--space-md); flex-wrap: wrap; }

.acg-grid { display: grid; grid-template-columns: 1fr 380px; gap: var(--space-lg); align-items: start; }
.grid-main { display: flex; flex-direction: column; gap: var(--space-lg); }
.grid-side { display: flex; flex-direction: column; gap: var(--space-lg); }

.schedule-strip { padding: var(--space-md); }
.schedule-strip h4 { margin: 0 0 var(--space-sm); font-size: 13px; font-weight: 700; color: var(--text-primary); }
.batch-row { display: flex; gap: var(--space-md); flex-wrap: wrap; }
.batch { display: flex; align-items: center; gap: 4px; padding: 4px 8px; background: var(--bg-input); border-radius: var(--radius-md); }
.batch-idx { font-size: 11px; color: var(--text-secondary); font-weight: 600; margin-right: 4px; }
.batch-node { font-size: 11px; padding: 2px 8px; background: var(--primary-fade); color: var(--primary-color); border-radius: 10px; font-family: monospace; }

.placeholder { display: flex; flex-direction: column; align-items: center; gap: var(--space-md); padding: 48px; text-align: center; color: var(--text-secondary); }
.ph-icon { font-size: 40px; color: var(--primary-color); opacity: .5; }

@media (max-width: 1160px) {
  .acg-grid { grid-template-columns: 1fr; }
}
</style>
