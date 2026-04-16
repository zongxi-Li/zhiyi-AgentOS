const normalizeKey = (value?: string) => (value || '').trim().toLowerCase()

const tryParseJson = (value: string): any | null => {
  try {
    return JSON.parse(value)
  } catch {
    return null
  }
}

const truncate = (value: string, max = 160) => {
  const text = (value || '').replace(/\s+/g, ' ').trim()
  if (text.length <= max) return text
  return `${text.slice(0, max)}...`
}

export const SKILL_NAME_ZH_MAP: Record<string, string> = {
  case_understanding: '案情理解',
  statute_retrieval: '法条检索',
  case_retrieval: '判例检索',
  evidence_analysis: '证据分析',
  limitation_calculation: '诉讼时效',
  jurisdiction_determination: '管辖确定',
  hearing_outline_generation: '庭审提纲',
  document_generation: '文书生成',
  risk_assessment: '风险评估',
  student_diagnosis: '学情诊断',
  lesson_plan_generation: '个性化教案生成',
  homework_grading: '作业批改',
  error_analysis_question_push: '错题归因与推题',
  tutoring_qa: '智能答疑',
  learning_path_planning: '学习路径规划',
  progress_report_generation: '学情报告生成',
  classroom_interaction_design: '课堂互动设计',
  parent_communication_suggestion: '家长沟通建议'
}

const THOUGHT_ZH_BY_ACTION: Record<string, string> = {
  case_understanding: '先完成案情梳理，提取争议焦点与事实要点。',
  statute_retrieval: '检索相关法条，建立法律依据。',
  case_retrieval: '检索类似案例，补充判例支撑。',
  evidence_analysis: '评估证据强度、关联性和缺口。',
  limitation_calculation: '计算诉讼时效与关键截止时间。',
  jurisdiction_determination: '确定可起诉法院与优先方案。',
  hearing_outline_generation: '生成庭审问答与举证提纲。',
  document_generation: '输出结构化法律文书草稿。',
  risk_assessment: '汇总风险并给出行动建议。',
  student_diagnosis: '先做学情诊断，定位薄弱点和学习画像。',
  lesson_plan_generation: '结合学情与课题生成可执行教案。',
  homework_grading: '对照标准批改并输出改进建议。',
  error_analysis_question_push: '分析错因并推送同类训练题。',
  tutoring_qa: '给出分步引导，避免直接给出答案。',
  learning_path_planning: '生成分阶段学习路径和资源建议。',
  progress_report_generation: '汇总阶段表现并形成报告。',
  classroom_interaction_design: '设计提问链、活动和板书策略。',
  parent_communication_suggestion: '输出家校沟通要点与话术。'
}

const RISK_LEVEL_ZH_MAP: Record<string, string> = {
  high: '高',
  medium: '中',
  low: '低',
  unknown: '未知'
}

export const toSkillNameZh = (skill?: string) => {
  const key = normalizeKey(skill)
  return SKILL_NAME_ZH_MAP[key] || skill || '未知技能'
}

export const toActionLabelZh = (action?: string) => {
  const key = normalizeKey(action)
  const zh = toSkillNameZh(key)
  if (!key) return '未指定动作'
  return zh === key ? key : zh
}

export const toThoughtZh = (thought?: string, action?: string) => {
  const key = normalizeKey(action)
  if (THOUGHT_ZH_BY_ACTION[key]) return THOUGHT_ZH_BY_ACTION[key]
  const raw = (thought || '').trim()
  if (!raw) return '系统正在规划下一步处理动作。'
  return raw
}

export const toRiskLevelZh = (riskLevel?: string) => {
  const key = normalizeKey(riskLevel)
  return RISK_LEVEL_ZH_MAP[key] || riskLevel || '未知'
}

