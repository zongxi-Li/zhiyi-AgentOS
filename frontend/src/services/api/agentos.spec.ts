import { beforeEach, describe, expect, it, vi } from 'vitest'
import { agentosApi, agentosRequest, WorkflowApiContractError } from './agentos'

describe('AgentOS async workflow API', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('starts through the Java gateway with clientRequestId and AbortSignal', async () => {
    const signal = new AbortController().signal
    const response = {
      accepted: true,
      task: { taskId: 'task_1', status: 'pending' },
      run: { runId: 'run_1', status: 'pending' }
    }
    const post = vi.spyOn(agentosRequest, 'post').mockResolvedValue({ data: response } as never)

    await expect(agentosApi.startWorkflowAsync({
      title: '合同审查',
      domain: 'legal',
      intent: 'contract_review',
      clientRequestId: 'request_1'
    }, { signal })).resolves.toEqual(response)

    expect(post).toHaveBeenCalledWith('/core/workflows/start-async', expect.objectContaining({
      clientRequestId: 'request_1'
    }), { signal })
  })

  it('rejects a successful-looking response that has no runId', async () => {
    vi.spyOn(agentosRequest, 'post').mockResolvedValue({
      data: { accepted: true, task: { taskId: 'task_1', status: 'pending' }, run: { status: 'pending' } }
    } as never)

    await expect(agentosApi.startWorkflowAsync({
      title: '合同审查', domain: 'legal', intent: 'review', clientRequestId: 'request_1'
    })).rejects.toBeInstanceOf(WorkflowApiContractError)
  })

  it('queries progress through Java, preserves null percent, and forwards cancellation', async () => {
    const signal = new AbortController().signal
    const payload = { runId: 'run/1', phase: 'planning', percent: null }
    const get = vi.spyOn(agentosRequest, 'get').mockResolvedValue({ data: payload } as never)

    const result = await agentosApi.getWorkflowProgress('run/1', { signal })

    expect(result.percent).toBeNull()
    expect(get).toHaveBeenCalledWith('/core/workflows/runs/run%2F1/progress', { signal })
  })

  it.each([409, 404, 503])('does not swallow HTTP %s', async (status) => {
    const error = { response: { status } }
    vi.spyOn(agentosRequest, 'get').mockRejectedValue(error)
    await expect(agentosApi.getWorkflowProgress('run_1')).rejects.toBe(error)
  })
})
