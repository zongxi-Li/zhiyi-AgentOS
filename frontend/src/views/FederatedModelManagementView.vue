<template>
  <div class="federated-model-management" :class="themeClass">
    <!-- 极高保真背景层 -->
    <div class="cinematic-bg">
      <div class="gradient-wash"></div>
      <div class="spatial-dust">
        <div v-for="i in 30" :key="i" class="dust-particle"></div>
      </div>
      <div class="radial-vignette"></div>
    </div>

    <!-- 顶部社论式导航 -->
    <header class="studio-header">
      <div class="brand-nexus">
        <button class="minimal-back" @click="router.push('/chat')">
          <el-icon><ArrowLeft /></el-icon>
        </button>
        <div class="brand-divider"></div>
        <div class="title-group">
          <h1>FEDERATED INTELLIGENCE</h1>
          <p>Autonomous Model Evolution & Cluster Synchronizer</p>
        </div>
      </div>
      
      <div class="status-matrix">
        <div class="matrix-unit">
          <span class="m-label">NETWORK_STATUS</span>
          <span class="m-value status-online">
            <span class="dot"></span> SECURE_ACTIVE
          </span>
        </div>
        <div class="matrix-unit">
          <span class="m-label">SYSTEM_CORE</span>
          <span class="m-value">V2.5.0_STABLE</span>
        </div>
        <div class="theme-switch-art" @click="toggleTheme">
          <el-icon v-if="isDark"><Moon /></el-icon>
          <el-icon v-else><Sunny /></el-icon>
        </div>
      </div>
    </header>

    <!-- 核心 Hero 可视化区域 -->
    <main class="dashboard-hero">
      <div class="vis-canvas-wrap">
        <FederatedNetworkVis :theme="isDark ? 'dark' : 'light'" />
        
        <!-- 悬浮在可视化之上的核心摘要 -->
        <div class="floating-insight">
          <div class="insight-block">
            <span class="i-val">1,248</span>
            <span class="i-lbl">TOTAL_ACTIVE_NODES</span>
          </div>
          <div class="insight-divider"></div>
          <div class="insight-block">
            <span class="i-val accent">91.7%</span>
            <span class="i-lbl">CLUSTER_PRECISION</span>
          </div>
        </div>
      </div>

      <!-- 核心指标：极简但强有力的视觉 -->
      <div class="pro-metrics-bar">
        <div class="metric-glass-card" v-for="(stat, index) in stats" :key="stat.label">
          <div class="card-inner">
            <span class="label">{{ stat.label }}</span>
            <div class="value-box">
              <span class="value">{{ stat.value }}</span>
              <div class="mini-trend" :class="{ up: index === 3 }">
                <el-icon v-if="index === 3"><Top /></el-icon>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 下层：功能控制与模型管理 -->
    <section class="management-layers">
      <div class="controls-integrated">
        <div class="custom-tab-system">
          <button 
            v-for="cat in categories" 
            :key="cat.key"
            class="tab-pill"
            :class="{ active: activeCategory === cat.key }"
            @click="switchCategory(cat.key)"
          >
            <span class="t-text">{{ cat.label }}</span>
            <span class="t-count">{{ getCategoryCount(cat.key) }}</span>
          </button>
        </div>
        
        <div class="global-actions">
          <div class="sync-timestamp">SYNCED: {{ lastSyncTime }}</div>
          <button class="pro-sync-btn" @click="refreshAll" :disabled="refreshing">
            <el-icon :class="{ 'is-loading': refreshing }"><Refresh /></el-icon>
            <span>SYNC CLUSTER DATA</span>
          </button>
        </div>
      </div>

      <!-- 模型网格：拒绝陈旧，采用高级质感 -->
      <div class="art-model-grid" v-if="Object.keys(currentModels).length > 0">
        <div 
          v-for="(model, key) in currentModels" 
          :key="key"
          class="art-model-card"
        >
          <div class="card-content">
            <div class="card-top">
              <div class="name-area">
                <h3>{{ model.name }}</h3>
                <span class="rev">REV_{{ model.version }}</span>
              </div>
              <div class="type-pill">{{ getTypeLabel(model.type) }}</div>
            </div>

            <div class="performance-visual">
              <div class="p-row" v-for="(value, metric) in model.performance" :key="metric">
                <span class="p-label">{{ getMetricLabel(metric) }}</span>
                <div class="p-progress">
                  <div class="p-bar" :style="{ width: (value * 100) + '%' }" :class="metric"></div>
                </div>
                <span class="p-value">{{ (value * 100).toFixed(0) }}%</span>
              </div>
            </div>

            <div class="card-footer-actions">
              <button class="minimal-art-btn" @click="evaluateModel(key)">ANALYZE</button>
              <button class="primary-art-btn" @click="optimizeModel(key)" :disabled="isOptimizing(key)">
                <el-icon v-if="isOptimizing(key)" class="is-loading"><Loading /></el-icon>
                <span>{{ isOptimizing(key) ? 'SYNCING' : 'OPTIMIZE' }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="pro-empty-state" v-else>
        <div class="empty-art-icon"></div>
        <p>NO CLUSTER MODELS DISCOVERED</p>
      </div>
    </section>

    <!-- 底部：隐私协议与系统页脚 -->
    <footer class="studio-footer">
      <div class="privacy-nexus">
        <el-icon><Lock /></el-icon>
        <span>END-TO-END ENCRYPTION ENABLED / AES-256-GCM / DIFFERENTIAL PRIVACY ε=0.15</span>
      </div>
    </footer>

    <!-- 对话框：保持电影级覆盖感 -->
    <el-dialog
      v-model="evaluationDialog.visible"
      title="INTELLIGENCE REPORT"
      width="840px"
      class="studio-dialog"
    >
      <div v-if="evaluationDialog.loading" class="dialog-loader">
        <div class="loader-line"></div>
        <p>RECONSTRUCTING NEURAL MAPPING...</p>
      </div>
      <div v-else-if="evaluationDialog.result" class="report-container">
        <div class="report-meta">
          <div class="tx-id">TX_AUTH: {{ Math.floor(Math.random()*900000) }}</div>
          <div class="timestamp">{{ formatTime(evaluationDialog.result.evaluation_time) }}</div>
        </div>
        
        <div class="report-stats">
          <div class="stat-box" v-for="(value, key) in evaluationDialog.result.metrics" :key="key">
            <span class="s-label">{{ getMetricLabel(key) }}</span>
            <span class="s-value">{{ formatMetricValue(key, value) }}</span>
          </div>
        </div>

        <div class="report-recommendations">
          <h4>CLUSTER_OPTIMIZATION_PATH</h4>
          <div class="rec-list">
            <div class="rec-item" v-for="(rec, idx) in evaluationDialog.result.recommendations" :key="idx">
              <span class="bullet"></span>
              <span class="text">{{ rec }}</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-actions-art">
          <button class="art-btn ghost" @click="evaluationDialog.visible = false">CANCEL</button>
          <button class="art-btn primary" @click="startOptimization">CONFIRM_SYNC</button>
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
  Refresh, ArrowLeft, Lock, Moon, Sunny, Top, Loading
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

// 核心指标
const stats = ref([
  { label: 'CONNECTED_MODELS', value: '7' },
  { label: 'OPTIMIZED_INSTANCES', value: '6' },
  { label: 'ACTIVE_NODES', value: '1,248' },
  { label: 'CLUSTER_PRECISION', value: '91.7%' }
])

const refreshing = ref(false)

// 分类
const categories = [
  { key: 'text_generation', label: 'GEN_TEXT' },
  { key: 'digital_human', label: 'AVATAR' },
  { key: 'emotion_recognition', label: 'EMOTION' }
]

const activeCategory = ref('text_generation')

// 模型数据
const models = ref<Record<string, Record<string, ModelInfo>>>({})
const optimizing = ref<Record<string, boolean>>({})

const currentModels = computed(() => models.value[activeCategory.value] || {})
const getCategoryCount = (key: string) => Object.keys(models.value[key] || {}).length
const switchCategory = (key: string) => activeCategory.value = key

const isOptimizing = (modelKey: string) => {
  const key = `${activeCategory.value}_${modelKey}`
  return optimizing.value[key] || false
}

const getTypeLabel = (type: string) => ({
  'fast': 'FAST',
  'balanced': 'BALANCED',
  'advanced': 'PRO'
})[type] || type

const getMetricLabel = (m: string) => ({
  'accuracy': 'PRECISION',
  'speed': 'LATENCY',
  'efficiency': 'THROUGHPUT'
})[m] || m.toUpperCase()

const formatMetricValue = (k: string, v: number) => 
  (k === 'accuracy' || k === 'success_rate') ? (v * 100).toFixed(1) + '%' : v.toString()

const formatTime = (t: string) => t ? new Date(t).toLocaleTimeString() : ''

// 对话框状态
const evaluationDialog = ref({ visible: false, loading: false, result: null as any, modelKey: '' })

// 逻辑实现
const loadModels = async () => {
  try {
    const res = await federatedModelApi.listModels()
    if (res.success) {
      models.value = res.data
      lastSyncTime.value = new Date().toLocaleTimeString()
    }
  } catch (e) {
    ElMessage.error('Synchronization failed')
  }
}

const evaluateModel = async (key: string) => {
  const model = currentModels.value[key]
  if (!model) return
  evaluationDialog.value.visible = true
  evaluationDialog.value.loading = true
  evaluationDialog.value.modelKey = key
  try {
    const res = await federatedModelApi.evaluateModel(model.type)
    if (res.success) {
      evaluationDialog.value.result = res.data
    }
  } finally {
    evaluationDialog.value.loading = false
  }
}

const optimizeModel = async (key: string) => {
  const model = currentModels.value[key]
  if (!model) return
  const ok = `${activeCategory.value}_${key}`
  optimizing.value[ok] = true
  try {
    const res = await federatedModelApi.optimizeModel(model.type, 'federated', 'quality', 10)
    if (res.success) {
      ElMessage.success('Cluster synchronization initiated')
      await loadModels()
    }
  } finally {
    optimizing.value[ok] = false
  }
}

const startOptimization = () => {
  evaluationDialog.value.visible = false
  optimizeModel(evaluationDialog.value.modelKey)
}

const refreshAll = async () => {
  refreshing.value = true
  try {
    await loadModels()
    ElMessage.success('Cluster fully synced')
  } finally {
    refreshing.value = false
  }
}

onMounted(() => {
  loadModels()
})
</script>

<style scoped lang="scss">
.federated-model-management {
  --bg: radial-gradient(circle at 50% 50%, #0f121d 0%, #05070a 100%);
  --text: #f8fafc;
  --text-dim: rgba(248, 250, 252, 0.45);
  --accent: #6366f1;
  --border: rgba(255, 255, 255, 0.06);
  --glass: rgba(255, 255, 255, 0.015);
  --glass-heavy: rgba(255, 255, 255, 0.04);
  
  &.theme-light {
    --bg: #f8fafc;
    --text: #0f172a;
    --text-dim: #64748b;
    --accent: #4f46e5;
    --border: rgba(0, 0, 0, 0.05);
    --glass: rgba(255, 255, 255, 0.8);
    --glass-heavy: rgba(255, 255, 255, 0.95);
  }

  position: relative;
  min-height: 100vh;
  background: var(--bg);
  background-attachment: fixed;
  color: var(--text);
  font-family: 'Inter', -apple-system, system-ui, sans-serif;
  transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 0;
  overflow-x: hidden;
}

/* --- 高保真渲染背景 --- */
.cinematic-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;

  .gradient-wash {
    position: absolute;
    top: -10%;
    right: -5%;
    width: 70%;
    height: 70%;
    background: radial-gradient(circle, var(--accent) 0%, transparent 75%);
    opacity: 0.12;
    filter: blur(140px);
    animation: pulse-wash 15s infinite alternate ease-in-out;
  }

  .spatial-dust {
    position: absolute;
    inset: 0;
    opacity: 0.15;
  }

  .dust-particle {
    position: absolute;
    width: 1.5px;
    height: 1.5px;
    background: white;
    border-radius: 50%;
    opacity: 0.3;
    animation: dust-float 20s infinite linear;
    @for $i from 1 through 30 {
      &:nth-child(#{$i}) {
        top: random(100) * 1%;
        left: random(100) * 1%;
        animation-delay: random(10) * -1s;
      }
    }
  }

  .radial-vignette {
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 50% 50%, transparent 30%, var(--bg) 100%);
    opacity: 0.7;
  }
}