const summarizeLawyerObservation = (action: string, obj: any) => {
  if (action === 'evidence_analysis') {
    const evidenceCount = Array.isArray(obj?.evidence_items) ? obj.evidence_items.length : 0
    const missingCount = Array.isArray(obj?.missing_evidence) ? obj.missing_evidence.length : 0
    return `证据分析完成：识别证据 ${evidenceCount} 项，缺失 ${missingCount} 项。`
  }
  if (action === 'limitation_calculation') {
    const deadline = obj?.deadline || obj?.expiry_date || '未提供'
    const days = typeof obj?.days_remaining === 'number' ? obj.days_remaining : null
    return `时效计算完成：截止日期 ${deadline}${days !== null ? `，剩余 ${days} 天` : ''}。`
  }
  if (action === 'jurisdiction_determination') {
    const courts = Array.isArray(obj?.courts)
      ? obj.courts.length
      : Array.isArray(obj?.recommended_courts)
        ? obj.recommended_courts.length
        : 0
    return `管辖分析完成：提供 ${courts} 个法院建议。`
  }
  if (action === 'hearing_outline_generation') {
    const agendaCount = Array.isArray(obj?.agenda) ? obj.agenda.length : 0
    const outlineLength = String(obj?.outline_markdown || obj?.outline || '').length
    return `庭审提纲生成完成${agendaCount ? `：${agendaCount} 个模块` : ''}${outlineLength ? `，内容约 ${outlineLength} 字` : ''}。`
  }
  if (action === 'risk_assessment') {
    const level = toRiskLevelZh(obj?.risk_level || obj?.riskLevel)
    return `风险评估完成：风险等级 ${level}。`
  }
  return ''
}

const summarizeTeacherObservation = (action: string, obj: any) => {
  if (action === 'student_diagnosis') {
    const weakCount = Array.isArray(obj?.weak_points) ? obj.weak_points.length : 0
    const level = obj?.mastery_level || 'unknown'
    return `学情诊断完成：薄弱点 ${weakCount} 项，掌握等级 ${level}。`
  }
  if (action === 'lesson_plan_generation') {
    const lessonLength = String(obj?.lesson_plan || '').length
    return `教案生成完成：内容约 ${lessonLength} 字。`
  }
  if (action === 'homework_grading') {
    const score = obj?.score
    return `作业批改完成：评分 ${score ?? '--'}。`
  }
  if (action === 'error_analysis_question_push') {
    const gapCount = Array.isArray(obj?.knowledge_gap) ? obj.knowledge_gap.length : 0
    const qCount = Array.isArray(obj?.similar_questions) ? obj.similar_questions.length : 0
    return `错题归因完成：漏洞 ${gapCount} 项，推题 ${qCount} 题。`
  }
  if (action === 'learning_path_planning') {
    const scheduleCount = Array.isArray(obj?.schedule) ? obj.schedule.length : 0
    return `学习路径生成完成：计划 ${scheduleCount} 天。`
  }
  if (action === 'progress_report_generation') {
    const trend = obj?.trend?.trend || 'unknown'
    return `学情报告完成：趋势 ${trend}。`
  }
  if (action === 'classroom_interaction_design') {
    const qCount = Array.isArray(obj?.question_chain) ? obj.question_chain.length : 0
    return `互动设计完成：提问链 ${qCount} 条。`
  }
  if (action === 'parent_communication_suggestion') {
    const count = Array.isArray(obj?.communication_points) ? obj.communication_points.length : 0
    return `家校沟通建议生成完成：要点 ${count} 条。`
  }
  if (action === 'tutoring_qa') {
    const steps = Array.isArray(obj?.steps) ? obj.steps.length : 0
    return `智能答疑完成：引导步骤 ${steps} 条。`
  }
  return ''
}

export const summarizeObservationZh = (action?: string, observation?: string) => {
  if (!observation) return '暂无观察结果。'

  const raw = observation.trim()
  const key = normalizeKey(action)
  const parsed = tryParseJson(raw)

  if (parsed && typeof parsed === 'object') {
    const lawyerSummary = summarizeLawyerObservation(key, parsed)
    if (lawyerSummary) return lawyerSummary

    const teacherSummary = summarizeTeacherObservation(key, parsed)
    if (teacherSummary) return teacherSummary

    return `已返回结构化结果（${Object.keys(parsed).length} 个字段）。`
  }

  return truncate(raw, 180)
}
