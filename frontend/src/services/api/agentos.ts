import axios from 'axios'

export const agentosRequest = axios.create({
  baseURL: '/ai',
  timeout: 240000,
  headers: {
    'Content-Type': 'application/json'
  }
})

agentosRequest.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
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

export interface PageResponse<T> {
  items: T[]
  total: number
  page?: number
  pageSize?: number
}

export interface WorkflowStep {
  stepId: string
  name: string
  agentName: string
  capability?: string
  status: StepStatus
  input?: Record<string, any>
  outputSpec?: Record<string, any>
  resolvedInput?: Record<string, any>
  output?: Record<string, any>
  error?: string
  retryCount?: number
  attempt?: number
  maxRetries?: number
  timeout?: number
  priority?: number
  reviewRequired?: boolean
  durationMs?: number
  startedAt?: string
  completedAt?: string
}

export interface Checkpoint {
  checkpointId: string
  runId: string
  stepId: string
  stateSnapshot: Record<string, any>
  outputSnapshot: Record<string, any>
  canResume: boolean
  createdAt?: string
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
  runtimeEngine?: string
  implementationId?: string
  status: WorkflowStatus
  currentStepId?: string
  reviewMode: string
  input: Record<string, any>
  output: Record<string, any>
  steps: WorkflowStep[]
  checkpoints: Checkpoint[]
  trace: TraceEvent[]
  error?: string
  recoveryCount?: number
  completedStepIds?: string[]
  activeStepIds?: string[]
  provenance?: Record<string, any>
  executionState?: Record<string, any>
  createdAt?: string
  updatedAt?: string
}

export interface WorkflowTraceExport {
  runId: string
  taskId: string
  workflowId: string
  domain: string
  status: WorkflowStatus
  eventCount: number
  events: TraceEvent[]
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

export type ReviewDecision = 'approved' | 'rejected' | 'need_more_info' | 'rerun' | 'cancelled'

export interface ReviewRequest {
  stepId: string
  decision: ReviewDecision
  reviewer?: string
  comment?: string
}

export interface ReviewRecord {
  reviewId: string
  runId: string
  stepId: string
  decision: ReviewDecision
  reviewer: string
  comment?: string
  traceEventId?: string
  createdAt?: string
}

export interface WorkflowMetric {
  totalRuns: number
  completedRuns: number
  failedRuns: number
  cancelledRuns: number
  waitingReviewRuns: number
  retryingRuns: number
  completionRate: number
  failureRate: number
  recoverySuccessRate: number
  averageRecoveryCount: number
  averageTraceEvents: number
  reviewCount: number
  statusBreakdown: Record<string, number>
}

export interface EvaluationRun {
  evaluationId: string
  domain?: string
  workflowId?: string
  source?: string
  metrics: WorkflowMetric
  createdAt?: string
}

export interface WorkflowRunQuery {
  status?: WorkflowStatus | ''
  domain?: string
  workflowId?: string
  source?: string
  page?: number
  pageSize?: number
}

// ===== ACG 动态群体智能引擎可视化视图类型 =====

export interface AcgNode {
  nodeId: string
  nodeType: 'step' | 'agent' | 'skill' | 'memory' | 'evidence' | 'control'
  name?: string
  description?: string
  goal?: string
  agentName?: string
  capability?: string
  controlType?: string
  metadata?: Record<string, any>
}

export interface AcgEdge {
  edgeId: string
  sourceId: string
  targetId: string
  edgeType: 'dependency' | 'communication' | 'control_flow' | 'execution' | 'write' | 'read' | 'support'
  condition?: string
  metadata?: Record<string, any>
}

export interface AcgBlueprint {
  graphId: string
  taskId?: string
  objective?: string
  complexityLevel?: string
  nodes: AcgNode[]
  edges: AcgEdge[]
  metadata?: Record<string, any>
}

export interface ProvenanceProduction {
  eventId: string
  producerStepId: string
  checksum?: string
  fieldNames?: string[]
  tokenSize?: number
  runId?: string
  taskId?: string
  agentName?: string
  attempt?: number
  previousHash?: string
  eventHash?: string
  createdAt?: string
  evidenceRefs?: string[]
}

export interface ProvenanceConsumption {
  eventId: string
  consumerStepId: string
  producerStepIds: string[]
  runId?: string
  taskId?: string
  consumerAgentName?: string
  attempt?: number
  producerEventIds?: string[]
  consumedFields?: string[]
  fieldsByProducer?: Record<string, string[]>
  tokensDelivered?: number
  tokensAvailable?: number
  savingRatio?: number
  contractStatus?: string
  checksum?: string
  previousHash?: string
  eventHash?: string
  createdAt?: string
}

export interface RuntimeInteraction {
  interactionId: string
  eventId: string
  runId?: string
  taskId?: string
  edgeIds: string[]
  producerStepIds: string[]
  consumerStepId: string
  producerAgentNames: string[]
  consumerAgentName: string
  fieldsByProducer: Record<string, string[]>
  tokensDelivered: number
  tokensAvailable: number
  savingRatio: number
  evidenceRefs: string[]
  contractStatus: string
  checksum?: string
  previousHash?: string
  eventHash?: string
  createdAt?: string
}

export interface AcgStepState {
  stepId: string
  status: StepStatus
  agentName: string
  attempt: number
  retryCount: number
}

export interface AcgLowEntropyMetrics {
  averageSavingRatio: number
  effectiveSavingRatio: number
  tokensAvailable: number
  tokensDelivered: number
  tokensSaved: number
  recoveryCount: number
  interactionCount: number
  contractViolationCount: number
  integrityStatus: string
}

export interface AcgDeliverable {
  stepId: string
  name: string
  status: string
  output: Record<string, any>
}

export interface AcgView {
  runId: string
  status: WorkflowStatus
  engine: string
  acgBlueprint: AcgBlueprint | null
  completedStepIds: string[]
  activeStepIds: string[]
  stepStates: AcgStepState[]
  provenance: {
    schemaVersion?: number
    productions: ProvenanceProduction[]
    consumptions: ProvenanceConsumption[]
    interactions: RuntimeInteraction[]
    integrityStatus?: string
  }
  interactions: RuntimeInteraction[]
  contractViolations: TraceEvent[]
  recoveryTrace: TraceEvent[]
  scheduleTrace: TraceEvent[]
  deliverables: AcgDeliverable[]
  finalReport: string | null
  lowEntropyMetrics: AcgLowEntropyMetrics
}

const normalizeAcgView = (view: AcgView): AcgView => ({
  ...view,
  completedStepIds: Array.isArray(view.completedStepIds) ? view.completedStepIds : [],
  activeStepIds: Array.isArray(view.activeStepIds) ? view.activeStepIds : [],
  stepStates: Array.isArray(view.stepStates) ? view.stepStates : [],
  provenance: {
    schemaVersion: view.provenance?.schemaVersion,
    productions: Array.isArray(view.provenance?.productions) ? view.provenance.productions : [],
    consumptions: Array.isArray(view.provenance?.consumptions) ? view.provenance.consumptions : [],
    interactions: Array.isArray(view.provenance?.interactions) ? view.provenance.interactions : [],
    integrityStatus: view.provenance?.integrityStatus
  },
  interactions: Array.isArray(view.interactions) ? view.interactions : [],
  contractViolations: Array.isArray(view.contractViolations) ? view.contractViolations : [],
  recoveryTrace: Array.isArray(view.recoveryTrace) ? view.recoveryTrace : [],
  scheduleTrace: Array.isArray(view.scheduleTrace) ? view.scheduleTrace : [],
  deliverables: Array.isArray(view.deliverables) ? view.deliverables : [],
  finalReport: typeof view.finalReport === 'string' ? view.finalReport : null,
  lowEntropyMetrics: {
    averageSavingRatio: 0,
    effectiveSavingRatio: 0,
    tokensAvailable: 0,
    tokensDelivered: 0,
    tokensSaved: 0,
    recoveryCount: 0,
    interactionCount: 0,
    contractViolationCount: 0,
    integrityStatus: 'valid',
    ...(view.lowEntropyMetrics || {})
  }
})

export const agentosApi = {
  async listWorkflowRuns(params: WorkflowRunQuery = {}): Promise<PageResponse<WorkflowRun>> {
    const response = await agentosRequest.get<PageResponse<WorkflowRun>>('/core/workflows/runs', { params })
    return response.data
  },

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
  },

