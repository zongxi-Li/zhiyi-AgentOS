<template>
  <section class="human-review-panel">
    <div class="section-head">
      <h3>人工审核</h3>
      <span :class="{ active: canReview }">{{ canReview ? '可处理' : '无待审节点' }}</span>
    </div>

    <div v-if="!run" class="empty">选择运行记录后提交审核</div>

    <template v-else>
      <form class="review-form" @submit.prevent="submit">
        <label>
          <span>步骤</span>
          <select v-model="stepId" :disabled="!run.steps.length">
            <option v-for="step in run.steps" :key="step.stepId" :value="step.stepId">
              {{ step.name }} · {{ step.stepId }}
            </option>
          </select>
        </label>

        <label>
          <span>决定</span>
          <select v-model="decision">
            <option value="approved">通过</option>
            <option value="rejected">驳回</option>
            <option value="rerun">重跑</option>
            <option value="cancelled">取消</option>
          </select>
        </label>

        <label>
          <span>审核人</span>
          <input v-model="reviewer" placeholder="reviewer" />
        </label>

        <label>
          <span>意见</span>
          <textarea v-model="comment" rows="3" placeholder="填写审核意见" />
        </label>

        <button type="submit" :disabled="submitting || !stepId">
          {{ submitting ? '提交中...' : '提交审核' }}
        </button>
      </form>

      <div class="review-history">
        <div class="history-head">
          <strong>审核记录</strong>
          <span>{{ reviews.length }} 条</span>
        </div>
        <div v-if="loading" class="empty">正在加载审核记录...</div>
        <div v-else-if="!reviews.length" class="empty">暂无审核记录</div>
        <template v-else>
          <article v-for="record in reviews" :key="record.reviewId" class="review-record">
            <div>
              <strong>{{ decisionLabel(record.decision) }}</strong>
              <span>{{ record.stepId }} · {{ record.reviewer }}</span>
            </div>
            <time>{{ formatTime(record.createdAt) }}</time>
            <p v-if="record.comment">{{ record.comment }}</p>
          </article>
        </template>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { ReviewDecision, ReviewRecord, ReviewRequest, WorkflowRun } from '@/services/api/workflow'

const props = defineProps<{
  run: WorkflowRun | null
  reviews: ReviewRecord[]
  loading?: boolean
  submitting?: boolean
}>()

const emit = defineEmits<{
  submit: [payload: ReviewRequest]
}>()

const stepId = ref('')
const decision = ref<ReviewDecision>('approved')
const reviewer = ref(localStorage.getItem('userId') || 'console_reviewer')
const comment = ref('')

const canReview = computed(() => props.run?.status === 'waiting_review')

watch(
  () => props.run,
  run => {
    const preferred = run?.steps.find(step => step.status === 'waiting_review') || run?.steps.find(step => step.stepId === run.currentStepId)
    stepId.value = preferred?.stepId || run?.currentStepId || run?.steps[0]?.stepId || ''
    decision.value = 'approved'
    comment.value = ''
  },
  { immediate: true }
)

const submit = () => {
  if (!stepId.value) return
  emit('submit', {
    stepId: stepId.value,
    decision: decision.value,
    reviewer: reviewer.value || 'console_reviewer',
    comment: comment.value
  })
}

const decisionLabel = (value: ReviewDecision) => {
  const labels: Record<ReviewDecision, string> = {
    approved: '通过',
    rejected: '驳回',
    rerun: '重跑',
    cancelled: '取消'
  }
  return labels[value] || value
}

const formatTime = (value?: string) => {
  if (!value) return ''
  return new Date(value).toLocaleString()
}
</script>

<style scoped>
.human-review-panel {
  padding: 16px;
  border: 1px solid #dde4ef;
  border-radius: 8px;
  background: #fff;
}

.section-head,
.history-head,
.review-record > div:first-child {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.section-head {
  margin-bottom: 12px;
}

h3,
p {
  margin: 0;
}

h3 {
  color: #0f172a;
  font-size: 15px;
}

.section-head span,
.history-head span,
.empty,
time,
p {
  color: #64748b;
  font-size: 12px;
}

.section-head span.active {
  color: #b45309;
  font-weight: 700;
}

.review-form {
  display: grid;
  gap: 10px;
}

label {
  display: grid;
  gap: 5px;
}

label span {
  color: #334155;
  font-size: 12px;
  font-weight: 700;
}

select,
input,
textarea {
  width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #fff;
  color: #0f172a;
  font-size: 13px;
}

select,
input {
  height: 34px;
  padding: 0 9px;
}

textarea {
  min-height: 72px;
  padding: 9px;
  resize: vertical;
}

button {
  height: 34px;
  border: 0;
  border-radius: 6px;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
  font-weight: 700;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.review-history {
  display: grid;
  gap: 8px;
  margin-top: 16px;
}

.history-head strong,
.review-record strong {
  color: #111827;
  font-size: 13px;
}

.review-record {
  display: grid;
  gap: 6px;
  padding: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

.review-record span {
  color: #64748b;
  font-size: 12px;
}

p {
  overflow-wrap: anywhere;
}
</style>
