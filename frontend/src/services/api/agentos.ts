import axios from 'axios'

const agentosRequest = axios.create({
  baseURL: '/ai',
  timeout: 240000,
  headers: {
    'Content-Type': 'application/json'
  }
})

agentosRequest.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  const userId = localStorage.getItem('userId')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  if (userId) {
    config.headers['X-User-Id'] = userId
  }
  return config
})

export type WorkflowStatus =
  | 'pending'
  | 'planning'
  | 'running'
  | 'waiting_review'
  | 'retrying'
  | 'failed'
  | 'completed'
  | 'cancelled'

export type StepStatus =
  | 'pending'
  | 'running'
  | 'waiting_review'
  | 'retrying'
  | 'failed'
  | 'completed'
  | 'cancelled'

export interface AgentTask {
  taskId: string
  title: string
  domain: string
  intent: string
  input: Record<string, any>
  securityLevel: string
  priority: string
  status: WorkflowStatus
  recommendedWorkflow?: string
  createdAt?: string
  updatedAt?: string
}

export interface WorkflowStep {
  stepId: string
  name: string
  agentName: string
  capability?: string
  status: StepStatus
  input?: Record<string, any>
  output?: Record<string, any>
  error?: string
  reviewRequired?: boolean
}

export interface TraceEvent {
  eventId: string
  runId: string
  stepId?: string
  agentName?: string
  eventType: string
  observation?: string
  payload?: Record<string, any>
  durationMs?: number
  createdAt?: string
}

export interface WorkflowRun {
  runId: string
  taskId: string
  workflowId: string
  domain: string
  status: WorkflowStatus
  currentStepId?: string
  reviewMode: string
  input: Record<string, any>
  output: Record<string, any>
  steps: WorkflowStep[]
  trace: TraceEvent[]
  error?: string
}

export interface WorkflowStartRequest {
  title: string
  domain: string
  intent: string
  input?: Record<string, any>
  securityLevel?: string
  priority?: string
  workflowId?: string
  reviewMode?: string
}

export interface WorkflowStartResponse {
  task: AgentTask
  run: WorkflowRun
  source?: string
}

export interface ChatWorkflowUpgradeRequest {
  text: string
  title?: string
  domain?: string
  intent?: string
  workflowId?: string
  reviewMode?: string
  roleId?: string
  contextId?: string
  context?: Array<{ role: string; content: string }>
  input?: Record<string, any>
}

export const agentosApi = {
  async startWorkflow(payload: WorkflowStartRequest): Promise<WorkflowStartResponse> {
    const response = await agentosRequest.post<WorkflowStartResponse>('/core/workflows/start', payload)
    return response.data
  },

  async upgradeChatToWorkflow(payload: ChatWorkflowUpgradeRequest): Promise<WorkflowStartResponse> {
    const response = await agentosRequest.post<WorkflowStartResponse>('/chat/workflows/upgrade', payload)
    return response.data
  },

  async getWorkflowRun(runId: string): Promise<WorkflowRun> {
    const response = await agentosRequest.get<WorkflowRun>(`/core/workflows/runs/${runId}`)
    return response.data
  }
}
