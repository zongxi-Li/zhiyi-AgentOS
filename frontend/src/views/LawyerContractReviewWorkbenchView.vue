<!-- 律师合同审查工作台页面 — 核心业务页面，支持角色与模板切换，合同审查全工作流管理 -->
<template>
  <main class="contract-review-workbench ui-shell" :style="roleThemeStyle">
    <header class="workbench-header ui-hero">
      <div class="workbench-title">
        <span class="ui-icon-badge">
          <el-icon><DocumentChecked /></el-icon>
        </span>
        <div>
          <span class="ui-hero__eyebrow">Zhiyi AgentOS Workbench</span>
          <h1 class="ui-hero__title">{{ modeConfig.title }}</h1>
          <p class="ui-hero__subtitle">{{ modeConfig.subtitle }}</p>
        </div>
      </div>
      <div class="header-controls">
        <button class="template-trigger" type="button" :disabled="loading.start" @click="openTemplateSwitcher">
          <span>当前模板</span>
          <strong>{{ activeRole.name }} / {{ activeTemplate.name }}</strong>
          <i>{{ modeConfig.executionMode === 'backend' ? '可运行' : '预览' }}</i>
        </button>
        <button class="header-action" type="button" :disabled="!selectedRun || loading.detail" @click="refreshSelectedRun">
          <el-icon><Refresh /></el-icon>
          <span>刷新</span>
        </button>
      </div>
    </header>

    <Teleport to="body">
      <div v-if="templateSwitcherOpen" class="template-switcher-layer" :style="roleThemeStyle" @click.self="closeTemplateSwitcher">
        <section class="template-switcher liquid-glass" role="dialog" aria-modal="true" aria-label="选择角色与模板">
          <header class="switcher-head">
            <div>
              <span>角色模板</span>
              <h2>选择角色与模板</h2>
            </div>
            <button type="button" aria-label="关闭模板选择器" @click="closeTemplateSwitcher">×</button>
          </header>

          <div class="switcher-body">
            <nav class="switcher-roles" aria-label="角色">
              <button
                v-for="role in roleTemplateGroups"
                :key="role.id"
                type="button"
                :class="{ active: pendingRoleId === role.id }"
                :style="roleButtonStyle(role)"
                @click="selectPendingRole(role.id)"
              >
                <span>{{ role.short }}</span>
                <strong>{{ role.name }}</strong>
                <small>{{ role.summary }}</small>
                <em>{{ role.tone }}</em>
              </button>
            </nav>

            <section class="switcher-templates">
              <button
                v-for="template in pendingRole.templates"
                :key="template.key"
                type="button"
                :class="{ active: pendingTemplateKey === template.key }"
                @click="pendingTemplateKey = template.key"
              >
                <div>
                  <strong>{{ template.name }}</strong>
                  <small>{{ template.brief }}</small>
                </div>
                <span>{{ template.key === activeTemplateKey ? '当前' : template.executionMode === 'backend' ? '后端' : '预览' }}</span>
              </button>
            </section>

            <aside class="switcher-preview">
              <span class="preview-label">{{ pendingRole.name }}</span>
              <h3>{{ pendingTemplate.name }}</h3>
              <p>{{ pendingTemplate.subtitle }}</p>
              <div class="preview-meta">
                <span>{{ pendingTemplate.runtimeLabel }}</span>
                <span>{{ pendingTemplate.workflowId }}</span>
              </div>
              <div class="preview-flow">
                <span
                  v-for="step in pendingTemplate.steps"
                  :key="step.id"
                  :style="taskToneStyle(step)"
                >
                  {{ step.title }}
                </span>
              </div>
              <dl>
                <div>
                  <dt>输出</dt>
                  <dd>{{ pendingTemplate.outputTitle }}</dd>
                </div>
              <div>
                <dt>Workflow</dt>
                <dd>{{ pendingTemplate.workflowLabel }}</dd>
              </div>
              <div>
                <dt>Domain</dt>
                <dd>{{ pendingTemplate.domain }}</dd>
              </div>
              </dl>
            </aside>
          </div>

          <footer class="switcher-footer">
            <span v-if="selectedRun && runTemplateLabel">当前运行结果来自：{{ runTemplateLabel }}</span>
            <span v-else>切换模板不会自动启动 Workflow；未接入后端的模板会生成前端预览。</span>
            <div>
              <button type="button" class="ghost-button" @click="closeTemplateSwitcher">取消</button>
              <button type="button" class="apply-button" @click="applyPendingTemplate">
                <el-icon><Check /></el-icon>
                <span>确定</span>
              </button>
            </div>
          </footer>
        </section>
      </div>
    </Teleport>

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
            <button type="button" class="primary-action" :disabled="loading.start || !contractText.trim()" @click="startActiveWorkflow">
              <el-icon><Check /></el-icon>
              <span>{{ loading.start ? '启动中...' : modeConfig.actionLabel }}</span>
            </button>
            <span v-if="selectedRun">当前运行：{{ selectedRun.runId }}</span>
            <span v-if="selectedRun && runTemplateLabel && runTemplateLabel !== currentTemplateLabel">结果来自：{{ runTemplateLabel }}</span>
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

          <template v-if="isContractReviewResult">
            <ContractRiskPanel :risks="contractArtifacts.risks" />
            <ContractEvidencePanel :evidences="contractArtifacts.evidences" />
            <ContractReportPreview :report-markdown="contractArtifacts.reportMarkdown" />
          </template>

          <section v-else class="preflight-output-panel ui-surface ui-surface--pad">
            <div class="section-head">
              <div class="section-title">
                <el-icon><DocumentChecked /></el-icon>
                <h3>{{ modeConfig.outputTitle }}</h3>
              </div>
              <span>{{ modeConfig.runtimeLabel }}</span>
            </div>
            <div class="preflight-output-grid">
              <article v-for="item in preflightOutputs" :key="item.id" class="preflight-output-item">
                <strong>{{ item.title }}</strong>
                <p>{{ item.path }}</p>
              </article>
            </div>
          </section>
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
              <article
                v-for="step in preflightSteps"
                :key="step.id"
                class="preflight-step"
                :style="taskToneStyle(step)"
              >
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
            <div v-if="activePreviewResult" class="frontend-preview-result">
              <div class="preview-result-head">
                <strong>{{ activePreviewResult.roleName }} / {{ activePreviewResult.templateName }}</strong>
                <span>{{ activePreviewResult.createdAt }}</span>
              </div>
              <p>{{ activePreviewResult.summary }}</p>
              <div class="preview-result-grid">
                <article v-for="item in activePreviewResult.panels" :key="item.id">
                  <strong>{{ item.title }}</strong>
                  <p>{{ item.content }}</p>
                </article>
              </div>
            </div>
            <div v-else class="preflight-output-grid">
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
            <div v-for="item in artifactPathRows" :key="item.id">
              <dt>{{ item.id }}</dt>
              <dd>{{ item.path }}</dd>
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
              <span>{{ modeConfig.runtimeLabel }}</span>
            </div>
            <dl>
              <div>
                <dt>workflow</dt>
                <dd>{{ selectedWorkflowId }}</dd>
              </div>
              <div>
                <dt>domain</dt>
                <dd>{{ modeConfig.domain }}</dd>
              </div>
              <div>
                <dt>intent</dt>
                <dd>{{ modeConfig.intent }}</dd>
              </div>
              <div>
                <dt>role</dt>
                <dd>{{ activeRole.name }}</dd>
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
import { roleTemplateGroups, taskToneStyles, workbenchTemplateAliases, type FrontendPreviewResult, type RoleTemplateGroup, type TemplateStep } from '@/config/agentWorkbench'
import { extractContractReviewArtifacts } from '@/utils/agentos/contractReviewArtifactExtractor'

