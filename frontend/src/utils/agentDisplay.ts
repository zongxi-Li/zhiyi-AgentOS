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
  parent_communication_suggestion: '家长沟通建议',
  code_review: '代码审查',
  debug_trace: '调试追踪',
  architecture_suggestion: '架构建议',
  unit_test_generation: '单元测试生成',
  code_refactor: '代码重构',
  api_design: '接口设计',
  performance_optimization: '性能优化',
  security_audit: '安全审计',
  dependency_analysis: '依赖分析',
  outline_generation: '大纲生成',
  style_analysis: '风格分析',
  plot_logic_check: '情节逻辑检查',
  text_polish: '文本润色',
  title_optimization: '标题优化',
  character_design: '角色设计',
  dialogue_generation: '对话生成',
  copywriting: '文案创作',
  seo_optimization: 'SEO优化'
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
  parent_communication_suggestion: '输出家校沟通要点与话术。',
  code_review: '审查代码质量，识别潜在问题与改进空间。',
  debug_trace: '追踪错误根因，逐步定位问题源头。',
  architecture_suggestion: '分析架构并提出优化建议。',
  unit_test_generation: '生成覆盖关键路径的单元测试用例。',
  code_refactor: '识别代码异味并输出重构方案。',
  api_design: '设计接口规范与数据契约。',
  performance_optimization: '定位性能瓶颈并给出优化策略。',
  security_audit: '审计安全漏洞与合规风险。',
  dependency_analysis: '分析依赖关系与版本风险。',
  outline_generation: '生成文章大纲与结构规划。',
  style_analysis: '分析写作风格并给出评分与建议。',
  plot_logic_check: '检查情节逻辑一致性与时间线。',
  text_polish: '润色文本并对比修改前后差异。',
  title_optimization: '优化标题以提高吸引力。',
  character_design: '设计角色画像与性格特征。',
  dialogue_generation: '生成符合角色特征的对话内容。',
  copywriting: '创作营销文案与品牌内容。',
  seo_optimization: '优化内容以提升搜索引擎排名。'
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

const summarizeProgrammerObservation = (action: string, obj: any) => {
  if (action === 'code_review') {
    const issueCount = Array.isArray(obj?.issues) ? obj.issues.length : 0
    const score = obj?.quality_score
    return `代码审查完成：发现 ${issueCount} 个问题${score != null ? `，质量评分 ${score}` : ''}。`
  }
  if (action === 'debug_trace') {
    const stepCount = Array.isArray(obj?.steps) ? obj.steps.length : 0
    const rootCause = obj?.root_cause || obj?.rootCause ? '已定位' : '未定位'
    return `调试追踪完成：${stepCount} 步，根因${rootCause}。`
  }
  if (action === 'architecture_suggestion') {
    const suggestCount = Array.isArray(obj?.suggestions) ? obj.suggestions.length : 0
    const pattern = obj?.pattern || ''
    return `架构建议完成：${suggestCount} 条建议${pattern ? `，推荐模式 ${pattern}` : ''}。`
  }
  if (action === 'unit_test_generation') {
    const caseCount = Array.isArray(obj?.test_cases) ? obj.test_cases.length : 0
    const coverage = obj?.coverage
    return `单元测试生成完成：${caseCount} 个用例${coverage != null ? `，覆盖率 ${coverage}%` : ''}。`
  }
  if (action === 'code_refactor') {
    const count = Array.isArray(obj?.refactor_items) ? obj.refactor_items.length : 0
    return `代码重构分析完成：${count} 个重构项。`
  }
  if (action === 'performance_optimization') {
    const count = Array.isArray(obj?.bottlenecks) ? obj.bottlenecks.length : 0
    return `性能优化完成：${count} 个瓶颈点。`
  }
  if (action === 'security_audit') {
    const count = Array.isArray(obj?.vulnerabilities) ? obj.vulnerabilities.length : 0
    return `安全审计完成：${count} 个风险项。`
  }
  return ''
}

const summarizeWriterObservation = (action: string, obj: any) => {
  if (action === 'outline_generation') {
    const nodeCount = Array.isArray(obj?.outline) ? obj.outline.length : 0
    const title = obj?.title || ''
    return `大纲生成完成：${nodeCount} 个章节${title ? `，标题「${title}」` : ''}。`
  }
  if (action === 'style_analysis') {
    const score = obj?.overall_score || obj?.overallScore
    const style = obj?.dominant_style || obj?.dominantStyle || ''
    return `风格分析完成${score != null ? `：评分 ${score}` : ''}${style ? `，主导风格 ${style}` : ''}。`
  }
  if (action === 'plot_logic_check') {
    const issueCount = Array.isArray(obj?.issues) ? obj.issues.length : 0
    const score = obj?.logic_score || obj?.logicScore
    return `情节逻辑检查完成：${issueCount} 个问题${score != null ? `，逻辑评分 ${score}` : ''}。`
  }
  if (action === 'text_polish') {
    const changeCount = Array.isArray(obj?.changes) ? obj.changes.length : 0
    return `文本润色完成：${changeCount} 处修改。`
  }
  if (action === 'title_optimization') {
    const count = Array.isArray(obj?.alternatives) ? obj.alternatives.length : 0
    return `标题优化完成：${count} 个备选标题。`
  }
  if (action === 'character_design') {
    const count = Array.isArray(obj?.characters) ? obj.characters.length : 0
    return `角色设计完成：${count} 个角色。`
  }
  if (action === 'copywriting') {
    const count = Array.isArray(obj?.variants) ? obj.variants.length : 0
    return `文案创作完成：${count} 个变体。`
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

    const programmerSummary = summarizeProgrammerObservation(key, parsed)
    if (programmerSummary) return programmerSummary

    const writerSummary = summarizeWriterObservation(key, parsed)
    if (writerSummary) return writerSummary

    return `已返回结构化结果（${Object.keys(parsed).length} 个字段）。`
  }

  return truncate(raw, 180)
}
