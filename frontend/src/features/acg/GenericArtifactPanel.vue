<template>
  <section class="generic-artifacts ui-surface">
    <header><h4>最终交付物</h4><span>{{ finalArtifactCount }} 项</span></header>
    <div v-if="!finalReport && !finalArtifacts.length" class="empty">任务完成后，最终成果将在这里汇总</div>
    <article v-if="finalReport" class="final-report"><pre>{{ finalReport }}</pre></article>
    <div v-else-if="finalArtifacts.length" class="final-artifact-list">
      <article v-for="artifact in finalArtifacts" :key="artifact.artifactId" class="final-report">
        <h5>{{ artifact.title }}</h5>
        <pre>{{ artifact.content }}</pre>
      </article>
    </div>
    <section v-if="stepOutputs.length" class="step-output-section">
      <header><h5>步骤产出</h5><span>{{ stepOutputs.length }} 项</span></header>
      <div class="artifact-list">
      <details v-for="item in stepOutputs" :key="item.stepId">
        <summary>{{ item.name }} <small>{{ item.status }}</small></summary>
        <pre>{{ JSON.stringify(item.output, null, 2) }}</pre>
      </details>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { AcgDeliverable, AcgFinalArtifact } from '@/services/api/workflow'

const props = defineProps<{
  stepOutputs: AcgDeliverable[]
  finalArtifacts: AcgFinalArtifact[]
  finalReport: string | null
}>()

const finalArtifactCount = computed(() => props.finalArtifacts.length || (props.finalReport ? 1 : 0))
</script>

<style scoped>
.generic-artifacts { padding:14px; }
header { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
header h4 { margin:0; }
header span, .empty, summary small { color:var(--text-secondary); }
.artifact-list { display:flex; flex-direction:column; gap:8px; }
.final-artifact-list { display:flex; flex-direction:column; gap:10px; }
.step-output-section { margin-top:14px; }
.step-output-section header { margin:0 0 8px; }
.step-output-section h5, .final-report h5 { margin:0; }
details, .final-report { padding:10px; border:1px solid var(--border-color); border-radius:8px; }
summary { cursor:pointer; font-weight:600; }
pre { margin:8px 0 0; white-space:pre-wrap; overflow-wrap:anywhere; font:12px/1.6 var(--font-mono, monospace); }
</style>
