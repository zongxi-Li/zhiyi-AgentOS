<template>
  <div class="federated-model-management" :class="themeClass">
    <!-- 极简背景：动态纹理与环境光 -->
    <div class="bg-layer">
      <div class="ambient-glow"></div>
      <div class="noise-texture"></div>
    </div>

    <!-- 顶层：大气的 Editorial Style 头部 -->
    <div class="editorial-header">
      <div class="header-left">
        <div class="system-meta">
          <span class="version-tag">SYSTEM v2.5</span>
          <span class="status-indicator">
            <span class="dot"></span> ONLINE
          </span>
        </div>
        <h1 class="grand-title">Federated<br/>Intelligence</h1>
        <p class="tagline">大规模隐私保护下的模型协同进化系统</p>
      </div>
      
      <div class="header-right">
        <div class="header-tools">
          <div class="sync-status">
            <span class="time">{{ lastSyncTime }}</span>
            <span class="label">LAST UPDATED</span>
          </div>
          <div class="theme-toggle-art" @click="toggleTheme">
            <div class="toggle-inner" :class="{ 'is-dark': isDark }">
              <div class="toggle-circle">
                <el-icon v-if="isDark"><Moon /></el-icon>
                <el-icon v-else><Sunny /></el-icon>
              </div>
            </div>
          </div>
        </div>
        
        <div class="action-bar-top">
          <button class="minimal-btn back" @click="router.push('/chat')">
            <el-icon><ArrowLeft /></el-icon> BACK
          </button>
          <button class="primary-grand-btn" @click="refreshAll" :loading="refreshing">
            <el-icon><Refresh /></el-icon> SYNC CLUSTER
          </button>
        </div>
      </div>
    </div>

    <!-- 中层：极具氛围感的可视化大屏 -->
    <div class="grand-visualization">
      <div class="vis-hero">
        <FederatedNetworkVis :theme="isDark ? 'dark' : 'light'" />
      </div>
      
      <!-- 核心指标：大字重、极简设计 -->
      <div class="hero-stats">
        <div class="stat-group" v-for="(stat, index) in stats" :key="stat.label">
          <span class="stat-label">{{ stat.label }}</span>
          <span class="stat-value">{{ stat.value }}</span>
          <div class="stat-mini-chart" :class="`theme-${index}`"></div>
        </div>
      </div>
    </div>

    <!-- 下层：功能控制与网格展示 -->
    <div class="content-section-art">
      <div class="section-nav">
        <div class="category-list">
          <div 
            v-for="category in categories" 
            :key="category.key"
            class="category-btn"
            :class="{ active: activeCategory === category.key }"
            @click="switchCategory(category.key)"
          >
            {{ category.label }}
            <span class="count">{{ getCategoryCount(category.key) }}</span>
          </div>
        </div>
        
        <div class="privacy-summary">
          <el-icon><Lock /></el-icon>
          <span>ENCRYPTED END-TO-END</span>
        </div>
      </div>

      <!-- 模型网格：拒绝传统阴影，采用深度空间感 -->
      <div class="models-minimal-grid" v-if="Object.keys(currentModels).length > 0">
        <div 
          v-for="(model, key) in currentModels" 
          :key="key"
          class="model-art-entry"
        >
          <div class="entry-header">
            <div class="entry-title-row">
              <h3 class="name">{{ model.name }}</h3>
              <span class="status-pill" :class="model.status"></span>
            </div>
            <div class="entry-meta">
              <span>v{{ model.version }}</span>
              <span class="separator">/</span>
              <span>{{ getTypeLabel(model.type) }}</span>
            </div>
          </div>

          <div class="entry-visuals">
            <div class="metric-visual" v-for="(value, metric) in model.performance" :key="metric">
              <div class="vis-label-row">
                <span class="label">{{ getMetricLabel(metric) }}</span>
                <span class="value">{{ (value * 100).toFixed(0) }}%</span>
              </div>
              <div class="vis-track">
                <div class="vis-bar" :style="{ width: (value * 100) + '%' }" :class="metric"></div>
              </div>
            </div>
          </div>

          <div class="entry-actions">
            <button class="action-pill evaluate" @click="evaluateModel(key)">EVALUATE</button>
            <button class="action-pill optimize" @click="optimizeModel(key)" :disabled="isOptimizing(key)">
              {{ isOptimizing(key) ? 'SYNCING...' : 'OPTIMIZE' }}
            </button>
            <button class="icon-only-btn" @click="viewDetails(key)">
              <el-icon><View /></el-icon>
            </button>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div class="grand-empty" v-else>
        <div class="empty-icon-art"></div>
        <p>NO ACTIVE MODELS DETECTED</p>
      </div>
    </div>

    <!-- 对话框：同样追求极致质感 -->
    <el-dialog
      v-model="evaluationDialog.visible"
      title="Intelligence Report"
      width="800px"
      class="grand-art-dialog"
    >
      <div v-if="evaluationDialog.loading" class="grand-loading">
        <div class="loading-scanner"></div>
        <p>ANALYZING NEURAL WEIGHTS...</p>
      </div>
      <div v-else-if="evaluationDialog.result" class="report-grand-view">
        <div class="report-top">
          <div class="token">TOKEN: #{{ Math.floor(Math.random()*900000)+100000 }}</div>
          <div class="timestamp">{{ formatTime(evaluationDialog.result.evaluation_time) }}</div>
        </div>
        
        <div class="report-grid">
          <div class="report-card" v-for="(value, key) in evaluationDialog.result.metrics" :key="key">
            <span class="r-label">{{ getMetricLabel(key) }}</span>
            <span class="r-value">{{ formatMetricValue(key, value) }}</span>
            <div class="r-trend" v-if="key === 'accuracy' && evaluationDialog.result.comparison">
              <span :class="evaluationDialog.result.comparison.improvement > 0 ? 'up' : 'down'">
                {{ evaluationDialog.result.comparison.improvement > 0 ? '↑' : '↓' }} 
                {{ evaluationDialog.result.comparison.improvement_percentage.toFixed(1) }}%
              </span>
            </div>
          </div>
        </div>

        <div class="report-insights">
          <h4 class="insights-title">SYSTEM RECOMMENDATIONS</h4>
          <div class="insights-list">
            <div class="insight-row" v-for="(rec, idx) in evaluationDialog.result.recommendations" :key="idx">
              <span class="bullet"></span>
              <span class="text">{{ rec }}</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="grand-footer">
          <button class="grand-btn secondary" @click="evaluationDialog.visible = false">CLOSE</button>
          <button class="grand-btn primary" @click="startOptimization">INITIATE OPTIMIZATION</button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  Refresh, DataAnalysis, MagicStick, View, Loading,
  Box, InfoFilled, ArrowUp, ArrowDown, ArrowLeft,
  Lock, Cpu, CircleCheckFilled, Sunny, Moon
} from '@element-plus/icons-vue'
import { federatedModelApi, type ModelInfo } from '@/services/api/federatedModel'
import FederatedNetworkVis from '@/components/FederatedNetworkVis.vue'