  async listWorkflowCheckpoints(runId: string): Promise<PageResponse<Checkpoint> & { runId: string }> {
    const response = await agentosRequest.get<PageResponse<Checkpoint> & { runId: string }>(`/core/workflows/runs/${runId}/checkpoints`)
    return response.data
  },

  async getWorkflowTrace(runId: string): Promise<WorkflowTraceExport> {
    const response = await agentosRequest.get<WorkflowTraceExport>(`/core/workflows/runs/${runId}/trace`)
    return response.data
  },

  async exportWorkflowTraceMarkdown(runId: string): Promise<string> {
    const response = await agentosRequest.get<string>(`/core/workflows/runs/${runId}/trace`, {
      params: { format: 'markdown' },
      responseType: 'text'
    })
    return response.data
  },

  async listWorkflowReviews(runId: string): Promise<PageResponse<ReviewRecord> & { runId: string }> {
    const response = await agentosRequest.get<PageResponse<ReviewRecord> & { runId: string }>(`/core/workflows/runs/${runId}/reviews`)
    return response.data
  },

  async applyWorkflowReview(runId: string, payload: ReviewRequest): Promise<WorkflowRun> {
    const response = await agentosRequest.post<WorkflowRun>(`/core/workflows/runs/${runId}/reviews`, payload)
    return response.data
  },

  async resumeWorkflow(runId: string, checkpointId: string): Promise<WorkflowRun> {
    const response = await agentosRequest.post<WorkflowRun>(`/core/workflows/runs/${runId}/resume`, { checkpointId })
    return response.data
  },

  async getWorkflowMetrics(params: Pick<WorkflowRunQuery, 'status' | 'domain' | 'workflowId' | 'source'> = {}): Promise<EvaluationRun> {
    const response = await agentosRequest.get<EvaluationRun>('/core/workflows/metrics', { params })
    return response.data
  },

  async getAcgView(runId: string): Promise<AcgView> {
    const response = await agentosRequest.get<AcgView>(`/core/workflows/runs/${runId}/acg`)
    return normalizeAcgView(response.data)
  }
}
