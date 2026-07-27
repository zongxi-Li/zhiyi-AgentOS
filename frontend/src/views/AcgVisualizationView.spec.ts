import { flushPromises, shallowMount, type VueWrapper } from '@vue/test-utils'
import { createMemoryHistory, createRouter, type Router } from 'vue-router'
import { createPinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import AcgVisualizationView from './AcgVisualizationView.vue'
import WorkflowProgressBar from '@/components/agentos/WorkflowProgressBar.vue'
import { workflowApi, type AcgView, type WorkflowProgress, type WorkflowRun } from '@/services/api/workflow'
import { DEFAULT_ACG_PROMPT_PRESET } from '@/test/fixtures/acgPromptPresets'
import { fileApi } from '@/services/api/file'

vi.mock('@/services/api/workflow', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/api/workflow')>()
  return {
    ...actual,
    workflowApi: {
      ...actual.workflowApi,
      startWorkflow: vi.fn(),
      startWorkflowAsync: vi.fn(),
      getWorkflowProgress: vi.fn(),
      getRun: vi.fn(),
      getAcgView: vi.fn()
    }
  }
})

vi.mock('@/services/api/file', () => ({
  fileApi: {
    uploadTaskMaterial: vi.fn(),
    deleteTaskMaterial: vi.fn(),
    extractDocumentText: vi.fn()
  }
}))

const makeProgress = (overrides: Partial<WorkflowProgress> = {}): WorkflowProgress => ({
  taskId: 'task_1', runId: 'run_1', workflowId: 'workflow_1', status: 'running',
  phase: 'planning', message: '正在规划任务', percent: null,
  totalSteps: 0, pendingSteps: 0, runningSteps: 0, waitingReviewSteps: 0,
  retryingSteps: 0, failedSteps: 0, completedSteps: 0, cancelledSteps: 0,
  currentStepId: null, activeStepIds: [], recoveryCount: 0,
  startedAt: '2026-07-22T00:00:00Z', updatedAt: '2026-07-22T00:00:01Z',
  progress: 0, percentage: 0,
  ...overrides
})

const makeRun = (): WorkflowRun => ({
  runId: 'run_1', taskId: 'task_1', workflowId: 'workflow_1', domain: 'legal',
  status: 'running', reviewMode: 'manual', input: {}, output: {}, steps: [], checkpoints: [], trace: []
})

const makeAcg = (): AcgView => ({
  runId: 'run_1', status: 'running', engine: 'acg', acgBlueprint: null,
  completedStepIds: [], activeStepIds: [], stepStates: [],
  provenance: { productions: [], consumptions: [], interactions: [] }, interactions: [],
  contractViolations: [], recoveryTrace: [], scheduleTrace: [], deliverables: [], finalReport: null,
  lowEntropyMetrics: {
    averageSavingRatio: 0, effectiveSavingRatio: 0, tokensAvailable: 0, tokensDelivered: 0,
    tokensSaved: 0, recoveryCount: 0, interactionCount: 0, contractViolationCount: 0,
    integrityStatus: 'valid'
  }
})

const buttonStub = {
  emits: ['click'],
  template: '<button type="button" @click="$emit(\'click\')"><slot /></button>'
}

const mountPage = async (query = ''): Promise<{ wrapper: VueWrapper; router: Router }> => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/agentos/acg', component: { template: '<div />' } },
      { path: '/agentos-console', component: { template: '<div />' } }
    ]
  })
  await router.push(`/agentos/acg${query}`)
  await router.isReady()
  const wrapper = shallowMount(AcgVisualizationView, {
    global: {
      plugins: [createPinia(), router],
      stubs: {
        'el-button': buttonStub,
        'el-input': true,
        'el-icon': true,
        'el-tag': { template: '<span class="el-tag-stub"><slot /></span>' },
        'el-radio-group': true,
        'el-radio-button': true,
        'el-checkbox': true,
        'el-checkbox-group': true,
        'el-checkbox-button': true,
        'el-select': true,
        'el-option': true
      }
    }
  })
  await flushPromises()
  return { wrapper, router }
}

const clickStart = async (wrapper: VueWrapper) => {
  const button = wrapper.findAll('button').find((item) => item.text().includes('启动 ACG'))
  if (!button) throw new Error('start button not found')
  await button.trigger('click')
  await flushPromises()
}