const router = useRouter()

// 最后同步时间
const lastSyncTime = ref(new Date().toLocaleTimeString())

// 主题切换
const isDark = ref(true)
const toggleTheme = () => {
  isDark.value = !isDark.value
}
const themeClass = computed(() => isDark.value ? 'theme-dark' : 'theme-light')

// 统计数据
const stats = ref([
  { label: 'CONNECTED MODELS', value: '0' },
  { label: 'OPTIMIZED INSTANCES', value: '0' },
  { label: 'ACTIVE NODES', value: '1,248' },
  { label: 'AVG ACCURACY', value: '0%' }
])

const refreshing = ref(false)

// 分类标签
const categories = [
  { key: 'text_generation', label: 'GEN-TEXT' },
  { key: 'digital_human', label: 'AVATAR' },
  { key: 'emotion_recognition', label: 'EMOTION' }
]

const activeCategory = ref('text_generation')

// 模型数据
const models = ref<Record<string, Record<string, ModelInfo>>>({})
const optimizing = ref<Record<string, boolean>>({})

const currentModels = computed(() => {
  return models.value[activeCategory.value] || {}
})

const getCategoryCount = (categoryKey: string) => {
  return Object.keys(models.value[categoryKey] || {}).length
}

const switchCategory = (key: string) => {
  activeCategory.value = key
}

const getTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    'fast': 'FAST',
    'balanced': 'BALANCED',
    'advanced': 'PRO',
    'avatar': 'IMG',
    'animation': 'VID'
  }
  return labels[type] || type
}

const getMetricLabel = (metric: string) => {
  const labels: Record<string, string> = {
    'accuracy': 'ACCURACY',
    'speed': 'SPEED',
    'efficiency': 'EFFICIENCY',
    'response_time': 'LATENCY',
    'success_rate': 'SUCCESS',
    'throughput': 'THROUGHPUT',
    'resource_usage': 'MEMORY',
    'cost_per_request': 'COST'
  }
  return labels[metric] || metric
}

const formatMetricValue = (key: string, value: number) => {
  if (key === 'accuracy' || key === 'success_rate' || key === 'resource_usage') {
    return (value * 100).toFixed(1) + '%'
  } else if (key === 'response_time') {
    return value.toFixed(2) + 's'
  }
  return value.toString()
}

const formatTime = (timeStr: string) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleTimeString('en-US', { hour12: false })
}

// 评估对话框
const evaluationDialog = ref({
  visible: false,
  loading: false,
  result: null as any,
  modelKey: ''
})

// 优化对话框
const optimizationDialog = ref({
  visible: false,
  loading: false,
  modelKey: ''
})

const optimizationForm = ref({
  method: 'federated',
  target: 'quality',
  epochs: 10
})

// 详情对话框
const detailsDialog = ref({
  visible: false,
  loading: false,
  modelName: '',
  data: null as any
})

// 加载模型列表
const loadModels = async () => {
  try {
    const response = await federatedModelApi.listModels()
    if (response.success) {
      models.value = response.data
      updateStats()
      lastSyncTime.value = new Date().toLocaleTimeString()
    }
  } catch (e: any) {
    ElMessage.error('Failed to sync model cluster')
  }
}

// 更新统计数据
const updateStats = () => {
  let total = 0
  let optimized = 0
  let totalAccuracy = 0
  let accuracyCount = 0

  Object.values(models.value).forEach(category => {
    Object.values(category).forEach((model: any) => {
      total++
      if (model.optimized) optimized++
      if (model.performance?.accuracy) {
        totalAccuracy += model.performance.accuracy
        accuracyCount++
      }
    })
  })

  stats.value[0].value = total.toString()
  stats.value[1].value = optimized.toString()
  stats.value[3].value = accuracyCount > 0 
    ? (totalAccuracy / accuracyCount * 100).toFixed(1) + '%'
    : '0.0%'
}

// 评估模型
const evaluateModel = async (modelKey: string) => {
  const category = activeCategory.value
  const model = models.value[category]?.[modelKey]
  if (!model) return

  evaluationDialog.value.visible = true
  evaluationDialog.value.loading = true
  evaluationDialog.value.modelKey = modelKey
  evaluationDialog.value.result = null

  try {
    const response = await federatedModelApi.evaluateModel(model.type)
    if (response.success) {
      evaluationDialog.value.result = response.data
    }
  } finally {
    evaluationDialog.value.loading = false
  }
}

// 优化模型
const optimizeModel = (modelKey: string) => {
  const category = activeCategory.value
  const model = models.value[category]?.[modelKey]
  if (!model) return

  optimizationDialog.value.modelKey = modelKey
  confirmOptimization() // 直接执行优化（简约化流程）
}

// 检查是否正在优化
const isOptimizing = (modelKey: string) => {
  const key = `${activeCategory.value}_${modelKey}`
  return optimizing.value[key] || false
}

