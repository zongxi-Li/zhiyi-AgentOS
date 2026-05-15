import {
  agentosApi,
  type Checkpoint,
  type EvaluationRun,
  type PageResponse,
  type ReviewRecord,
  type ReviewRequest,
  type ReviewDecision,
  type StepStatus,
  type TraceEvent,
  type WorkflowRun,
  type WorkflowRunQuery,
  type WorkflowStatus,
  type WorkflowTraceExport
} from './agentos'

export type {
  Checkpoint,
  EvaluationRun,
  PageResponse,
  ReviewRecord,
  ReviewRequest,
  ReviewDecision,
  StepStatus,
  TraceEvent,
  WorkflowRun,
  WorkflowRunQuery,
  WorkflowStatus,
  WorkflowTraceExport
}

export const workflowApi = {
  listRuns(params: WorkflowRunQuery = {}): Promise<PageResponse<WorkflowRun>> {
    return agentosApi.listWorkflowRuns({ page: 1, pageSize: 20, ...params })
  },

  getRun(runId: string): Promise<WorkflowRun> {
    return agentosApi.getWorkflowRun(runId)
  },

  getTrace(runId: string): Promise<WorkflowTraceExport> {
    return agentosApi.getWorkflowTrace(runId)
  },

  exportTraceMarkdown(runId: string): Promise<string> {
    return agentosApi.exportWorkflowTraceMarkdown(runId)
  },

  listCheckpoints(runId: string): Promise<PageResponse<Checkpoint> & { runId: string }> {
    return agentosApi.listWorkflowCheckpoints(runId)
  },

  listReviews(runId: string): Promise<PageResponse<ReviewRecord> & { runId: string }> {
    return agentosApi.listWorkflowReviews(runId)
  },

  submitReview(runId: string, payload: ReviewRequest): Promise<WorkflowRun> {
    return agentosApi.applyWorkflowReview(runId, payload)
  },

  resumeFromCheckpoint(runId: string, checkpointId: string): Promise<WorkflowRun> {
    return agentosApi.resumeWorkflow(runId, checkpointId)
  },

  getMetrics(params: Pick<WorkflowRunQuery, 'status' | 'domain' | 'workflowId' | 'source'> = {}): Promise<EvaluationRun> {
    return agentosApi.getWorkflowMetrics(params)
  }
}
