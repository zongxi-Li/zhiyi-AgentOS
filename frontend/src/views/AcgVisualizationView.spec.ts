import { flushPromises, shallowMount, type VueWrapper } from '@vue/test-utils'
import { createMemoryHistory, createRouter, type Router } from 'vue-router'
import { createPinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import AcgVisualizationView from './AcgVisualizationView.vue'
import WorkflowProgressBar from '@/components/agentos/WorkflowProgressBar.vue'
import { workflowApi, type AcgView, type WorkflowProgress, type WorkflowRun } from '@/services/api/workflow'

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
    routes: [{ path: '/agentos/acg', component: { template: '<div />' } }]
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
  })

  afterEach(() => {
    vi.clearAllMocks()
    vi.useRealTimers()
  })

  it('uses async start, writes runId to query, and begins progress immediately', async () => {
    const { wrapper, router } = await mountPage()
    await clickStart(wrapper)

    expect(workflowApi.startWorkflowAsync).toHaveBeenCalledOnce()
    expect(workflowApi.startWorkflowAsync).toHaveBeenCalledWith(expect.objectContaining({
      reviewMode: 'human_in_loop',
      input: expect.objectContaining({ source: 'acg' })
    }), expect.any(Object))
    expect(workflowApi.startWorkflow).not.toHaveBeenCalled()
    expect(vi.mocked(workflowApi.startWorkflowAsync).mock.calls[0][0].clientRequestId).toBeTruthy()
    expect(workflowApi.getWorkflowProgress).toHaveBeenCalledWith('run_1', expect.objectContaining({ signal: expect.any(AbortSignal) }))
    expect(router.currentRoute.value.query.runId).toBe('run_1')
    expect(workflowApi.getAcgView).not.toHaveBeenCalled()
    expect(wrapper.find('.input-fields').attributes('style') || '').not.toContain('display: none')
    await vi.advanceTimersByTimeAsync(1400)
    expect(wrapper.find('.input-summary').exists()).toBe(true)
    expect(wrapper.find('.input-fields').attributes('style')).toContain('display: none')
    expect(wrapper.findComponent(WorkflowProgressBar).exists()).toBe(true)
    expect(wrapper.find('.ctrl-options').exists()).toBe(true)
    expect(wrapper.findAll('.input-panel-toggle')).toHaveLength(1)
    expect(wrapper.find('.input-panel-toggle').attributes('aria-expanded')).toBe('false')
    await wrapper.find('.input-panel-toggle').trigger('click')
    expect(wrapper.find('.input-fields').attributes('style')).not.toContain('display: none')
    expect(wrapper.find('.input-panel-toggle').attributes('aria-expanded')).toBe('true')
    wrapper.unmount()
  })

  it('keeps the compact header context visible before a Run starts', async () => {
    const { wrapper } = await mountPage()

    expect(wrapper.find('.hero-right').text()).toContain('RUN--')
    expect(wrapper.find('.hero-right').text()).toContain('准备中')
    expect(wrapper.find('.hero-right').text()).toContain('engine: acg')
    expect(wrapper.findAll('.hero-right button').every(button => button.attributes('disabled') !== undefined)).toBe(true)
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