const route = useRoute()
const router = useRouter()

const templateMap = new Map(roleTemplateGroups.flatMap(role => role.templates.map(template => [template.key, template])))

const resolveTemplateAlias = (templateKey: string) => {
  return workbenchTemplateAliases[templateKey] || templateKey
}

const findRoleByTemplate = (templateKey: string) => {
  const resolvedTemplateKey = resolveTemplateAlias(templateKey)
  return roleTemplateGroups.find(role => role.templates.some(template => template.key === resolvedTemplateKey)) || roleTemplateGroups[0]
}

const resolveRouteSelection = () => {
  const routeMode = typeof route.query.mode === 'string' ? route.query.mode : ''
  const routeTemplate = resolveTemplateAlias(typeof route.query.template === 'string' ? route.query.template : routeMode)
  const routeRole = typeof route.query.role === 'string' ? route.query.role : ''
  const role = roleTemplateGroups.find(item => item.id === routeRole) || findRoleByTemplate(routeTemplate)
  const template = role.templates.find(item => item.key === routeTemplate) || role.templates[0]
  return { roleId: role.id, templateKey: template.key }
}

const initialSelection = resolveRouteSelection()
const activeRoleId = ref(initialSelection.roleId)
const activeTemplateKey = ref(initialSelection.templateKey)
const pendingRoleId = ref(activeRoleId.value)
const pendingTemplateKey = ref(activeTemplateKey.value)
const templateSwitcherOpen = ref(false)
const runTemplateLabel = ref('')

