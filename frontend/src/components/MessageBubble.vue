<!-- 消息展示组件 — 用户使用紧凑气泡，助手使用无边框阅读流 -->
<template>
  <div v-if="message && message.role && message.content !== undefined" :class="['message-bubble', message.role]">
    <div class="message-content-wrapper">
      <div class="message-content">
        <!-- 文件展示 -->
        <div v-if="message.fileUrl" class="message-file">
          <div
            v-if="isImage(message.fileUrl)"
            class="message-image-wrapper"
            @click="openImageViewer"
          >
            <img :src="message.fileUrl" class="message-image" />
            <div class="image-overlay">
              <el-icon><FullScreen /></el-icon>
            </div>
          </div>
          <div v-else class="file-attachment">
            <el-icon><Document /></el-icon>
            <div class="file-info">
              <span class="filename">附件文件</span>
              <a :href="message.fileUrl" target="_blank" class="download-link">下载</a>
            </div>
          </div>
        </div>

        <ImageViewer
          v-model:visible="imageViewerVisible"
          :src="message.fileUrl"
          :file-name="'image.png'"
        />

        <!-- 文本内容 -->
        <div
          v-if="message.content"
          class="message-text markdown-body"
          v-html="renderedMessageHtml"
        />
        
        <!-- 可解释性信息（仅AI回复显示） -->
        <div v-if="message.role === 'assistant' && hasExplanation" class="message-explanation">
          <el-collapse v-model="activeCollapse" class="explanation-collapse">
            <el-collapse-item name="explanation">
              <template #title>
                <div class="explanation-toggle">
                  <el-icon><InfoFilled /></el-icon>
                  <span>AI 思考过程与详情</span>
                </div>
              </template>
              
              <!-- 置信度 -->
              <div v-if="message.confidence" class="explanation-item">
                <span class="explanation-label">置信度</span>
                <div class="explanation-value-row">
                  <el-progress
                    :percentage="(message.confidence * 100)"
                    :color="getConfidenceColor(message.confidence)"
                    :stroke-width="6"
                    :show-text="false"
                    style="width: 100px;"
                  />
                  <span class="value-text">{{ (message.confidence * 100).toFixed(1) }}%</span>
                </div>
              </div>
              
              <!-- Token使用 -->
              <div v-if="message.tokensUsed" class="explanation-item">
                <span class="explanation-label">消耗</span>
                <span class="explanation-value">{{ message.tokensUsed }} tokens</span>
              </div>
              
              <!-- 答案来源（RAG） -->
              <div v-if="message.sources && message.sources.length > 0" class="explanation-item vertical">
                <span class="explanation-label">参考来源</span>
                <div class="sources-list">
                  <div
                    v-for="(source, index) in message.sources"
                    :key="index"
                    class="source-tag"
                  >
                    <el-icon><Link /></el-icon>
                    {{ source.title || source.filename || `来源 ${index + 1}` }}
                  </div>
                </div>
              </div>
              
              <!-- 推理路径 -->
              <div v-if="message.reasoningPath" class="explanation-item vertical">
                <span class="explanation-label">推理路径</span>
                <div class="reasoning-path">
                  <div v-for="(step, index) in message.reasoningPath" :key="index" class="reasoning-step">
                    <div class="step-dot"></div>
                    <div class="step-content">
                      <div class="step-title">{{ step.title }}</div>
                      <div class="step-desc">{{ step.description }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
      </div>

      <!-- Message Actions Area -->
      <div class="message-actions">
        <el-tooltip content="复制" placement="top">
          <div class="action-item" @click="handleAction('copy')"><el-icon><CopyDocument /></el-icon></div>
        </el-tooltip>
        <el-tooltip content="引用" placement="top">
          <div class="action-item" @click="handleAction('quote')"><el-icon><ChatLineSquare /></el-icon></div>
        </el-tooltip>
        <el-tooltip content="生成语音" placement="top">
          <div class="action-item" @click="handleAction('tts')"><el-icon><Microphone /></el-icon></div>
        </el-tooltip>
        <el-tooltip content="导出" placement="top">
          <div class="action-item" @click="handleAction('export')"><el-icon><Download /></el-icon></div>
        </el-tooltip>
        <el-tooltip content="删除" placement="top">
          <div class="action-item delete" @click="handleAction('delete')"><el-icon><Delete /></el-icon></div>
        </el-tooltip>
        <span class="message-action-time">{{ formatTime(message.createdAt) }}</span>
      </div>
    </div>
  </div>
  <div v-else class="message-bubble error">
    <div class="message-content">
      <div class="message-text">消息数据无效</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Document, InfoFilled, Link, CopyDocument, ChatLineSquare, Delete, Microphone, Download, FullScreen } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ImageViewer from '@/components/common/ImageViewer.vue'