@keyframes pulse-wash {
  from { transform: scale(1); opacity: 0.08; }
  to { transform: scale(1.2); opacity: 0.15; }
}

/* --- Studio Header --- */
.studio-header {
  position: relative;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 120px;
  padding: 0 80px;
  
  .brand-nexus {
    display: flex;
    align-items: center;
    gap: 40px;
    
    .minimal-back {
      width: 44px;
      height: 44px;
      border-radius: 14px;
      border: 1px solid var(--border);
      background: var(--glass);
      color: var(--text);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      &:hover { 
        border-color: var(--text); 
        background: var(--glass-heavy);
        transform: translateX(-4px); 
      }
    }
    
    .brand-divider { 
      width: 1px; 
      height: 24px; 
      background: var(--border); 
      margin: 0 12px;
    }
    
    .title-group {
      h1 { font-size: 24px; font-weight: 900; letter-spacing: 2px; margin: 0; }
      p { font-size: 13px; color: var(--text-dim); margin: 4px 0 0 0; font-weight: 500; }
    }
  }

  .status-matrix {
    display: flex;
    align-items: center;
    gap: 48px;
    
    .matrix-unit {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      .m-label { font-size: 9px; font-weight: 900; color: var(--text-dim); letter-spacing: 1.5px; }
      .m-value { 
        font-size: 14px; font-weight: 700; margin-top: 4px; 
        &.status-online { color: #10b981; display: flex; align-items: center; gap: 8px; .dot { width: 6px; height: 6px; background: currentColor; border-radius: 50%; box-shadow: 0 0 10px #10b981; } }
      }
    }
    
    .theme-switch-art {
      width: 48px; height: 48px; border-radius: 16px; border: 1px solid var(--border);
      display: flex; align-items: center; justify-content: center;
      cursor: pointer; font-size: 18px; transition: all 0.3s;
      &:hover { background: var(--text); color: var(--bg); }
    }
  }
}

/* --- Hero Visual Section --- */
.dashboard-hero {
  position: relative;
  z-index: 1;
  padding: 0 80px;
  margin-bottom: 120px;
  
  .vis-canvas-wrap {
    position: relative;
    border-radius: 80px;
    overflow: hidden;
    border: 1px solid var(--border);
    background: var(--glass);
    box-shadow: 0 60px 120px rgba(0,0,0,0.25);
    transition: all 0.8s ease;
  }

  .floating-insight {
    position: absolute;
    bottom: 60px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    align-items: center;
    gap: 60px;
    padding: 24px 80px;
    background: var(--glass-heavy);
    backdrop-filter: blur(40px);
    border: 1px solid var(--border);
    border-radius: 100px;
    box-shadow: 0 30px 60px rgba(0,0,0,0.12);
    transition: all 0.5s ease;
    
    .insight-block {
      display: flex;
      flex-direction: column;
      align-items: center;
      min-width: 140px;
      .i-val { 
        font-size: 36px; 
        font-weight: 900; 
        letter-spacing: -2px; 
        color: var(--text);
        line-height: 1;
        &.accent { color: var(--accent); } 
      }
      .i-lbl { font-size: 10px; font-weight: 900; color: var(--text-dim); letter-spacing: 2px; margin-top: 8px; text-transform: uppercase; }
    }
    .insight-divider { width: 1px; height: 40px; background: var(--border); opacity: 0.5; }
  }

  .pro-metrics-bar {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 40px;
    margin-top: 80px;
    
    .metric-glass-card {
      .card-inner {
        display: flex;
        flex-direction: column;
        gap: 16px;
        padding: 0 20px;
        .label { font-size: 11px; font-weight: 900; color: var(--text-dim); letter-spacing: 2.5px; text-transform: uppercase; }
        .value-box {
          display: flex;
          align-items: baseline;
          gap: 16px;
          .value { font-size: 72px; font-weight: 800; letter-spacing: -5px; line-height: 1; }
          .mini-trend { font-size: 24px; color: var(--text-dim); &.up { color: #10b981; } }
        }
      }
    }
  }
}

/* --- Management Layers --- */
.management-layers {
  position: relative;
  z-index: 1;
  padding: 0 80px 120px;

  .controls-integrated {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 80px;
    
    .custom-tab-system {
      display: flex;
      gap: 16px;
      .tab-pill {
        padding: 16px 40px;
        border-radius: 20px;
        background: transparent;
        border: 1px solid var(--border);
        color: var(--text-dim);
        font-size: 14px;
        font-weight: 900;
        letter-spacing: 2px;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        .t-count { font-size: 11px; opacity: 0.4; margin-left: 12px; font-family: 'JetBrains Mono'; }
        &:hover { color: var(--text); border-color: var(--text-dim); transform: translateY(-2px); }
        &.active { background: var(--text); border-color: var(--text); color: var(--bg); box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
      }
    }

    .global-actions {
      display: flex;
      align-items: center;
      gap: 32px;
      .sync-timestamp { font-size: 11px; font-weight: 800; color: var(--text-dim); letter-spacing: 1px; font-family: 'JetBrains Mono'; }
      .pro-sync-btn {
        height: 60px; padding: 0 40px; background: var(--accent); color: white; border: none; border-radius: 20px;
        font-size: 13px; font-weight: 900; letter-spacing: 1.5px; cursor: pointer; display: flex; align-items: center; gap: 16px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        &:hover { transform: translateY(-4px) scale(1.02); box-shadow: 0 20px 40px rgba(99, 102, 241, 0.3); }
      }
    }
  }
}

.art-model-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(460px, 1fr));
  gap: 48px;
}

.art-model-card {
  .card-content {
    padding: 60px;
    background: var(--glass);
    border: 1px solid var(--border);
    border-radius: 56px;
    transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    &:hover { 
      background: var(--glass-heavy); 
      border-color: var(--text-dim); 
      transform: translateY(-15px);
      box-shadow: 0 40px 80px rgba(0,0,0,0.3);
    }
  }

  .card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 56px;
    .name-area {
      h3 { font-size: 28px; font-weight: 900; margin: 0 0 10px 0; letter-spacing: -1.5px; line-height: 1.1; }
      .rev { font-size: 11px; font-weight: 900; color: var(--accent); letter-spacing: 2px; }
    }
    .type-pill { font-size: 9px; font-weight: 900; padding: 6px 14px; border: 1px solid var(--border); border-radius: 10px; color: var(--text-dim); }
  }

  .performance-visual {
    display: flex;
    flex-direction: column;
    gap: 32px;
    margin-bottom: 64px;
    .p-row {
      display: grid;
      grid-template-columns: 110px 1fr 40px;
      align-items: center;
      gap: 24px;
      .p-label { font-size: 12px; font-weight: 900; color: var(--text-dim); letter-spacing: 1px; }
      .p-progress { height: 2px; background: var(--border); .p-fill { height: 100%; background: var(--text); transition: width 1.5s ease; &.accuracy { background: var(--accent); } } }
      .p-value { font-size: 15px; font-weight: 900; text-align: right; font-family: 'JetBrains Mono'; }
    }
  }

  .card-footer-actions {
    display: flex;
    gap: 20px;
    .art-btn {
      height: 54px; border-radius: 18px; font-size: 12px; font-weight: 900; letter-spacing: 1.5px; cursor: pointer; transition: all 0.3s;
      flex: 1; display: flex; align-items: center; justify-content: center; gap: 12px;
    }
    .eval { background: transparent; border: 1px solid var(--border); color: var(--text); &:hover { background: var(--text); color: var(--bg); } }
    .primary { background: var(--accent); border: none; color: white; &:hover { transform: translateY(-2px); filter: brightness(1.1); } }
  }
}

.studio-footer {
  padding: 80px;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: center;
  .privacy-nexus {
    display: flex;
    align-items: center;
    gap: 16px;
    font-size: 11px;
    font-weight: 800;
    color: var(--text-dim);
    letter-spacing: 2px;
    text-transform: uppercase;
  }
}

/* --- Studio Dialog --- */
.studio-dialog {
  :deep(.el-dialog) { background: var(--bg); border-radius: 64px; padding: 80px; border: 1px solid var(--border); box-shadow: 0 60px 120px rgba(0,0,0,0.5); }
  :deep(.el-dialog__header) { margin-bottom: 60px; .el-dialog__title { font-size: 36px; font-weight: 900; letter-spacing: -2px; } }
}

@keyframes dust-float { 0% { transform: translateY(0) translateX(0); } 50% { transform: translateY(-20px) translateX(10px); } 100% { transform: translateY(0) translateX(0); } }

@media (max-width: 1400px) {
  .dashboard-hero .pro-metrics-bar { grid-template-columns: repeat(2, 1fr); gap: 60px; }
  .studio-header { padding: 0 40px; }
  .dashboard-hero, .management-layers { padding: 0 40px; }
}
</style>
