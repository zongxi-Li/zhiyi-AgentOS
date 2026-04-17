import request from '@/utils/request'
import type { AgentTraceStep, FederatedInfo } from './agentLawyer'

const PROGRAMMER_AGENT_TIMEOUT_MS = 120000

export interface CodeReviewResult {
  summary?: string
  quality_score?: number
  issues?: Array<{
    severity?: string
    file?: string
    line?: number
    message?: string
    description?: string
    suggestion?: string
  }>
  metrics?: {
    complexity?: number | string
    coverage?: number | string
    duplicates?: number | string
    debt?: number | string
  }
}

export interface DebugTraceResult {
  root_cause?: string
  rootCause?: string
  steps?: Array<{
    action?: string
    description?: string
    file?: string
    line?: number
    detail?: string
    output?: string
    status?: string
  }>
  fix_suggestion?: string
  fixSuggestion?: string
  status?: string
}

export interface ArchSuggestResult {
  overview?: string
  pattern?: string
  suggestions?: Array<{
    priority?: string
    category?: string
    title?: string
    name?: string
    description?: string
    reason?: string
    implementation?: string
  }>
  tech_stack?: string[]
  techStack?: string[]
}

export interface UnitTestResult {
  summary?: string
  coverage?: number
  test_cases?: Array<{
    name?: string
    test_name?: string
    description?: string
    code?: string
    test_code?: string
    status?: string
    assertions?: number
  }>
}

export interface ProgrammerAgentRequest {
  text: string
  sessionId?: string
}

export interface ProgrammerAgentResponse {
  success: boolean
  answer: string
  sessionId: string
  skillsUsed: string[]
  trace: AgentTraceStep[]
  riskLevel?: string
  federated?: FederatedInfo
  codeReview?: CodeReviewResult
  code_review?: CodeReviewResult
  debugTrace?: DebugTraceResult
  debug_trace?: DebugTraceResult
  archSuggest?: ArchSuggestResult
  architecture_suggestion?: ArchSuggestResult
  unitTest?: UnitTestResult
  unit_test_generation?: UnitTestResult
  message?: string
  error?: string
}

export const agentProgrammerApi = {
  async chat(payload: ProgrammerAgentRequest): Promise<ProgrammerAgentResponse> {
    const response = await request.post<ProgrammerAgentResponse>(
      '/agent/programmer/chat',
      payload,
      { timeout: PROGRAMMER_AGENT_TIMEOUT_MS }
    )
    return response.data
  }
}
