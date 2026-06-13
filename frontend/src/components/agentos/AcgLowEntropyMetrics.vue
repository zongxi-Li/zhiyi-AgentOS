<template>
  <section class="acg-metrics ui-surface">
    <header class="panel-head">
      <div class="head-left">
        <el-icon class="head-icon"><DataLine /></el-icon>
        <h4>低熵通信指标</h4>
      </div>
    </header>

    <div class="metric-grid">
      <div class="metric-card highlight">
        <span class="metric-value">{{ savingPercent }}</span>
        <span class="metric-label">平均 Token 节省率</span>
      </div>
      <div class="metric-card">
        <span class="metric-value">{{ formatNum(metrics.tokensSaved) }}</span>
        <span class="metric-label">累计节省 Token</span>
      </div>
      <div class="metric-card">
        <span class="metric-value">{{ formatNum(metrics.tokensDelivered) }} / {{ formatNum(metrics.tokensAvailable) }}</span>
        <span class="metric-label">投递 / 可获取</span>
      </div>
      <div class="metric-card" :class="{ warn: metrics.recoveryCount > 0 }">
        <span class="metric-value">{{ metrics.recoveryCount }}</span>
        <span class="metric-label">自愈恢复次数</span>
      </div>
    </div>

    <div class="bar-wrap" v-if="metrics.tokensAvailable > 0">
      <div class="bar-track">
        <div class="bar-fill" :style="{ width: deliveredPercent }"></div>
      </div>
      <div class="bar-caption">
        <span>实际投递 {{ deliveredPercent }}</span>
        <span class="saved">引擎按需投递，省去 {{ savingPercent }} 冗余</span>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { DataLine } from '@element-plus/icons-vue'
import type { AcgLowEntropyMetrics } from '@/services/api/agentos'

const props = withDefaults(defineProps<{
  metrics?: AcgLowEntropyMetrics
}>(), {
  metrics: () => ({
    averageSavingRatio: 0,
    tokensAvailable: 0,
    tokensDelivered: 0,
    tokensSaved: 0,
    recoveryCount: 0
  })
})

const savingPercent = computed(() => `${(props.metrics.averageSavingRatio * 100).toFixed(1)}%`)

const deliveredPercent = computed(() => {
  const { tokensAvailable, tokensDelivered } = props.metrics
  if (!tokensAvailable) return '0%'
  return `${Math.min(100, (tokensDelivered / tokensAvailable) * 100).toFixed(1)}%`
})

const formatNum = (n: number) => {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return String(n ?? 0)
}
</script>

<style scoped>
.acg-metrics { display: flex; flex-direction: column; }
.panel-head { display: flex; align-items: center; margin-bottom: var(--space-md); }
.head-left { display: flex; align-items: center; gap: 6px; }
.head-icon { font-size: 15px; color: var(--primary-color); }
.panel-head h4 { margin: 0; font-size: 14px; font-weight: 700; color: var(--text-primary); }

.metric-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--space-sm);
}
.metric-card {
  display: flex; flex-direction: column; gap: 4px;
  padding: var(--space-md); border-radius: var(--radius-md);
  background: var(--bg-input); border: 1px solid var(--border-light);
}
.metric-card.highlight { background: var(--primary-fade); border-color: var(--primary-color); }
.metric-card.warn { background: rgba(154, 116, 50, 0.1); border-color: var(--warning); }
.metric-value { font-size: 20px; font-weight: 800; color: var(--text-primary); line-height: 1.1; }
.metric-card.highlight .metric-value { color: var(--primary-color); }
.metric-label { font-size: 11px; color: var(--text-secondary); }

.bar-wrap { margin-top: var(--space-md); }
.bar-track { height: 10px; background: var(--primary-fade); border-radius: 6px; overflow: hidden; }
.bar-fill { height: 100%; background: var(--primary-color); border-radius: 6px; transition: width .4s ease; }
.bar-caption { display: flex; justify-content: space-between; margin-top: 4px; font-size: 11px; color: var(--text-secondary); }
.bar-caption .saved { color: var(--success); font-weight: 600; }
</style>