// 确认优化
const confirmOptimization = async () => {
  const category = activeCategory.value
  const modelKey = optimizationDialog.value.modelKey
  const model = models.value[category]?.[modelKey]
  if (!model) return

  const key = `${category}_${modelKey}`
  optimizing.value[key] = true

  try {
    const response = await federatedModelApi.optimizeModel(
      model.type,
      optimizationForm.value.method,
      optimizationForm.value.target,
      optimizationForm.value.epochs
    )
    if (response.success) {
      ElMessage.success('Cluster optimized successfully')
      await loadModels()
    }
  } finally {
    optimizing.value[key] = false
  }
}

// 查看详情
const viewDetails = async (modelKey: string) => {
  const category = activeCategory.value
  const model = models.value[category]?.[modelKey]
  if (!model) return
  // 详情逻辑简化
}

// 开始优化（从评估对话框）
const startOptimization = () => {
  evaluationDialog.value.visible = false
  optimizeModel(evaluationDialog.value.modelKey)
}

// 刷新所有数据
const refreshAll = async () => {
  refreshing.value = true
  try {
    await loadModels()
    ElMessage.success('Cluster synchronized')
  } finally {
    refreshing.value = false
  }
}

onMounted(() => {
  loadModels()
})
</script>

<style scoped lang="scss">
/* --- 极简质感：主题定义 --- */
.federated-model-management {
  --bg-color: #050505;
  --text-primary: #ffffff;
  --text-secondary: rgba(255, 255, 255, 0.4);
  --accent: #6366f1;
  --border: rgba(255, 255, 255, 0.06);
  --glass: rgba(255, 255, 255, 0.02);
  --btn-hover: rgba(255, 255, 255, 0.08);
  
  &.theme-light {
    --bg-color: #fcfcfc;
    --text-primary: #111111;
    --text-secondary: #666666;
    --accent: #000000;
    --border: rgba(0, 0, 0, 0.05);
    --glass: rgba(0, 0, 0, 0.01);
    --btn-hover: rgba(0, 0, 0, 0.04);
  }

  position: relative;
  min-height: 100vh;
  padding: 60px 80px;
  background: var(--bg-color);
  color: var(--text-primary);
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  overflow-x: hidden;
}

/* --- 动态氛围层 --- */
.bg-layer {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;

  .ambient-glow {
    position: absolute;
    top: -10%;
    right: -10%;
    width: 60%;
    height: 60%;
    background: radial-gradient(circle, var(--accent) 0%, transparent 70%);
    opacity: 0.05;
    filter: blur(100px);
  }

  .noise-texture {
    position: absolute;
    inset: 0;
    opacity: 0.02;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  }
}

