<template>
  <section class="skill-panel">
    <div class="panel-header">
      <h3>教师 Agent 工作台</h3>
      <span class="meta-pill">技能 {{ skillsUsed?.length || 0 }}</span>
    </div>

    <div class="panel-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
        <span v-if="tab.count > 0" class="tab-badge">{{ tab.count }}</span>
      </button>
    </div>

    <div class="panel-body">
      <div v-show="activeTab === 'skills'" class="tab-content">
        <div class="sub-section">
          <div class="sub-title">联邦增强状态</div>
          <div class="federated-row">
            <span class="status-pill" :class="federatedStatusClass">{{ federatedStatusText }}</span>
            <span class="meta" v-if="federated?.applied">
              调整：{{ formatAdjustment(federated?.risk_adjustment) }} | 置信度：{{ formatPercent(federated?.confidence) }} |
              节点：{{ federated?.federated_nodes_count ?? 0 }}
            </span>
          </div>
        </div>

        <div class="sub-section">
          <div class="sub-title">已调用技能</div>
          <div v-if="!skillVisuals.length" class="empty">
            <span class="empty-icon">📭</span>
            <span>暂无技能调用记录</span>
          </div>
          <div v-else class="skill-list">
            <div
              v-for="item in skillVisuals"
              :key="item.raw"
              class="skill-item"
              :class="item.tone"
              :title="item.raw"
            >
              <span class="skill-icon">{{ item.icon }}</span>
              <span class="skill-name">{{ item.zh }}</span>
              <span class="skill-state">
                <span class="state-dot"></span>
                已执行
              </span>
            </div>
          </div>
        </div>
      </div>

      <div v-show="activeTab === 'trace'" class="tab-content">
        <div v-if="!trace.length" class="empty">
          <span class="empty-icon">🧭</span>
          <span>暂无执行轨迹</span>
        </div>
        <div v-else class="trace-container">
          <TraceTimeline :trace="trace" />
        </div>
      </div>

      <div v-show="activeTab === 'results'" class="tab-content results-tab">
        <slot name="results">
          <div class="empty">
            <span class="empty-icon">📦</span>
            <span>暂无技能结果</span>
          </div>
        </slot>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import TraceTimeline, { type TraceStep } from './TraceTimeline.vue'
import { toSkillNameZh } from '@/utils/agentDisplay'

interface FederatedInfo {
  enabled?: boolean
  applied?: boolean
  risk_adjustment?: number
  confidence?: number
  federated_nodes_count?: number
}

interface SkillVisual {
  icon: string
  tone: 'blue' | 'green' | 'orange' | 'purple' | 'indigo'
}

const props = defineProps<{
  skillsUsed: string[]
  trace: TraceStep[]
  federated?: FederatedInfo
  resultCount?: number
}>()

const activeTab = ref<'skills' | 'trace' | 'results'>('skills')

const tabs = computed(() => [
  { key: 'skills' as const, label: '技能调用', icon: '🧠', count: props.skillsUsed?.length || 0 },
  { key: 'trace' as const, label: '执行轨迹', icon: '🪄', count: props.trace?.length || 0 },
  { key: 'results' as const, label: '结果面板', icon: '📘', count: props.resultCount || 0 }
])

const SKILL_VISUAL_MAP: Record<string, SkillVisual> = {
  student_diagnosis: { icon: '🩺', tone: 'blue' },
  lesson_plan_generation: { icon: '📝', tone: 'indigo' },
  homework_grading: { icon: '✅', tone: 'green' },
  error_analysis_question_push: { icon: '🎯', tone: 'orange' },
  tutoring_qa: { icon: '💡', tone: 'purple' },
  learning_path_planning: { icon: '🗺️', tone: 'indigo' },
  progress_report_generation: { icon: '📈', tone: 'blue' },
  classroom_interaction_design: { icon: '🤝', tone: 'green' },
  parent_communication_suggestion: { icon: '👪', tone: 'purple' }
}

const skillVisuals = computed(() => {
  return (props.skillsUsed || []).map(raw => {
    const key = (raw || '').trim().toLowerCase()
    const visual = SKILL_VISUAL_MAP[key] || { icon: '📌', tone: 'blue' as const }
    return {
      raw,
      zh: toSkillNameZh(raw),
      icon: visual.icon,
      tone: visual.tone
    }
  })
})

const federatedStatusText = computed(() => {
  if (!props.federated?.enabled) return '已关闭'
  return props.federated?.applied ? '已启用（本轮生效）' : '已开启（本轮未生效）'
})

