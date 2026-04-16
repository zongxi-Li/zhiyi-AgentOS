<template>
  <section class="card">
    <header class="card-head">
      <h4>作业批改结果</h4>
      <span class="score-pill">评分 {{ scoreText }}</span>
    </header>

    <el-progress :percentage="scoreValue" :stroke-width="10" />

    <div class="block">
      <div class="title">评语</div>
      <p class="text">{{ data?.feedback || '暂无评语。' }}</p>
    </div>

    <div class="block">
      <div class="title">修改建议</div>
      <ul v-if="corrections.length" class="list">
        <li v-for="item in corrections" :key="item">{{ item }}</li>
      </ul>
      <div v-else class="empty">暂无建议</div>
    </div>

    <div class="block">
      <div class="title">参考范文/答案</div>
      <p class="text">{{ data?.model_answer || '暂无参考内容。' }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface GradingData {
  score?: number
  feedback?: string
  corrections?: string[]
  model_answer?: string
}

const props = defineProps<{ data?: GradingData }>()

const scoreValue = computed(() => {
  const value = Number(props.data?.score ?? 0)
  return Math.max(0, Math.min(100, Math.round(value)))
})

const scoreText = computed(() => `${scoreValue.value}/100`)
const corrections = computed(() => props.data?.corrections || [])
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
  gap: 8px;
}

.card-head h4 {
  margin: 0;
  font-size: 14px;
}

.score-pill {
  font-size: 12px;
  color: #166534;
  background: #dcfce7;
  border: 1px solid #86efac;
  border-radius: 999px;
  padding: 2px 8px;
}

.title {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
}

.text {
  margin: 4px 0 0;
  font-size: 13px;
  line-height: 1.55;
}

.list {
  margin: 4px 0 0;
  padding-left: 18px;
  font-size: 12px;
  line-height: 1.5;
}

.empty {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
