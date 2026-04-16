<template>
  <section class="card">
    <header class="card-head">
      <h4>学情诊断</h4>
      <span class="level" :class="masteryLevelClass">掌握度 {{ masteryLevelText }}</span>
    </header>

    <div class="radar-wrap">
      <svg viewBox="0 0 220 220" class="radar-svg" aria-label="diagnosis-radar">
        <polygon v-for="(ring, idx) in rings" :key="idx" :points="ring" class="radar-ring" />
        <line v-for="axis in axes" :key="axis" x1="110" y1="110" :x2="axisPoint(axis).x" :y2="axisPoint(axis).y" class="radar-axis" />
        <polygon :points="polygonPoints" class="radar-area" />
      </svg>
      <div class="metrics">
        <div class="metric" v-for="item in scoreItems" :key="item.key">
          <span class="label">{{ item.label }}</span>
          <el-progress :percentage="Math.round(item.value)" :stroke-width="8" />
        </div>
      </div>
    </div>

    <p class="summary">{{ data?.diagnosis_summary || '暂无学情诊断说明。' }}</p>

    <div class="block">
      <div class="title">薄弱点</div>
      <ul v-if="weakPoints.length" class="list">
        <li v-for="item in weakPoints" :key="item">{{ item }}</li>
      </ul>
      <div v-else class="empty">暂无</div>
    </div>

    <div class="block">
      <div class="title">优势项</div>
      <ul v-if="strengths.length" class="list">
        <li v-for="item in strengths" :key="item">{{ item }}</li>
      </ul>
      <div v-else class="empty">暂无</div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface DiagnosisData {
  weak_points?: string[]
  strengths?: string[]
  mastery_level?: string
  mastery_score?: number
  volatility?: number
  trend?: string
  learning_style?: string
  diagnosis_summary?: string
}

const props = defineProps<{ data?: DiagnosisData }>()

const data = computed(() => props.data || {})
const weakPoints = computed(() => data.value.weak_points || [])
const strengths = computed(() => data.value.strengths || [])

const masteryLevelText = computed(() => {
  const level = String(data.value.mastery_level || '').toLowerCase()
  if (level === 'high') return '高'
  if (level === 'medium') return '中'
  if (level === 'low') return '低'
  return '未知'
})

const masteryLevelClass = computed(() => {
  const level = String(data.value.mastery_level || '').toLowerCase()
  if (level === 'high') return 'high'
  if (level === 'medium') return 'medium'
  if (level === 'low') return 'low'
  return ''
})

const trendScore = computed(() => {
  const trend = String(data.value.trend || '').toLowerCase()
  if (trend === 'up') return 85
  if (trend === 'flat') return 65
  if (trend === 'down') return 40
  return 55
})

const styleScore = computed(() => {
  const style = String(data.value.learning_style || '')
  if (!style) return 60
  return style.includes('稳') ? 75 : 62
})

const stabilityScore = computed(() => {
  const volatility = Number(data.value.volatility ?? 10)
  return Math.max(0, Math.min(100, 100 - volatility * 5))
})

const scoreItems = computed(() => {
  return [
    { key: 'mastery', label: '掌握水平', value: Number(data.value.mastery_score ?? 65) },
    { key: 'trend', label: '进步趋势', value: trendScore.value },
    { key: 'stability', label: '学习稳定性', value: stabilityScore.value },
    { key: 'style', label: '学习状态', value: styleScore.value }
  ]
})

const axes = [0, 1, 2, 3]

const axisPoint = (axis: number, scale = 100) => {
  const angle = (-90 + axis * 90) * (Math.PI / 180)
  const radius = (scale / 100) * 80
  return {
    x: 110 + Math.cos(angle) * radius,
    y: 110 + Math.sin(angle) * radius
  }
}

const rings = computed(() => {
  return [25, 50, 75, 100].map(scale =>
    axes.map(axis => {
      const p = axisPoint(axis, scale)
      return `${p.x},${p.y}`
    }).join(' ')
  )
})

const polygonPoints = computed(() => {
  return scoreItems.value.map((item, idx) => {
    const p = axisPoint(idx, item.value)
    return `${p.x},${p.y}`
  }).join(' ')
})
</script>

<style scoped>
.card {
  border: 1px solid var(--border-light);
  border-radius: 12px;
  background: #fff;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-head h4 {
  margin: 0;
  font-size: 14px;
}

.level {
  font-size: 12px;
  border-radius: 999px;
  padding: 2px 8px;
  background: #f3f4f6;
  color: #374151;
}

.level.high {
  background: #dcfce7;
  color: #166534;
}

.level.medium {
  background: #fef3c7;
  color: #92400e;
}

.level.low {
  background: #fee2e2;
  color: #b91c1c;
}

.radar-wrap {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 10px;
  align-items: center;
}

.radar-svg {
  width: 220px;
  height: 220px;
}

.radar-ring {
  fill: none;
  stroke: #dbeafe;
  stroke-width: 1;
}

.radar-axis {
  stroke: #e5e7eb;
  stroke-width: 1;
}

.radar-area {
  fill: rgba(37, 99, 235, 0.2);
  stroke: #2563eb;
  stroke-width: 2;
}

.metrics {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric .label {
  display: block;
  font-size: 12px;
  margin-bottom: 4px;
  color: var(--text-secondary);
}

.summary {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
}

.title {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
}

.list {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  line-height: 1.5;
}

.empty {
  font-size: 12px;
  color: var(--text-secondary);
}

@media (max-width: 900px) {
  .radar-wrap {
    grid-template-columns: 1fr;
  }
  .radar-svg {
    margin: 0 auto;
  }
}
</style>