describe('AcgVisualizationView async progress loop', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.mocked(workflowApi.startWorkflowAsync).mockResolvedValue({
      accepted: true,
      task: { taskId: 'task_1', status: 'pending' },
      run: { runId: 'run_1', status: 'pending', lifecyclePhase: 'understanding' }
    })
    vi.mocked(workflowApi.getWorkflowProgress).mockResolvedValue(makeProgress())
    vi.mocked(workflowApi.getRun).mockResolvedValue(makeRun())
    vi.mocked(workflowApi.getAcgView).mockResolvedValue(makeAcg())
    vi.mocked(fileApi.uploadTaskMaterial).mockResolvedValue({
      materialId: 'mat_123', state: 'ready', originalFilename: '合同.txt', mediaType: 'text/plain',
      size: 18, sha256: 'source_hash', extractedTextSha256: 'text_hash', extractedText: '上传后的合同正文',
      textLength: 8, extraction: { method: 'utf-8', ocrUsed: false, pages: 0 }
    })
    vi.mocked(fileApi.deleteTaskMaterial).mockResolvedValue()
  })

  it('uploads a selected contract through the task material API and shows the ready state', async () => {
    const { wrapper } = await mountPage()
    const input = wrapper.find('input[type="file"]')
    const file = new File(['上传后的合同正文'], '合同.txt', { type: 'text/plain' })
    Object.defineProperty(input.element, 'files', { configurable: true, value: [file] })

    await input.trigger('change')
    await flushPromises()

    expect(fileApi.uploadTaskMaterial).toHaveBeenCalledWith(file, expect.any(Function))
    expect(wrapper.find('.contract-upload__copy').text()).toContain('合同.txt')
    expect(wrapper.find('.contract-upload__copy').text()).toContain('已提取')
    wrapper.unmount()
  })

  it('surfaces the backend 422 message without discarding the existing draft text', async () => {
    vi.mocked(fileApi.uploadTaskMaterial).mockRejectedValueOnce({
      response: { status: 422, data: { error: 'MATERIAL_FILE_REQUIRED', message: '上传请求缺少 file 字段' } }
    })
    const { wrapper } = await mountPage()
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', {
      configurable: true,
      value: [new File(['probe'], '合同.txt', { type: 'text/plain' })]
    })

    await input.trigger('change')
    await flushPromises()

    expect(wrapper.find('.contract-upload__error').text()).toBe('上传请求缺少 file 字段')
    wrapper.unmount()
  })

  afterEach(() => {
    vi.clearAllMocks()
    vi.useRealTimers()
  })

  it('uses the fixed ACG engine header and routes to history operations', async () => {
    const { wrapper, router } = await mountPage()

    expect(wrapper.find('.hero-left h3').text()).toBe('ACG 动态群体智能引擎')
    expect(wrapper.find('.hero-run-chip').text()).toContain('RUN')
    expect(wrapper.find('.hero-engine').text()).toBe('engine: acg')

    await wrapper.find('.hero-operations').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/agentos-console')
    expect(router.currentRoute.value.query.source).toBe('acg')
    wrapper.unmount()
  })

  it('uses async start, writes runId to query, and begins progress immediately', async () => {
    const { wrapper, router } = await mountPage()
    await clickStart(wrapper)

    expect(workflowApi.startWorkflowAsync).toHaveBeenCalledOnce()
    expect(workflowApi.startWorkflowAsync).toHaveBeenCalledWith(expect.objectContaining({
      title: DEFAULT_ACG_PROMPT_PRESET.taskName,
      reviewMode: 'human_in_loop',
      input: expect.objectContaining({
        source: 'acg',
        contractText: DEFAULT_ACG_PROMPT_PRESET.contractText,
        userIntent: DEFAULT_ACG_PROMPT_PRESET.userIntent
      })
    }), expect.any(Object))
    expect(workflowApi.startWorkflow).not.toHaveBeenCalled()
    expect(vi.mocked(workflowApi.startWorkflowAsync).mock.calls[0][0].clientRequestId).toBeTruthy()
    expect(workflowApi.getWorkflowProgress).toHaveBeenCalledWith('run_1', expect.objectContaining({ signal: expect.any(AbortSignal) }))
    expect(router.currentRoute.value.query.runId).toBe('run_1')
    expect(workflowApi.getAcgView).not.toHaveBeenCalled()
    expect(wrapper.find('.input-panel-expandable').attributes('style') || '').not.toContain('display: none')
    await vi.advanceTimersByTimeAsync(1400)
    expect(wrapper.find('.input-summary').exists()).toBe(false)
    await vi.advanceTimersByTimeAsync(450)
    expect(wrapper.find('.input-summary').exists()).toBe(true)
    expect(wrapper.find('.input-panel-expandable').attributes('style')).toContain('display: none')
    expect(wrapper.findComponent(WorkflowProgressBar).exists()).toBe(true)
    expect(wrapper.find('.ctrl-options').exists()).toBe(true)
    expect(wrapper.findAll('.input-panel-toggle')).toHaveLength(1)
    expect(wrapper.find('.input-panel-toggle').attributes('aria-expanded')).toBe('false')
    await wrapper.find('.input-panel-toggle').trigger('click')
    expect(wrapper.find('.input-panel-expandable').attributes('style')).not.toContain('display: none')
    expect(wrapper.find('.input-panel-toggle').attributes('aria-expanded')).toBe('true')
    wrapper.unmount()
  })

  it('keeps the compact header context visible before a Run starts', async () => {
    const { wrapper } = await mountPage()

    expect(wrapper.find('.hero-left').text()).toContain('ACG 动态群体智能引擎')
    expect(wrapper.find('.hero-run-chip').text()).toContain('RUN—')
    expect(wrapper.find('.hero-right').text()).toContain('准备中')
    expect(wrapper.find('.hero-engine').text()).toBe('engine: acg')
    expect(wrapper.find('.hero-icon-action').attributes('disabled')).toBeDefined()
    expect(wrapper.find('.task-brief').text()).toBe('ACG 动态智能体长程任务')
    expect(wrapper.find('#acg-task-name').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('测试预设')
    wrapper.unmount()
  })

  it('restores a query runId without starting a duplicate workflow', async () => {
    const { wrapper } = await mountPage('?runId=run_1')

    expect(workflowApi.startWorkflowAsync).not.toHaveBeenCalled()
    expect(workflowApi.getWorkflowProgress).toHaveBeenCalledWith('run_1', expect.any(Object))
    expect(workflowApi.getAcgView).not.toHaveBeenCalled()
    expect(wrapper.find('.input-summary').exists()).toBe(true)
    expect(wrapper.find('.ctrl-options').exists()).toBe(true)
    wrapper.unmount()
  })

  it('does not load topology in planning but loads it when execution begins', async () => {
    vi.mocked(workflowApi.getWorkflowProgress).mockResolvedValue(makeProgress({
      phase: 'executing', percent: 25, totalSteps: 4, completedSteps: 1, updatedAt: '2026-07-22T00:00:02Z'
    }))
    const { wrapper } = await mountPage('?runId=run_1')
    await vi.advanceTimersByTimeAsync(0)
    await flushPromises()

    expect(workflowApi.getAcgView).toHaveBeenCalledOnce()
    expect(workflowApi.getRun).toHaveBeenCalledOnce()
    wrapper.unmount()
  })

  it('refreshes Run Detail and ACG immediately when graphVersion changes', async () => {
    vi.mocked(workflowApi.getWorkflowProgress)
      .mockResolvedValueOnce(makeProgress({
        phase: 'executing', graphVersion: 1, percent: 25, totalSteps: 4, completedSteps: 1
      }))
      .mockResolvedValueOnce(makeProgress({
        phase: 'executing', graphVersion: 2, dynamicStepCount: 2,
        percent: 16.67, totalSteps: 6, completedSteps: 1, updatedAt: '2026-07-22T00:00:02Z'
      }))
    const { wrapper } = await mountPage('?runId=run_1')
    await vi.advanceTimersByTimeAsync(0)
    await flushPromises()
    expect(workflowApi.getAcgView).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(2000)
    await flushPromises()
    expect(workflowApi.getAcgView).toHaveBeenCalledTimes(2)
    expect(workflowApi.getRun).toHaveBeenCalledTimes(2)
    wrapper.unmount()
  })

  it('forces final ACG loading for completed and keeps review polling nonterminal', async () => {
    vi.mocked(workflowApi.getWorkflowProgress).mockResolvedValueOnce(makeProgress({
      phase: 'review', status: 'waiting_review', percent: 75
    })).mockResolvedValueOnce(makeProgress({
      phase: 'completed', status: 'completed', percent: 100, completedSteps: 4, totalSteps: 4
    }))
    const { wrapper } = await mountPage('?runId=run_1')

    await vi.advanceTimersByTimeAsync(2000)
    await flushPromises()
    expect(workflowApi.getWorkflowProgress).toHaveBeenCalledTimes(2)
    expect(workflowApi.getAcgView).toHaveBeenCalled()
    wrapper.unmount()
  })

  it('shows the review panel when the canonical Run is waiting even if progress is briefly stale', async () => {
    vi.mocked(workflowApi.getWorkflowProgress).mockResolvedValue(makeProgress({
      phase: 'executing', status: 'running', percent: 75, waitingReviewSteps: 0,
      currentStepId: 'human_review', activeStepIds: ['human_review']
    }))
    vi.mocked(workflowApi.getRun).mockResolvedValue({
      ...makeRun(), status: 'waiting_review',
      steps: [{ stepId: 'human_review', name: '人工审核', agentName: 'reviewer', status: 'waiting_review' }]
    })
    const { wrapper } = await mountPage('?runId=run_1')
    await vi.advanceTimersByTimeAsync(0)
    await flushPromises()

    expect(wrapper.findComponent({ name: 'WorkflowReviewPanel' }).exists()).toBe(true)
    wrapper.unmount()
  })

  it('shows idempotency conflict separately from a workflow failure', async () => {
    vi.mocked(workflowApi.startWorkflowAsync).mockRejectedValue({
      isAxiosError: true,
      response: { status: 409 }
    })
    const { wrapper } = await mountPage()
    await clickStart(wrapper)

    expect(wrapper.text()).toContain('相同请求标识已用于不同参数')
    expect(wrapper.text()).not.toContain('工作流执行失败')
    wrapper.unmount()
  })

  it('aborts an outstanding start request when the page unmounts', async () => {
    let signal: AbortSignal | undefined
    vi.mocked(workflowApi.startWorkflowAsync).mockImplementation((_payload, options) => {
      signal = options.signal
      return new Promise(() => undefined)
    })
    const { wrapper } = await mountPage()
    const startPromise = clickStart(wrapper)
    await Promise.resolve()
    wrapper.unmount()
    expect(signal?.aborted).toBe(true)
    void startPromise
  })

  it('completes the controlled T0-T6 lifecycle without polling full ACG every two seconds', async () => {
    vi.mocked(workflowApi.getWorkflowProgress)
      .mockResolvedValueOnce(makeProgress({ phase: 'understanding', message: '理解任务' }))
      .mockResolvedValueOnce(makeProgress({ phase: 'planning', message: '规划任务', updatedAt: '2026-07-22T00:00:02Z' }))
      .mockResolvedValueOnce(makeProgress({ phase: 'graph_building', message: '构建 ACG', updatedAt: '2026-07-22T00:00:03Z' }))
      .mockResolvedValueOnce(makeProgress({
        phase: 'executing', message: '执行节点', percent: 50, totalSteps: 4, completedSteps: 2,
        updatedAt: '2026-07-22T00:00:04Z'
      }))
      .mockResolvedValueOnce(makeProgress({
        phase: 'completed', status: 'completed', message: '执行完成', percent: 100,
        totalSteps: 4, completedSteps: 4, updatedAt: '2026-07-22T00:00:05Z'
      }))
    const { wrapper } = await mountPage()
    await clickStart(wrapper)

    for (let second = 2; second <= 8; second += 2) {
      await vi.advanceTimersByTimeAsync(2000)
      await flushPromises()
    }

    expect(workflowApi.getWorkflowProgress).toHaveBeenCalledTimes(5)
    expect(workflowApi.getAcgView).toHaveBeenCalledTimes(2)
    expect(workflowApi.getRun).toHaveBeenCalledTimes(2)
    expect(vi.mocked(workflowApi.getAcgView).mock.calls.every(([runId]) => runId === 'run_1')).toBe(true)
    wrapper.unmount()
  })
})