/* --- Editorial Header: 大气排版 --- */
.editorial-header {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 80px;

  .system-meta {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 24px;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 2px;
    
    .version-tag { color: var(--accent); }
    .status-indicator {
      display: flex;
      align-items: center;
      gap: 6px;
      color: var(--text-secondary);
      .dot { width: 4px; height: 4px; background: #10b981; border-radius: 50%; box-shadow: 0 0 8px #10b981; }
    }
  }

  .grand-title {
    font-size: 80px;
    font-weight: 800;
    line-height: 0.9;
    letter-spacing: -4px;
    margin: 0 0 16px 0;
    text-transform: uppercase;
  }

  .tagline {
    font-size: 16px;
    color: var(--text-secondary);
    font-weight: 500;
  }

  .header-tools {
    display: flex;
    align-items: center;
    gap: 40px;
    margin-bottom: 40px;
    
    .sync-status {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      .time { font-size: 14px; font-weight: 800; font-family: 'JetBrains Mono'; }
      .label { font-size: 9px; font-weight: 900; color: var(--text-secondary); letter-spacing: 1px; }
    }
  }

  /* 主题切换开关 - 艺术感 */
  .theme-toggle-art {
    width: 64px;
    height: 32px;
    background: var(--border);
    border-radius: 20px;
    padding: 4px;
    cursor: pointer;
    .toggle-inner {
      width: 100%;
      height: 100%;
      position: relative;
      .toggle-circle {
        position: absolute;
        left: 0;
        width: 24px;
        height: 24px;
        background: var(--text-primary);
        color: var(--bg-color);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
      }
      &.is-dark .toggle-circle { transform: translateX(32px); }
    }
  }

  .action-bar-top {
    display: flex;
    gap: 16px;
    
    .minimal-btn {
      height: 54px;
      padding: 0 24px;
      background: transparent;
      border: 1px solid var(--border);
      color: var(--text-primary);
      border-radius: 16px;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 1px;
      cursor: pointer;
      transition: all 0.3s;
      &:hover { background: var(--btn-hover); border-color: var(--text-secondary); }
    }

    .primary-grand-btn {
      height: 54px;
      padding: 0 32px;
      background: var(--accent);
      color: #fff;
      border: none;
      border-radius: 16px;
      font-size: 12px;
      font-weight: 900;
      letter-spacing: 1px;
      cursor: pointer;
      box-shadow: 0 10px 30px rgba(0,0,0,0.1);
      display: flex;
      align-items: center;
      gap: 12px;
      transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      &:hover { transform: translateY(-4px); filter: brightness(1.1); }
    }
  }
}

/* --- 大屏核心可视化 --- */
.grand-visualization {
  position: relative;
  z-index: 1;
  margin-bottom: 100px;
  
  .vis-hero {
    background: var(--glass);
    border: 1px solid var(--border);
    border-radius: 48px;
    backdrop-filter: blur(20px);
    overflow: hidden;
  }

  .hero-stats {
    display: flex;
    justify-content: space-between;
    padding: 60px 40px 0;
    
    .stat-group {
      display: flex;
      flex-direction: column;
      gap: 8px;
      flex: 1;
      
      .stat-label { font-size: 10px; font-weight: 900; color: var(--text-secondary); letter-spacing: 2px; }
      .stat-value { font-size: 48px; font-weight: 800; letter-spacing: -2px; }
      .stat-mini-chart {
        width: 60px;
        height: 2px;
        background: var(--border);
        margin-top: 16px;
        position: relative;
        &::after {
          content: ''; position: absolute; left: 0; top: 0; width: 40%; height: 100%;
          background: var(--accent);
        }
      }
    }
  }
}

/* --- 功能区与网格 --- */
.content-section-art {
  position: relative;
  z-index: 1;

  .section-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 48px;
    
    .category-list {
      display: flex;
      gap: 12px;
      .category-btn {
        padding: 12px 28px;
        border-radius: 14px;
        font-size: 12px;
        font-weight: 900;
        letter-spacing: 1px;
        color: var(--text-secondary);
        cursor: pointer;
        transition: all 0.3s;
        border: 1px solid transparent;
        &:hover { color: var(--text-primary); }
        &.active {
          color: var(--text-primary);
          background: var(--glass);
          border-color: var(--border);
        }
        .count { font-size: 10px; opacity: 0.4; margin-left: 8px; }
      }
    }

    .privacy-summary {
      font-size: 10px;
      font-weight: 900;
      color: var(--text-secondary);
      display: flex;
      align-items: center;
      gap: 10px;
      letter-spacing: 1.5px;
    }
  }
}

.models-minimal-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 40px;
}