const activeRole = computed(() => roleTemplateGroups.find(role => role.id === activeRoleId.value) || roleTemplateGroups[0])
const activeTemplate = computed(() => templateMap.get(activeTemplateKey.value) || activeRole.value.templates[0])
const modeConfig = computed(() => activeTemplate.value)
const currentTemplateLabel = computed(() => `${activeRole.value.name} / ${activeTemplate.value.name}`)
const roleThemeStyle = computed(() => ({
  '--role-accent': activeRole.value.accent,
  '--role-accent-soft': activeRole.value.softAccent
}))
const roleButtonStyle = (role: RoleTemplateGroup) => ({
  '--role-local-accent': role.accent,
  '--role-local-soft': role.softAccent
})
const taskToneStyle = (step: TemplateStep) => {
  const tone = taskToneStyles[step.tone || 'blue']
  return {
    '--task-accent': tone.accent,
    '--task-soft': tone.soft
  }
}
const pendingRole = computed(() => roleTemplateGroups.find(role => role.id === pendingRoleId.value) || roleTemplateGroups[0])
const pendingTemplate = computed(() => {
  return pendingRole.value.templates.find(template => template.key === pendingTemplateKey.value) || pendingRole.value.templates[0]
})

const workflowOptions = computed(() => [
  { label: modeConfig.value.workflowLabel, value: modeConfig.value.workflowId }
])

const preflightSteps = computed(() => modeConfig.value.steps)
const preflightOutputs = computed(() => modeConfig.value.outputs)
const preflightMonitors = computed(() => {
  if (!activePreviewResult.value) return modeConfig.value.monitors
  return [
    { id: 'preview', title: '前端预览', value: '已生成' },
    { id: 'workflow', title: 'Workflow ID', value: activePreviewResult.value.workflowId },
    { id: 'backend', title: '后端状态', value: modeConfig.value.runtimeLabel }
  ]
})

const contractText = ref(modeConfig.value.defaultText)
const selectedWorkflowId = ref(workflowOptions.value[0].value)
const selectedRun = ref<WorkflowRun | null>(null)
const frontendPreviewResult = ref<FrontendPreviewResult | null>(null)
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
const isContractReviewResult = computed(() => modeConfig.value.resultView === 'contract-review')
const activePreviewResult = computed(() => {
  return frontendPreviewResult.value?.templateKey === activeTemplateKey.value ? frontendPreviewResult.value : null
})
const artifactPathRows = computed(() => {
  if (selectedRun.value && isContractReviewResult.value) {
    return [
      { id: 'risks', path: contractArtifacts.value.paths.risks },
      { id: 'evidences', path: contractArtifacts.value.paths.evidences },
      { id: 'report', path: contractArtifacts.value.paths.reportMarkdown }
    ]
  }
  return modeConfig.value.outputs.map(item => ({ id: item.id, path: item.path }))
})

const syncTemplateDefaults = () => {
  selectedWorkflowId.value = workflowOptions.value[0].value
  contractText.value = modeConfig.value.defaultText
  errorMessage.value = ''
  selectedRun.value = null
  frontendPreviewResult.value = null
  traceEvents.value = []
  checkpoints.value = []
  reviews.value = []
  metrics.value = null
}

const openTemplateSwitcher = () => {
  pendingRoleId.value = activeRoleId.value
  pendingTemplateKey.value = activeTemplateKey.value
  templateSwitcherOpen.value = true
}

const closeTemplateSwitcher = () => {
  templateSwitcherOpen.value = false
}

const selectPendingRole = (roleId: string) => {
  const role = roleTemplateGroups.find(item => item.id === roleId)
  if (!role) return
  pendingRoleId.value = role.id
  pendingTemplateKey.value = role.templates[0].key
}

