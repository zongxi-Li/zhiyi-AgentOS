<template>
  <section class="card">
    <header class="card-head">
      <h4>错题归因与推题</h4>
      <span class="count">推题 {{ questions.length }}</span>
    </header>

    <div class="block">
      <div class="title">知识漏洞</div>
      <ul v-if="knowledgeGap.length" class="list">
        <li v-for="item in knowledgeGap" :key="item">{{ item }}</li>
      </ul>
      <div v-else class="empty">暂无知识漏洞信息</div>
    </div>

    <div class="block">
      <div class="title">归因总结</div>
      <p class="text">{{ data?.analysis_summary || '暂无归因总结。' }}</p>
    </div>

    <div class="block">
      <div class="title">推荐练习题</div>
      <div v-if="questions.length" class="question-list">
        <div class="question-item" v-for="(item, idx) in questions" :key="item.id || idx">
          <div class="q-text">{{ idx + 1 }}. {{ item.question_text || item.question || '未提供题干' }}</div>
          <div class="q-meta">
            <span>难度：{{ item.difficulty || '-' }}</span>
            <span>题型：{{ item.question_type || '-' }}</span>
            <span>学科：{{ item.subject || '-' }}</span>
          </div>
        </div>
      </div>
      <div v-else class="empty">暂无推荐题目</div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface SimilarQuestion {
  id?: string
  question_text?: string
  question?: string
  difficulty?: string
  question_type?: string
  subject?: string
}

interface ErrorPushData {
  knowledge_gap?: string[]
  analysis_summary?: string
  similar_questions?: SimilarQuestion[]
}

const props = defineProps<{ data?: ErrorPushData }>()

const knowledgeGap = computed(() => props.data?.knowledge_gap || [])
const questions = computed(() => props.data?.similar_questions || [])
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

.count {
  font-size: 12px;
  color: #1d4ed8;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
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

.question-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.question-item {
  border: 1px solid #dbeafe;
  background: #f8fbff;
  border-radius: 10px;
  padding: 8px 10px;
}

.q-text {
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-primary);
}

.q-meta {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 12px;
  color: var(--text-secondary);
}

.empty {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