.model-art-entry {
  padding: 40px;
  background: var(--glass);
  border: 1px solid var(--border);
  border-radius: 36px;
  transition: all 0.5s cubic-bezier(0.2, 0.8, 0.2, 1);
  
  &:hover {
    background: var(--btn-hover);
    border-color: var(--text-secondary);
    transform: translateY(-8px);
  }

  .entry-header {
    margin-bottom: 32px;
    .entry-title-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      .name { font-size: 20px; font-weight: 800; letter-spacing: -0.5px; }
      .status-pill { width: 6px; height: 6px; border-radius: 50%; background: #10b981; }
    }
    .entry-meta { font-size: 11px; font-weight: 700; color: var(--text-secondary); letter-spacing: 1px; }
  }

  .entry-visuals {
    display: flex;
    flex-direction: column;
    gap: 20px;
    margin-bottom: 40px;
    
    .metric-visual {
      .vis-label-row {
        display: flex; justify-content: space-between; font-size: 11px; font-weight: 800;
        margin-bottom: 8px;
        .label { color: var(--text-secondary); letter-spacing: 0.5px; }
      }
      .vis-track {
        height: 2px; background: var(--border); overflow: hidden;
        .vis-bar {
          height: 100%; background: var(--text-primary);
          transition: width 1.5s cubic-bezier(0.22, 1, 0.36, 1);
          &.accuracy { background: var(--accent); }
        }
      }
    }
  }

  .entry-actions {
    display: flex;
    gap: 12px;
    .action-pill {
      height: 40px; padding: 0 20px; border-radius: 12px; border: 1px solid var(--border);
      background: transparent; color: var(--text-primary); font-size: 10px; font-weight: 900;
      letter-spacing: 1px; cursor: pointer; transition: all 0.3s;
      &:hover { background: var(--text-primary); color: var(--bg-color); }
      &.optimize { background: var(--accent); color: white; border: none; }
    }
    .icon-only-btn {
      width: 40px; height: 40px; border-radius: 12px; border: 1px solid var(--border);
      background: transparent; color: var(--text-secondary); cursor: pointer;
      &:hover { color: var(--text-primary); border-color: var(--text-secondary); }
    }
  }
}

/* --- 艺术对话框 --- */
.grand-art-dialog {
  :deep(.el-dialog) {
    background: var(--bg-color);
    border-radius: 40px;
    padding: 60px;
    border: 1px solid var(--border);
    box-shadow: 0 100px 200px rgba(0,0,0,0.4);
  }
  :deep(.el-dialog__header) { padding: 0; margin-bottom: 40px; .el-dialog__title { font-size: 32px; font-weight: 800; letter-spacing: -1.5px; } }

  .report-top {
    display: flex; justify-content: space-between; margin-bottom: 40px;
    font-size: 11px; font-weight: 900; color: var(--text-secondary); letter-spacing: 1px;
  }

  .report-grid {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-bottom: 60px;
    .report-card {
      padding: 32px; background: var(--glass); border: 1px solid var(--border); border-radius: 24px;
      .r-label { display: block; font-size: 10px; font-weight: 900; color: var(--text-secondary); margin-bottom: 12px; }
      .r-value { font-size: 32px; font-weight: 800; letter-spacing: -1px; }
    }
  }

  .report-insights {
    .insights-title { font-size: 12px; font-weight: 900; letter-spacing: 2px; margin-bottom: 24px; opacity: 0.6; }
    .insights-list {
      display: flex; flex-direction: column; gap: 16px;
      .insight-row {
        display: flex; align-items: center; gap: 16px; font-size: 14px; font-weight: 500;
        .bullet { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); }
      }
    }
  }

  .grand-footer {
    display: flex; justify-content: flex-end; gap: 16px; margin-top: 60px;
    .grand-btn {
      height: 54px; padding: 0 32px; border-radius: 16px; font-size: 12px; font-weight: 900; letter-spacing: 1px; cursor: pointer; transition: all 0.3s;
      &.secondary { background: transparent; border: 1px solid var(--border); color: var(--text-primary); }
      &.primary { background: var(--accent); border: none; color: white; }
    }
  }
}

.grand-loading {
  padding: 80px 0; text-align: center;
  .loading-scanner {
    width: 60px; height: 2px; background: var(--accent); margin: 0 auto 32px;
    animation: scan-move 2s infinite;
  }
  p { font-size: 12px; font-weight: 900; letter-spacing: 2px; opacity: 0.5; }
}

@keyframes scan-move {
  0%, 100% { transform: scaleX(0.5); opacity: 0.2; }
  50% { transform: scaleX(2); opacity: 1; }
}

@keyframes status-pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.8); opacity: 0.3; }
  100% { transform: scale(1); opacity: 1; }
}

@media (max-width: 1200px) {
  .editorial-header .grand-title { font-size: 60px; }
  .dashboard-vis-container { grid-template-columns: 1fr; }
}
</style>