const applyPendingTemplate = () => {
  activeRoleId.value = pendingRole.value.id
  activeTemplateKey.value = pendingTemplate.value.key
  syncTemplateDefaults()
  templateSwitcherOpen.value = false
  void router.replace({
    path: route.path,
    query: {
      role: activeRoleId.value,
      template: activeTemplateKey.value
    }
  })
}

watch(
  () => [route.query.role, route.query.template, route.query.mode],
  () => {
    const nextSelection = resolveRouteSelection()
    if (nextSelection.roleId !== activeRoleId.value || nextSelection.templateKey !== activeTemplateKey.value) {
      activeRoleId.value = nextSelection.roleId
      activeTemplateKey.value = nextSelection.templateKey
      syncTemplateDefaults()
      if (!templateSwitcherOpen.value) {
        pendingRoleId.value = nextSelection.roleId
        pendingTemplateKey.value = nextSelection.templateKey
      }
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

const buildWorkflowInput = () => {
  const text = contractText.value.trim()
  const input: Record<string, string> = {
    source: 'workbench',
    role: activeRoleId.value,
    template: activeTemplateKey.value,
    text,
    chatText: text,
    [modeConfig.value.inputKey]: text
  }

  modeConfig.value.inputAliases.forEach(alias => {
    input[alias] = text
  })

  return input
}

const buildFrontendPreviewResult = (): FrontendPreviewResult => {
  const text = contractText.value.trim()
  const compactText = text.length > 90 ? `${text.slice(0, 90)}...` : text
  return {
    templateKey: activeTemplateKey.value,
    roleName: activeRole.value.name,
    templateName: modeConfig.value.name,
    workflowId: selectedWorkflowId.value,
    createdAt: new Date().toLocaleString('zh-CN', { hour12: false }),
    summary: `${modeConfig.value.runtimeLabel}。当前已根据输入生成前端预览，后端接入后会复用同一份 role/template/workflow 配置。`,
    panels: modeConfig.value.outputs.map((output, index) => {
      const step = modeConfig.value.steps[index % modeConfig.value.steps.length]
      return {
        id: output.id,
        title: output.title,
        content: `${step.title} -> ${output.path}。输入摘要：${compactText || '等待输入'}`
      }
    })
  }
}

const startPreviewWorkflow = async () => {
  frontendPreviewResult.value = buildFrontendPreviewResult()
  selectedRun.value = null
  traceEvents.value = []
  checkpoints.value = []
  reviews.value = []
  metrics.value = null
  runTemplateLabel.value = currentTemplateLabel.value
  ElMessage.info(`${modeConfig.value.name}已生成前端预览，后端 Workflow 待接入`)
}

const startBackendWorkflow = async () => {
  if (!contractText.value.trim()) return
  frontendPreviewResult.value = null
  const response = await workflowApi.startWorkflow({
    title: modeConfig.value.title,
    domain: modeConfig.value.domain,
    intent: modeConfig.value.intent,
    workflowId: selectedWorkflowId.value,
    reviewMode: modeConfig.value.reviewMode,
    input: buildWorkflowInput()
  })
  selectedRun.value = response.run
  runTemplateLabel.value = currentTemplateLabel.value
  await refreshRunUntilStable(response.run.runId)
  if (selectedRun.value?.status === 'waiting_review') {
    ElMessage.success(modeConfig.value.successMessage)
  }
}

const startActiveWorkflow = async () => {
  if (!contractText.value.trim()) return
  loading.start = true
  errorMessage.value = ''
  try {
    if (modeConfig.value.executionMode === 'backend') {
      await startBackendWorkflow()
    } else {
      await startPreviewWorkflow()
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
    domain: modeConfig.value.domain,
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
  --role-accent: var(--primary-color);
  --role-accent-soft: var(--primary-fade);
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

.template-trigger {
  min-height: 42px;
  min-width: 220px;
  padding: 7px 8px 7px 12px;
  border: 1px solid rgba(255, 255, 255, 0.48);
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.72), rgba(242, 248, 246, 0.42)),
    rgba(255, 255, 255, 0.36);
  color: var(--text-primary);
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 2px 10px;
  align-items: center;
  text-align: left;
  cursor: pointer;
  box-shadow: 0 12px 30px rgba(47, 90, 82, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.58);
  backdrop-filter: blur(18px) saturate(1.28);
  -webkit-backdrop-filter: blur(18px) saturate(1.28);
  transition: var(--transition);
}

.template-trigger:hover:not(:disabled) {
  border-color: var(--primary-line);
  box-shadow: 0 16px 34px rgba(47, 90, 82, 0.16), inset 0 1px 0 rgba(255, 255, 255, 0.68);
  transform: translateY(-1px);
}

.template-trigger:disabled {
  cursor: not-allowed;
  opacity: 0.74;
}

.template-trigger span,
.template-trigger i {
  color: var(--text-secondary);
  font-size: 11px;
  font-style: normal;
  font-weight: 800;
}

.template-trigger strong {
  min-width: 0;
  color: var(--role-accent);
  font-size: 13px;
  overflow-wrap: anywhere;
}

.template-trigger i {
  grid-row: 1 / 3;
  grid-column: 2;
  padding: 5px 8px;
  border-radius: 999px;
  background: var(--role-accent-soft);
  color: var(--role-accent);
}

.template-switcher-layer {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(30, 44, 42, 0.22);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.template-switcher {
  width: min(960px, calc(100vw - 48px));
  height: min(720px, calc(100vh - 48px));
  overflow: hidden;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
}

.liquid-glass {
  border: 1px solid rgba(255, 255, 255, 0.58);
  background:
    radial-gradient(circle at 16% 0%, rgba(255, 255, 255, 0.92), transparent 30%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(244, 250, 248, 0.76)),
    rgba(255, 255, 255, 0.74);
  box-shadow: 0 26px 80px rgba(27, 47, 45, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(22px) saturate(1.18);
  -webkit-backdrop-filter: blur(22px) saturate(1.18);
}

.switcher-head,
.switcher-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.switcher-head {
  flex: 0 0 auto;
  padding: 18px 20px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.42);
}

.switcher-head span,
.preview-label {
  color: var(--role-accent);
  font-size: 12px;
  font-weight: 900;
}

.switcher-head h2 {
  margin: 4px 0 0;
  color: var(--text-primary);
  font-size: 20px;
}

.switcher-head button {
  width: 34px;
  height: 34px;
  border: 1px solid rgba(255, 255, 255, 0.52);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.5);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 22px;
  line-height: 1;
}

.switcher-body {
  flex: 1 1 auto;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(240px, 0.88fr) minmax(270px, 1fr) minmax(280px, 1.05fr);
  gap: 14px;
  padding: 16px;
  overflow: hidden;
}

.switcher-roles,
.switcher-templates {
  height: 100%;
  min-height: 0;
  display: grid;
  align-content: start;
  gap: 10px;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 4px;
  scrollbar-gutter: stable;
}

.switcher-roles::-webkit-scrollbar,
.switcher-templates::-webkit-scrollbar,
.switcher-preview::-webkit-scrollbar {
  width: 6px;
}

.switcher-roles::-webkit-scrollbar-track,
.switcher-templates::-webkit-scrollbar-track,
.switcher-preview::-webkit-scrollbar-track {
  background: transparent;
}

.switcher-roles::-webkit-scrollbar-thumb,
.switcher-templates::-webkit-scrollbar-thumb,
.switcher-preview::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: rgba(63, 107, 99, 0.28);
}

.switcher-roles button,
.switcher-templates button,
.switcher-preview,
.ghost-button,
.apply-button {
  border: 1px solid rgba(255, 255, 255, 0.48);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.48);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.48);
}

.switcher-roles button,
.switcher-templates button {
  min-width: 0;
  padding: 12px;
  color: var(--text-primary);
  cursor: pointer;
  text-align: left;
  transition: var(--transition);
}

.switcher-roles button {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  gap: 4px 10px;
  align-items: start;
}

.switcher-roles button > span {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: var(--role-local-soft, var(--role-accent-soft));
  color: var(--role-local-accent, var(--role-accent));
  font-weight: 900;
}

.switcher-roles strong,
.switcher-roles small,
.switcher-roles em {
  min-width: 0;
  display: block;
  overflow-wrap: normal;
}

.switcher-roles strong {
  align-self: center;
}

.switcher-roles small {
  grid-column: 2;
  max-width: 100%;
}

.switcher-roles em {
  grid-column: 2;
  color: var(--role-local-accent, var(--role-accent));
  font-size: 11px;
  font-style: normal;
  font-weight: 800;
}

.switcher-roles small,
.switcher-templates small,
.switcher-preview p,
.switcher-preview dd,
.switcher-footer > span {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.switcher-roles button.active,
.switcher-templates button.active {
  border-color: var(--role-local-accent, var(--role-accent));
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 10px 26px rgba(47, 90, 82, 0.11), inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.switcher-templates button {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
}

.switcher-templates button > span {
  padding: 4px 7px;
  border-radius: 999px;
  background: var(--role-accent-soft);
  color: var(--role-accent);
  font-size: 11px;
  font-weight: 900;
}

.switcher-preview {
  min-height: 0;
  padding: 16px;
  overflow-y: auto;
  scrollbar-gutter: stable;
}

.switcher-preview h3 {
  margin-top: 8px;
  font-size: 19px;
}

.switcher-preview p {
  margin-top: 10px;
}

.preview-meta {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preview-meta span {
  min-width: 0;
  padding: 5px 8px;
  border-radius: 999px;
  background: var(--role-accent-soft);
  color: var(--role-accent);
  font-size: 11px;
  font-weight: 850;
  overflow-wrap: anywhere;
}

.preview-flow {
  margin-top: 16px;
  display: grid;
  gap: 8px;
}

.preview-flow span {
  padding: 9px 10px;
  border: 1px solid color-mix(in srgb, var(--task-accent, var(--role-accent)) 22%, transparent);
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.7), rgba(255, 255, 255, 0.46)),
    var(--task-soft, var(--role-accent-soft));
  color: var(--task-accent, var(--role-accent));
  font-size: 12px;
  font-weight: 800;
}

.switcher-preview dl {
  margin-top: 16px;
  display: grid;
  gap: 8px;
}

.switcher-preview dl > div {
  padding: 10px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.48);
}

.switcher-footer {
  flex: 0 0 auto;
  padding: 14px 16px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.42);
}

