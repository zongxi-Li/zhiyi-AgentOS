import request from '@/utils/request'
import type { AgentTraceStep, FederatedInfo } from './agentLawyer'

const WRITER_AGENT_TIMEOUT_MS = 120000

export interface OutlineResult {
  title?: string
  outline?: Array<{
    title: string
    level?: number
    summary?: string
    description?: string
    children?: Array<{
      title: string
      level?: number
      summary?: string
      description?: string
    }>
  }>
  outline_markdown?: string
  outlineMarkdown?: string
}

export interface StyleAnalysisResult {
  overall_score?: number
  overallScore?: number
  dominant_style?: string
  dominantStyle?: string
  dimensions?: Array<{
    name?: string
    dimension?: string
    score?: number
    value?: number
    comment?: string
    description?: string
  }>
  suggestions?: string[]
}

export interface PlotLogicResult {
  summary?: string
  logic_score?: number
  logicScore?: number
  timeline?: Array<{
    chapter?: string
    time?: string
    event?: string
    description?: string
  }>
  issues?: Array<{
    type?: string
    description?: string
    message?: string
    chapter?: string
    location?: string
    suggestion?: string
  }>
}

export interface PolishDiffResult {
  original?: string
  polished?: string
  changes?: Array<{
    type?: string
    old?: string
    before?: string
    new?: string
    after?: string
    reason?: string
  }>
  overall_comment?: string
  overallComment?: string
}

export interface WriterAgentRequest {
  text: string
  sessionId?: string
}

export interface WriterAgentResponse {
  success: boolean
  answer: string
  sessionId: string
  skillsUsed: string[]
  trace: AgentTraceStep[]
  riskLevel?: string
  federated?: FederatedInfo
  outline?: OutlineResult
  outline_generation?: OutlineResult
  styleAnalysis?: StyleAnalysisResult
  style_analysis?: StyleAnalysisResult
  plotLogic?: PlotLogicResult
  plot_logic_check?: PlotLogicResult
  polishDiff?: PolishDiffResult
  text_polish?: PolishDiffResult
  message?: string
  error?: string
}

export const agentWriterApi = {
  async chat(payload: WriterAgentRequest): Promise<WriterAgentResponse> {
    const response = await request.post<WriterAgentResponse>(
      '/agent/writer/chat',
      payload,
      { timeout: WRITER_AGENT_TIMEOUT_MS }
    )
    return response.data
  }
}