interface Source {
  title?: string
  filename?: string
  url?: string
  content?: string
}

interface ReasoningStep {
  title: string
  description: string
}

interface Props {
  message: {
    id: number | string
    role: 'user' | 'assistant'
    content: string
    createdAt: Date
    confidence?: number
    fileUrl?: string
    tokensUsed?: number
    sources?: Source[]
    reasoningPath?: ReasoningStep[]
    modelInfo?: string
  }
}

const props = defineProps<Props>()
const emit = defineEmits(['copy', 'quote', 'delete', 'tts', 'export'])
const activeCollapse = ref<string[]>([])
const imageViewerVisible = ref(false)

const openImageViewer = () => {
  imageViewerVisible.value = true
}

const handleAction = (type: 'copy' | 'quote' | 'delete' | 'tts' | 'export') => {
  if (type === 'copy') {
    navigator.clipboard.writeText(props.message.content)
    ElMessage.success('已复制到剪贴板')
  } else if (type === 'delete') {
    ElMessageBox.confirm('确定要删除这条消息吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      emit('delete', props.message.id)
    }).catch(() => {})
  } else {
    emit(type, props.message)
  }
}

const escapeHtml = (raw: string) => {
  return raw
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

const escapeAttr = (raw: string) => raw.replace(/"/g, '&quot;')

const isSafeUrl = (url: string) => /^(https?:\/\/|mailto:|\/)/i.test(url)

const applyInlineMarkdown = (value: string) => {
  let text = value
  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_all, label, url) => {
    const safe = String(url || '').trim()
    if (!isSafeUrl(safe)) return label
    return `<a href="${escapeAttr(safe)}" target="_blank" rel="noopener noreferrer">${label}</a>`
  })
  text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  text = text.replace(/`([^`]+)`/g, '<code>$1</code>')
  return text
}

const markdownToHtml = (raw: string) => {
  if (!raw) return ''

  const codeBlocks: string[] = []
  const stripped = raw.replace(/```([a-zA-Z0-9_-]+)?\n?([\s\S]*?)```/g, (_m, lang, code) => {
    const language = (lang || '').trim()
    const escapedCode = escapeHtml(String(code || '').replace(/\n$/, ''))
    const className = language ? ` class="language-${escapeAttr(language)}"` : ''
    const token = `@@CODE_BLOCK_${codeBlocks.length}@@`
    codeBlocks.push(`<pre><code${className}>${escapedCode}</code></pre>`)
    return token
  })

  const lines = stripped.split(/\r?\n/)
  const output: string[] = []
  let inUl = false
  let inOl = false

  const closeLists = () => {
    if (inUl) {
      output.push('</ul>')
      inUl = false
    }
    if (inOl) {
      output.push('</ol>')
      inOl = false
    }
  }

  lines.forEach((line) => {
    const trimmed = line.trim()
    if (!trimmed) {
      closeLists()
      return
    }

    if (/^@@CODE_BLOCK_\d+@@$/.test(trimmed)) {
      closeLists()
      output.push(trimmed)
      return
    }

    const escaped = escapeHtml(trimmed)
    const heading = escaped.match(/^(#{1,6})\s+(.+)$/)
    if (heading) {
      closeLists()
      const level = Math.min(6, heading[1].length)
      output.push(`<h${level}>${applyInlineMarkdown(heading[2])}</h${level}>`)
      return
    }

    const ul = escaped.match(/^[-*]\s+(.+)$/)
    if (ul) {
      if (!inUl) {
        closeLists()
        output.push('<ul>')
        inUl = true
      }
      output.push(`<li>${applyInlineMarkdown(ul[1])}</li>`)
      return
    }

    const ol = escaped.match(/^\d+\.\s+(.+)$/)
    if (ol) {
      if (!inOl) {
        closeLists()
        output.push('<ol>')
        inOl = true
      }
      output.push(`<li>${applyInlineMarkdown(ol[1])}</li>`)
      return
    }

    closeLists()
    output.push(`<p>${applyInlineMarkdown(escaped)}</p>`)
  })

  closeLists()
  let html = output.join('\n')
  codeBlocks.forEach((block, index) => {
    html = html.replace(`@@CODE_BLOCK_${index}@@`, block)
  })
  return html
}

const renderedMessageHtml = computed(() => {
  const content = props.message.content || ''
  if (!content) return ''
  if (props.message.role === 'assistant') return markdownToHtml(content)
  return escapeHtml(content).replace(/\n/g, '<br />')
})

const hasExplanation = computed(() => {
  return !!(
    props.message.confidence ||
    props.message.tokensUsed ||
    (props.message.sources && props.message.sources.length > 0) ||
    (props.message.reasoningPath && props.message.reasoningPath.length > 0) ||
    props.message.modelInfo
  )
})

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return 'var(--success)'
  if (confidence >= 0.6) return 'var(--warning)'
  return 'var(--danger)'
}

const isImage = (url: string) => {
  const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
  return imageExtensions.some(ext => url.toLowerCase().includes(ext))
}

const formatTime = (date: Date) => {
  const d = new Date(date)
  return d.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped lang="scss">
.message-bubble {
  width: 100%;
  display: flex;
  justify-content: center;
  box-sizing: border-box;
  margin: 0;
  animation: fadeIn 180ms var(--ease-out);
  padding: 0 28px;
}

.message-bubble.user {
  justify-content: flex-end;
}

.message-content-wrapper {
  width: min(100%, 780px);
  max-width: 100%;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.message-bubble.user .message-content-wrapper {
  width: auto;
  max-width: min(72%, 560px);
  align-items: flex-end;
}

.message-content {
  padding: 0;
  border-radius: 0;
  word-wrap: break-word;
  line-height: 1.75;
  font-size: 15.5px;
  position: relative;
  transition: var(--transition);
}

.message-bubble.user .message-content {
  padding: 9px 14px;
  border: 1px solid var(--border-light);
  border-radius: 18px;
  background: var(--bg-panel);
  color: var(--text-primary);
  box-shadow: none;
}

.message-bubble.assistant .message-content {
  background: transparent;
  color: var(--text-primary);
  border: 0;
  border-radius: 0;
  box-shadow: none;
}

/* System/History Messages (Placeholder for role='system') */
.message-bubble.system {
  justify-content: center;
  margin: 16px 0;
}
.message-bubble.system .message-content {
  background-color: var(--bg-input);
  color: var(--text-secondary);
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 8px;
  border: none;
  box-shadow: none;
}
.message-bubble.system .message-avatar, 
.message-bubble.system .message-meta {
  display: none;
}

/* Error Message Style */
.message-bubble.error {
  justify-content: center;
  margin: 16px 0;
}
.message-bubble.error .message-content {
  background-color: rgba(178, 74, 74, 0.08);
  color: var(--danger);
  font-size: 13px;
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid rgba(178, 74, 74, 0.18);
}
.message-bubble.error .message-avatar, 
.message-bubble.error .message-meta {
  display: none;
}

/* Message Actions Area */
.message-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-top: 7px;
  padding: 0;
  opacity: 0.62;
  transition: opacity 0.2s;
}

/* 保持悬停效果，但不再控制显示/隐藏 */
.message-bubble:hover .message-actions,
.message-actions:focus-within {
  opacity: 1;
}

.message-bubble.user .message-actions {
  justify-content: flex-end;
}

.action-item {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  cursor: pointer;
  color: var(--text-disabled);
  transition: var(--transition);
  background: transparent;
}

.action-item:hover {
  background: var(--bg-panel);
  color: var(--text-primary);
  transform: none;
}

.action-item.delete:hover {
  color: var(--danger);
}

.action-item .el-icon {
  font-size: 14px;
}

.message-bubble.user .action-item {
  color: var(--text-disabled);
  background: transparent;
}

.message-bubble.user .action-item:hover {
  color: var(--text-primary);
  background: var(--bg-panel);
}

.message-action-time {
  margin-left: 6px;
  color: var(--text-disabled);
  font-size: 10px;
  white-space: nowrap;
}

.message-bubble.user .message-action-time {
  order: -1;
  margin: 0 6px 0 0;
}

/* File Attachments */
.message-image-wrapper {
  position: relative;
  display: inline-block;
  cursor: zoom-in;
  border-radius: 8px;
  overflow: hidden;
}

.message-image {
  max-width: 100%;
  border-radius: 8px;
  border: 1px solid var(--border-light);
  display: block;
}

.image-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0);
  transition: background 0.2s ease;
  border-radius: 8px;
  opacity: 0;
  transition: all 0.2s ease;
}

.message-image-wrapper:hover .image-overlay {
  background: rgba(29, 36, 34, 0.24);
  opacity: 1;
}

.image-overlay .el-icon {
  color: #fff;
  font-size: 20px;
}

.file-attachment {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: color-mix(in srgb, var(--bg-card) 72%, transparent);
  border: 1px solid var(--border-light);
  border-radius: 8px;
}

.message-bubble.assistant .file-attachment {
  background: var(--bg-input);
  border-color: var(--border-light);
}

.message-text {
  white-space: pre-wrap;
}

.message-text.markdown-body {
  white-space: normal;
  line-height: 1.78;
}

.message-text.markdown-body :deep(h1),
.message-text.markdown-body :deep(h2),
.message-text.markdown-body :deep(h3),
.message-text.markdown-body :deep(h4),
.message-text.markdown-body :deep(h5),
.message-text.markdown-body :deep(h6) {
  margin: 8px 0;
  line-height: 1.4;
  font-weight: 700;
}

.message-text.markdown-body :deep(h1) { font-size: 20px; }
.message-text.markdown-body :deep(h2) { font-size: 18px; }
.message-text.markdown-body :deep(h3) { font-size: 16px; }

.message-text.markdown-body :deep(p) {
  margin: 0 0 12px;
}

.message-text.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.message-text.markdown-body :deep(ul),
.message-text.markdown-body :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.message-text.markdown-body :deep(li) {
  margin: 4px 0;
}

.message-text.markdown-body :deep(pre) {
  margin: 10px 0;
  padding: 10px 12px;
  border-radius: 8px;
  background: #20262b;
  color: #eef1ef;
  overflow-x: auto;
}

.message-text.markdown-body :deep(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  padding: 0 4px;
  border-radius: 4px;
  background: color-mix(in srgb, var(--primary-color) 12%, transparent);
}

.message-text.markdown-body :deep(pre code) {
  background: transparent;
  padding: 0;
}

.message-text.markdown-body :deep(a) {
  color: var(--primary-color);
  text-decoration: underline;
  word-break: break-all;
}

/* Explanation Section */
.message-explanation {
  margin-top: 12px;
  border-top: 1px solid rgba(29, 36, 34, 0.06);
  padding-top: 8px;
}

.message-bubble.user .message-explanation {
  border-top-color: rgba(255,255,255,0.18);
}

.explanation-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  
  &:hover {
    color: var(--primary-color);
  }
}

.explanation-collapse {
  --el-collapse-header-height: 32px;
  --el-collapse-border-color: transparent;
  
  :deep(.el-collapse-item__header) {
    background: transparent;
    border: none;
    font-size: 13px;
  }
  
  :deep(.el-collapse-item__content) {
    background: transparent;
    padding-bottom: 0;
  }
}

.explanation-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 12px;
  font-size: 13px;
  
  &.vertical {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }
}

.explanation-label {
  color: var(--text-secondary);
  font-weight: 500;
  min-width: 60px;
}

.explanation-value-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.value-text {
  font-size: 12px;
  color: var(--text-regular);
}

.source-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background-color: var(--bg-input);
  border-radius: 4px;
  font-size: 12px;
  color: var(--text-regular);
  margin-right: 4px;
  margin-bottom: 4px;
  border: 1px solid var(--border-light);
}

.reasoning-path {
  padding-left: 8px;
  border-left: 2px solid var(--border-color-light);
  margin-left: 4px;
}

.reasoning-step {
  position: relative;
  padding-bottom: 12px;
  padding-left: 12px;
  
  &:last-child {
    padding-bottom: 0;
  }
  
  .step-dot {
    position: absolute;
    left: -5px;
    top: 6px;
    width: 8px;
    height: 8px;
    background-color: var(--border-color-base);
    border-radius: 50%;
  }
  
  .step-title {
    font-weight: 500;
    font-size: 13px;
    color: var(--text-color-primary);
  }
  
  .step-desc {
    font-size: 12px;
    color: var(--text-color-secondary);
    margin-top: 2px;
  }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