.switcher-footer > div {
  display: flex;
  gap: 10px;
  align-items: center;
}

.ghost-button,
.apply-button {
  min-height: 38px;
  padding: 0 14px;
  color: var(--text-primary);
  cursor: pointer;
  font-weight: 800;
  transition: var(--transition);
}

.apply-button {
  min-width: 112px;
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  border-color: transparent;
  background: linear-gradient(135deg, var(--role-accent), color-mix(in srgb, var(--role-accent) 78%, #111 22%));
  color: #fff;
  font-size: 14px;
  font-weight: 900;
  box-shadow: 0 14px 30px color-mix(in srgb, var(--role-accent) 34%, transparent), inset 0 1px 0 rgba(255, 255, 255, 0.24);
}

.apply-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 18px 36px color-mix(in srgb, var(--role-accent) 40%, transparent), inset 0 1px 0 rgba(255, 255, 255, 0.28);
}

.apply-button:active {
  transform: translateY(0);
  box-shadow: 0 8px 18px color-mix(in srgb, var(--role-accent) 28%, transparent), inset 0 1px 2px rgba(24, 39, 35, 0.18);
}

.apply-button:focus-visible {
  outline: 3px solid var(--role-accent-soft);
  outline-offset: 2px;
}

.apply-button :deep(.el-icon) {
  width: 17px;
  height: 17px;
  font-size: 17px;
}

.ghost-button {
  background: rgba(255, 255, 255, 0.48);
  color: var(--text-secondary);
}

.ghost-button:hover {
  border-color: var(--border-hover);
  background: rgba(255, 255, 255, 0.72);
  color: var(--text-primary);
}

:global(.template-switcher .apply-button) {
  min-width: 112px;
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  border-color: transparent;
  background: linear-gradient(135deg, var(--role-accent), color-mix(in srgb, var(--role-accent) 78%, #111 22%));
  color: #fff;
  font-size: 14px;
  font-weight: 900;
  box-shadow: 0 14px 30px color-mix(in srgb, var(--role-accent) 34%, transparent), inset 0 1px 0 rgba(255, 255, 255, 0.24);
}

:global(.template-switcher .apply-button:hover) {
  transform: translateY(-1px);
  box-shadow: 0 18px 36px color-mix(in srgb, var(--role-accent) 40%, transparent), inset 0 1px 0 rgba(255, 255, 255, 0.28);
}

:global(.template-switcher .apply-button .el-icon) {
  width: 17px;
  height: 17px;
  font-size: 17px;
}

:global(.template-switcher .ghost-button) {
  background: rgba(255, 255, 255, 0.48);
  color: var(--text-secondary);
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
  color: var(--role-accent);
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
  border-color: var(--role-accent);
  box-shadow: 0 0 0 3px var(--role-accent-soft);
}

select:focus {
  background: #fff;
  border-color: var(--role-accent);
  box-shadow: 0 0 0 3px var(--role-accent-soft);
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
  background: linear-gradient(135deg, var(--role-accent), color-mix(in srgb, var(--role-accent) 82%, #111 18%));
  color: #fff;
  font-size: 14px;
  font-weight: 750;
  letter-spacing: 0;
  box-shadow: 0 10px 22px color-mix(in srgb, var(--role-accent) 26%, transparent), inset 0 1px 0 rgba(255, 255, 255, 0.18);
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
  background: linear-gradient(135deg, color-mix(in srgb, var(--role-accent) 90%, #fff 10%), color-mix(in srgb, var(--role-accent) 78%, #111 22%));
  box-shadow: 0 14px 28px color-mix(in srgb, var(--role-accent) 30%, transparent), inset 0 1px 0 rgba(255, 255, 255, 0.2);
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
.preview-result-grid,
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
.preview-result-grid article,
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
  border-color: color-mix(in srgb, var(--task-accent, var(--role-accent)) 18%, var(--border-light));
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.68), rgba(255, 255, 255, 0.42)),
    var(--task-soft, var(--bg-panel));
}

.preflight-output-item,
.preview-result-grid article,
.monitor-slots article {
  display: grid;
  gap: 6px;
}

.preflight-step strong,
.preflight-output-item strong,
.preview-result-grid strong,
.monitor-slots strong {
  color: var(--text-primary);
  font-size: 13px;
  overflow-wrap: anywhere;
}

.preflight-step p,
.preflight-output-item p,
.preview-result-grid p,
.monitor-slots p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 12px;
  overflow-wrap: anywhere;
}

.frontend-preview-result {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  padding: 14px;
  border: 1px solid color-mix(in srgb, var(--role-accent) 18%, transparent);
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.72), rgba(255, 255, 255, 0.44)),
    var(--role-accent-soft);
}

.preview-result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.preview-result-head strong {
  color: var(--role-accent);
  font-size: 14px;
}

.preview-result-head span,
.frontend-preview-result > p {
  color: var(--text-secondary);
  font-size: 12px;
}

.preview-result-grid {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 4px;
  scrollbar-gutter: stable;
}

.preflight-step span {
  justify-self: start;
  padding: 3px 7px;
  border-radius: 999px;
  background: var(--task-soft, rgba(73, 107, 143, 0.1));
  color: var(--task-accent, var(--info));
  font-size: 11px;
  font-weight: 800;
}

.preflight-step strong {
  color: var(--task-accent, var(--text-primary));
}

.preflight-output-grid,
.preview-result-grid,
.monitor-slots {
  flex: 1 1 auto;
  max-height: clamp(220px, 34vh, 420px);
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 4px;
  scrollbar-gutter: stable;
}

.preflight-output-grid::-webkit-scrollbar,
.preview-result-grid::-webkit-scrollbar,
.monitor-slots::-webkit-scrollbar {
  width: 5px;
}

.preflight-output-grid::-webkit-scrollbar-track,
.preview-result-grid::-webkit-scrollbar-track,
.monitor-slots::-webkit-scrollbar-track {
  background: transparent;
}

.preflight-output-grid::-webkit-scrollbar-thumb,
.preview-result-grid::-webkit-scrollbar-thumb,
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
  .template-trigger {
    width: 100%;
  }

  .template-switcher-layer {
    align-items: end;
    padding: 12px;
  }

  .template-switcher {
    width: 100%;
    height: calc(100vh - 24px);
    border-radius: 12px 12px 8px 8px;
  }

  .switcher-head,
  .switcher-footer {
    align-items: stretch;
    flex-direction: column;
  }

  .switcher-body {
    min-height: 0;
    grid-template-columns: 1fr;
    overflow-y: auto;
    overflow-x: hidden;
  }

  .switcher-roles,
  .switcher-templates,
  .switcher-preview {
    height: auto;
    overflow: visible;
  }

  .switcher-footer > div {
    width: 100%;
  }

  .ghost-button,
  .apply-button {
    flex: 1;
  }

  .preflight-steps {
    grid-template-columns: 1fr;
  }
}
</style>