const federatedStatusClass = computed(() => {
  if (!props.federated?.enabled) return 'off'
  return props.federated?.applied ? 'on' : 'idle'
})

const formatPercent = (v?: number) => `${Math.max(0, Math.round((v || 0) * 100))}%`
const formatAdjustment = (v?: number) => {
  const value = v || 0
  return `${value >= 0 ? '+' : ''}${(value * 100).toFixed(1)}%`
}
</script>

<style scoped>
.skill-panel {
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid var(--border-light);
  border-radius: 14px;
  overflow: hidden;
  height: 100%;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border-light);
  background: linear-gradient(135deg, #f6fdf8, #eef7ff);
}

.panel-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}

.meta-pill {
  font-size: 11px;
  border-radius: 999px;
  padding: 3px 10px;
  background: #eff6ff;
  color: #1d4ed8;
  white-space: nowrap;
  font-weight: 600;
}

.panel-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-light);
  background: #fafbfc;
}

.tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 10px 8px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  transition: all 0.2s ease;
  border-bottom: 2px solid transparent;
  position: relative;
}

.tab-btn:hover {
  background: rgba(59, 130, 246, 0.05);
  color: var(--text-primary);
}

.tab-btn.active {
  color: #2563eb;
  border-bottom-color: #2563eb;
  background: rgba(59, 130, 246, 0.06);
}

.tab-icon {
  font-size: 14px;
}

.tab-label {
  white-space: nowrap;
}

.tab-badge {
  font-size: 10px;
  min-width: 16px;
  height: 16px;
  line-height: 16px;
  text-align: center;
  border-radius: 999px;
  background: #e0e7ff;
  color: #3730a3;
  padding: 0 4px;
  font-weight: 700;
}

.tab-btn.active .tab-badge {
  background: #2563eb;
  color: #fff;
}

.panel-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.tab-content {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 12px 14px;
}

.sub-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 14px;
}

.sub-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-secondary);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.federated-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.status-pill {
  width: fit-content;
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 12px;
  font-weight: 500;
}

.status-pill.on {
  background: #dcfce7;
  color: #166534;
}

.status-pill.off {
  background: #f3f4f6;
  color: #374151;
}

.status-pill.idle {
  background: #e0e7ff;
  color: #3730a3;
}

.meta {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.45;
  word-break: break-word;
}

.skill-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.skill-item {
  display: grid;
  grid-template-columns: 28px 1fr auto;
  align-items: center;
  gap: 8px;
  min-height: 38px;
  border: 1px solid;
  border-radius: 10px;
  padding: 8px 10px;
  font-size: 12px;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.skill-item:hover {
  transform: translateX(2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.skill-item.blue {
  background: #eff6ff;
  border-color: #bfdbfe;
  color: #1d4ed8;
}

.skill-item.green {
  background: #ecfdf5;
  border-color: #a7f3d0;
  color: #047857;
}

.skill-item.orange {
  background: #fff7ed;
  border-color: #fed7aa;
  color: #c2410c;
}

.skill-item.purple {
  background: #f5f3ff;
  border-color: #ddd6fe;
  color: #6d28d9;
}

.skill-item.indigo {
  background: #eef2ff;
  border-color: #c7d2fe;
  color: #4338ca;
}

.skill-icon {
  text-align: center;
  font-size: 16px;
}

.skill-name {
  font-weight: 600;
  min-width: 0;
  word-break: break-word;
}

.skill-state {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  opacity: 0.85;
  white-space: nowrap;
}

.state-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.6;
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px 16px;
  color: var(--text-secondary);
  font-size: 13px;
}

.empty-icon {
  font-size: 28px;
  opacity: 0.6;
}

.trace-container {
  padding: 4px 0;
}

.results-tab :deep(.el-collapse) {
  border-top: none;
  border-bottom: none;
}

.results-tab :deep(.el-collapse-item__header) {
  min-height: 40px;
  height: auto;
  line-height: 1.45;
  padding: 8px 0;
  align-items: flex-start;
  font-size: 13px;
  font-weight: 600;
  white-space: normal;
}

.results-tab :deep(.el-collapse-item__arrow) {
  margin-top: 2px;
}

.results-tab :deep(.el-collapse-item__wrap) {
  overflow: hidden;
}

.results-tab :deep(.el-collapse-item__content) {
  padding-bottom: 10px;
  word-break: break-word;
}
</style>
