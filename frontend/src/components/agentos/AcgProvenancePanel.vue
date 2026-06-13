<template>
  <section class="acg-provenance ui-surface">
    <header class="panel-head">
      <div class="head-left">
        <el-icon class="head-icon"><Connection /></el-icon>
        <h4>数据血缘与恢复轨迹</h4>
      </div>
      <div class="tabs">
        <button :class="{ active: tab === 'lineage' }" @click="tab = 'lineage'">数据血缘</button>
        <button :class="{ active: tab === 'recovery' }" @click="tab = 'recovery'">恢复轨迹</button>
      </div>
    </header>

    <!-- 数据血缘 -->
    <div v-if="tab === 'lineage'" class="tab-body">
      <div v-if="!consumptions.length" class="empty">暂无数据流转记录</div>
      <ul v-else class="lineage-list">
        <li v-for="(c, i) in consumptions" :key="c.eventId || i" class="lineage-item">
          <div class="flow">
            <span class="node-tag producer" v-for="p in c.producerStepIds" :key="p">{{ p }}</span>
            <el-icon class="arrow"><Right /></el-icon>
            <span class="node-tag consumer">{{ c.consumerStepId }}</span>
          </div>
          <div class="fields" v-if="c.consumedFields && c.consumedFields.length">
            消费字段：<code v-for="f in c.consumedFields" :key="f">{{ f }}</code>
          </div>
        </li>
      </ul>
    </div>

    <!-- 恢复轨迹 -->
    <div v-else class="tab-body">
      <div v-if="!recoveryTrace.length" class="empty">本次运行未发生故障恢复</div>
      <ul v-else class="recovery-list">
        <li v-for="(e, i) in recoveryTrace" :key="e.eventId || i" class="recovery-item" :class="e.eventType">
          <div class="rec-head">
            <span class="rec-type">{{ recoveryLabel(e.eventType) }}</span>
            <span class="rec-step" v-if="e.stepId">{{ e.stepId }}</span>
          </div>
          <div class="rec-obs">{{ e.observation }}</div>
          <div class="rec-meta" v-if="e.payload?.strategy">
            策略：<strong>{{ e.payload.strategy }}</strong>
            <span v-if="e.payload.faultType"> · 故障类型：{{ e.payload.faultType }}</span>
          </div>
        </li>
      </ul>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Connection, Right } from '@element-plus/icons-vue'
import type { ProvenanceConsumption, TraceEvent } from '@/services/api/agentos'

withDefaults(defineProps<{
  consumptions?: ProvenanceConsumption[]
  recoveryTrace?: TraceEvent[]
}>(), {
  consumptions: () => [],
  recoveryTrace: () => []
})

const tab = ref<'lineage' | 'recovery'>('lineage')

const recoveryLabel = (t: string) => {
  if (t === 'step_failed') return '故障注入'
  if (t === 'run_recovered') return '检查点恢复'
  return t
}
</script>

<style scoped>
.acg-provenance { display: flex; flex-direction: column; }
.panel-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-sm); }
.head-left { display: flex; align-items: center; gap: 6px; }
.head-icon { font-size: 15px; color: var(--primary-color); }
.panel-head h4 { margin: 0; font-size: 14px; font-weight: 700; color: var(--text-primary); }
.tabs { display: flex; gap: 4px; }
.tabs button {
  padding: 4px 10px; font-size: 12px; border: 1px solid var(--border-light);
  background: var(--bg-input); color: var(--text-secondary); border-radius: 6px; cursor: pointer;
}
.tabs button.active { background: var(--primary-color); color: #fff; border-color: var(--primary-color); }

.tab-body { flex: 1 1 320px; min-height: 320px; overflow-y: auto; }
.empty {
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 12px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 13px;
}

.lineage-list, .recovery-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--space-sm); }
.lineage-item { padding: var(--space-sm); border: 1px solid var(--border-light); border-radius: var(--radius-md); background: var(--bg-panel); }
.flow { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.node-tag { font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 600; }
.node-tag.producer { background: var(--bg-input); color: var(--text-secondary); border: 1px solid var(--border-light); }
.node-tag.consumer { background: var(--primary-fade); color: var(--primary-color); }
.arrow { color: var(--text-disabled); font-size: 13px; }
.fields { margin-top: 6px; font-size: 11px; color: var(--text-secondary); }
.fields code { background: var(--bg-input); padding: 1px 5px; border-radius: 4px; margin-right: 4px; }

.recovery-item { padding: var(--space-sm); border-radius: var(--radius-md); border-left: 3px solid var(--border-light); background: var(--bg-panel); }
.recovery-item.step_failed { border-left-color: var(--warning); }
.recovery-item.run_recovered { border-left-color: var(--success); }
.rec-head { display: flex; justify-content: space-between; align-items: center; }
.rec-type { font-size: 12px; font-weight: 700; color: var(--text-primary); }
.rec-step { font-size: 11px; color: var(--text-secondary); font-family: monospace; }
.rec-obs { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
.rec-meta { font-size: 11px; color: var(--text-secondary); margin-top: 4px; }
.rec-meta strong { color: var(--success); }
</style>
