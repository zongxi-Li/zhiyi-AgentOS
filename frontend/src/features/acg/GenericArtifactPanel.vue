<template>
  <section class="generic-artifacts ui-surface">
    <header><h4>任务交付物</h4><span>{{ deliverables.length }} 项</span></header>
    <div v-if="!deliverables.length" class="empty">任务完成后，交付物将在这里汇总</div>
    <article v-else-if="finalReport" class="final-report"><pre>{{ finalReport }}</pre></article>
    <div v-else class="artifact-list">
      <details v-for="item in deliverables" :key="item.stepId">
        <summary>{{ item.name }} <small>{{ item.status }}</small></summary>
        <pre>{{ JSON.stringify(item.output, null, 2) }}</pre>
      </details>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { AcgDeliverable } from '@/services/api/workflow'
defineProps<{ deliverables: AcgDeliverable[]; finalReport: string | null }>()
</script>

<style scoped>
.generic-artifacts { padding:14px; }
header { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
header h4 { margin:0; }
header span, .empty, summary small { color:var(--text-secondary); }
.artifact-list { display:flex; flex-direction:column; gap:8px; }
details, .final-report { padding:10px; border:1px solid var(--border-color); border-radius:8px; }
summary { cursor:pointer; font-weight:600; }
pre { margin:8px 0 0; white-space:pre-wrap; overflow-wrap:anywhere; font:12px/1.6 var(--font-mono, monospace); }
</style>
