<template>
  <div class="federated-learning-view">
    <section class="page-header glass-panel">
      <div class="header-content">
        <h1>联邦管理</h1>
        <p>统一查看联邦节点、模型版本演进和训练过程，不弹新窗口。</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :disabled="demoRunning" @click="startDemo">
          <el-icon><VideoPlay /></el-icon>
          开始演示
        </el-button>
        <el-button @click="resetSystem">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
        <el-button @click="exportReport">
          <el-icon><Document /></el-icon>
          导出报告
        </el-button>
      </div>
    </section>

    <section class="overview-cards">
      <article v-for="item in systemStats" :key="item.label" class="overview-card glass-panel">
        <div class="stat-meta">
          <span class="label">{{ item.label }}</span>
          <strong class="value">{{ item.value }}</strong>
        </div>
        <div class="stat-trend" :class="{ up: item.trend > 0, down: item.trend < 0 }">
          <el-icon v-if="item.trend > 0"><Top /></el-icon>
          <el-icon v-else-if="item.trend < 0"><Bottom /></el-icon>
          <span>{{ Math.abs(item.trend) }}%</span>
        </div>
      </article>
    </section>

    <section class="main-content">
      <article class="network-section glass-panel">
        <div class="section-header">
          <div>
            <h2>联邦网络拓扑</h2>
            <p>展示中心节点与各客户端连接状态</p>
          </div>
          <div class="section-actions">
            <el-button size="small" @click="refreshNetwork">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-switch v-model="autoRefresh" active-text="自动刷新" inactive-text="手动刷新" />
          </div>
        </div>

        <div class="network-canvas-wrapper">
          <div class="network-toolbar">
            <el-button size="small" circle @click="zoomIn">+</el-button>
            <el-button size="small" circle @click="zoomOut">-</el-button>
            <el-button size="small" circle @click="resetView">
              <el-icon><Refresh /></el-icon>
            </el-button>
            <el-button size="small" circle @click="toggleFullscreen">
              <el-icon><FullScreen /></el-icon>
            </el-button>
          </div>

          <div class="network-canvas" :class="{ fullscreen: isFullscreen }">
            <div class="hub-node">
              <span class="hub-title">聚合中心</span>
              <span class="hub-subtitle">Coordinator</span>
            </div>

            <div
              v-for="(client, index) in clients"
              :key="client.clientId"
              class="line"
              :class="{ active: client.uploadCount > 0 }"
              :style="getLineStyle(index)"
            />

            <div
              v-for="(client, index) in clients"
              :key="`node-${client.clientId}`"
              class="client-node"
              :class="{ active: client.uploadCount > 0, online: client.isOnline }"
              :style="getNodeStyle(index)"
              @click="showClientDetails(client)"
            >
              <div class="node-badge">{{ getClientIcon(client.name) }}</div>
              <span class="node-name">{{ client.name }}</span>
            </div>
          </div>

          <div class="network-status">
            <div class="status-item">
              <span class="dot active"></span>
              活跃节点 {{ activeNodesCount }}
            </div>
            <div class="status-item">
              <span class="dot inactive"></span>
              待激活 {{ inactiveNodesCount }}
            </div>
            <div class="status-item">
              <span class="dot transfer"></span>
              数据传输 {{ dataTransfers }}
            </div>
          </div>
        </div>
      </article>

      <aside class="details-panel">
        <article class="detail-section glass-panel">
          <div class="section-header">
            <div>
              <h3>模型版本历史</h3>
              <p>跟踪联邦聚合版本与性能变化</p>
            </div>
            <el-button size="small" @click="exportHistory">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
          </div>

          <div class="timeline-controls">
            <el-radio-group v-model="timelineView" size="small">
              <el-radio-button label="all">全部</el-radio-button>
              <el-radio-button label="latest">最新</el-radio-button>
              <el-radio-button label="significant">重要</el-radio-button>
            </el-radio-group>
            <el-button size="small" :disabled="selectedVersions.length < 2" @click="compareVersions">
              版本对比
            </el-button>
          </div>

          <div class="timeline-list">
            <article
              v-for="version in filteredModelHistory"
              :key="version.versionId"
              class="timeline-item"
              :class="{ selected: selectedVersions.includes(version.versionId) }"
              @click="toggleVersionSelection(version)"
              @dblclick="showVersionDetails(version)"
            >
              <div class="item-row">
                <strong>v{{ version.version }}</strong>
                <el-tag size="small" :type="version.isLatest ? 'success' : (version.significant ? 'warning' : 'info')">
                  {{ version.isLatest ? '最新' : (version.significant ? '重要' : '常规') }}
                </el-tag>
              </div>
              <div class="item-row muted">
                <span>客户端 {{ version.clientsCount }}</span>
                <span>{{ formatTime(version.createdAt) }}</span>
              </div>
              <div class="item-row muted">
                <span>准确率 {{ version.accuracy.toFixed(1) }}%</span>
                <span>损失 {{ version.loss.toFixed(3) }}</span>
              </div>
            </article>
            <el-empty v-if="filteredModelHistory.length === 0" description="暂无版本记录" />
          </div>
        </article>

        <article class="detail-section glass-panel">
          <div class="section-header">
            <div>
              <h3>客户端列表</h3>
              <p>按节点查看上传和训练状态</p>
            </div>
            <el-input v-model="clientSearch" placeholder="搜索节点" clearable class="search-input">
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>

          <div class="clients-overview">
            <span>总节点 {{ clients.length }}</span>
            <span>活跃率 {{ activeRate }}%</span>
            <span>总数据 {{ totalDataSize }} MB</span>
          </div>

          <div class="clients-list">
            <article
              v-for="client in filteredClients"
              :key="client.clientId"
              class="client-card"
              :class="{ active: client.uploadCount > 0, selected: selectedClients.includes(client.clientId) }"
              @click="toggleClientSelection(client)"
              @dblclick="showClientDetails(client)"
            >
              <div class="item-row">
                <strong>{{ client.name }}</strong>
                <el-tag size="small" :type="client.uploadCount > 0 ? 'success' : 'info'">
                  {{ client.uploadCount > 0 ? '活跃' : '待激活' }}
                </el-tag>
              </div>
              <div class="item-row muted">
                <span>上传 {{ client.uploadCount }} 次</span>
                <span>{{ formatTime(client.lastUpload) }}</span>
              </div>
              <div class="metric">
                <span>贡献度 {{ client.contribution }}%</span>
                <el-progress :percentage="client.contribution" :stroke-width="6" :show-text="false" />
              </div>
              <div class="metric">
                <span>训练进度 {{ client.trainingProgress }}%</span>
                <el-progress :percentage="client.trainingProgress" :stroke-width="6" :show-text="false" />
              </div>
              <div class="actions">
                <el-button size="small" @click.stop="sendMessageToClient(client)">
                  <el-icon><Message /></el-icon>
                  发送消息
                </el-button>
                <el-button size="small" @click.stop="showClientDetails(client)">
                  详情
                </el-button>
              </div>
            </article>
            <el-empty v-if="filteredClients.length === 0" description="没有匹配节点" />
          </div>
        </article>
      </aside>
    </section>

    <section v-if="demoRunning" class="demo-panel glass-panel">
      <div class="demo-header">
        <strong>联邦演示进行中</strong>
        <el-button size="small" @click="stopDemo">停止演示</el-button>
      </div>
      <div class="demo-body">
        <div class="demo-item">
          <span>节点连接</span>
          <el-progress :percentage="demoProgress.clientConnect" />
        </div>
        <div class="demo-item">
          <span>本地训练</span>
          <el-progress :percentage="demoProgress.localTraining" />
        </div>
        <div class="demo-item">
          <span>全局聚合</span>
          <el-progress :percentage="demoProgress.globalAggregation" />
        </div>
      </div>
    </section>

    <el-dialog v-model="versionDialogVisible" title="版本详情" width="560px">
      <div v-if="activeVersion" class="dialog-grid">
        <div><span>版本</span><strong>v{{ activeVersion.version }}</strong></div>
        <div><span>发布时间</span><strong>{{ formatTime(activeVersion.createdAt) }}</strong></div>
        <div><span>客户端数</span><strong>{{ activeVersion.clientsCount }}</strong></div>
        <div><span>准确率</span><strong>{{ activeVersion.accuracy.toFixed(1) }}%</strong></div>
        <div><span>损失</span><strong>{{ activeVersion.loss.toFixed(3) }}</strong></div>
        <div><span>训练时长</span><strong>{{ activeVersion.trainingDuration }}</strong></div>
      </div>
    </el-dialog>

    <el-dialog v-model="clientDialogVisible" title="客户端详情" width="560px">
      <div v-if="activeClient" class="dialog-grid">
        <div><span>节点</span><strong>{{ activeClient.name }}</strong></div>
        <div><span>在线状态</span><strong>{{ activeClient.isOnline ? '在线' : '离线' }}</strong></div>
        <div><span>上传次数</span><strong>{{ activeClient.uploadCount }}</strong></div>
        <div><span>数据量</span><strong>{{ activeClient.dataSize }} MB</strong></div>
        <div><span>贡献度</span><strong>{{ activeClient.contribution }}%</strong></div>
        <div><span>训练进度</span><strong>{{ activeClient.trainingProgress }}%</strong></div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document,
  Download,
  FullScreen,
  Message,
  Refresh,
  Search,
  Top,
  Bottom,
  VideoPlay
} from '@element-plus/icons-vue'

type TimelineView = 'all' | 'latest' | 'significant'

interface ModelVersion {
  versionId: string
  version: string
  createdAt: string
  clientsCount: number
  accuracy: number
  loss: number
  trainingDuration: string
  significant: boolean
  isLatest: boolean
  accuracyTrend: number
}

interface ClientNode {
  clientId: string
  name: string
  uploadCount: number
  lastUpload: string
  dataSize: number
  contribution: number
  accuracy: number
  trainingProgress: number
  isOnline: boolean
  location: string
}

const autoRefresh = ref(true)
const demoRunning = ref(false)
const isFullscreen = ref(false)
const timelineView = ref<TimelineView>('all')
const clientSearch = ref('')
const dataTransfers = ref(18)

const selectedVersions = ref<string[]>([])
const selectedClients = ref<string[]>([])

const activeVersion = ref<ModelVersion | null>(null)
const activeClient = ref<ClientNode | null>(null)
const versionDialogVisible = ref(false)
const clientDialogVisible = ref(false)

const demoProgress = ref({
  clientConnect: 0,
  localTraining: 0,
  globalAggregation: 0
})

const modelHistory = ref<ModelVersion[]>([
  {
    versionId: 'v1.0.0',
    version: '1.0.0',
    createdAt: new Date(Date.now() - 9 * 24 * 60 * 60 * 1000).toISOString(),
    clientsCount: 4,
    accuracy: 84.6,
    loss: 0.412,
    trainingDuration: '14m',
    significant: true,
    isLatest: false,
    accuracyTrend: 3.1
  },
  {
    versionId: 'v1.1.0',
    version: '1.1.0',
    createdAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    clientsCount: 5,
    accuracy: 88.2,
    loss: 0.355,
    trainingDuration: '16m',
    significant: false,
    isLatest: false,
    accuracyTrend: 2.8
  },
  {
    versionId: 'v1.2.0',
    version: '1.2.0',
    createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    clientsCount: 6,
    accuracy: 90.3,
    loss: 0.291,
    trainingDuration: '18m',
    significant: true,
    isLatest: false,
    accuracyTrend: 1.9
  },
  {
    versionId: 'v1.3.0',
    version: '1.3.0',
    createdAt: new Date().toISOString(),
    clientsCount: 6,
    accuracy: 92.1,
    loss: 0.247,
    trainingDuration: '19m',
    significant: true,
    isLatest: true,
    accuracyTrend: 2.0
  }
])

const clients = ref<ClientNode[]>([
  {
    clientId: 'node-bj',
    name: '北京节点',
    uploadCount: 13,
    lastUpload: new Date().toISOString(),
    dataSize: 320,
    contribution: 26,
    accuracy: 91,
    trainingProgress: 100,
    isOnline: true,
    location: 'BJ'
  },
  {
    clientId: 'node-sh',
    name: '上海节点',
    uploadCount: 9,
    lastUpload: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    dataSize: 260,
    contribution: 22,
    accuracy: 89,
    trainingProgress: 88,
    isOnline: true,
    location: 'SH'
  },
  {
    clientId: 'node-gz',
    name: '广州节点',
    uploadCount: 0,
    lastUpload: '',
    dataSize: 140,
    contribution: 12,
    accuracy: 83,
    trainingProgress: 32,
    isOnline: false,
    location: 'GZ'
  },
  {
    clientId: 'node-sz',
    name: '深圳节点',
    uploadCount: 11,
    lastUpload: new Date(Date.now() - 80 * 60 * 1000).toISOString(),
    dataSize: 300,
    contribution: 24,
    accuracy: 90,
    trainingProgress: 76,
    isOnline: true,
    location: 'SZ'
  },
  {
    clientId: 'node-hz',
    name: '杭州节点',
    uploadCount: 5,
    lastUpload: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
    dataSize: 210,
    contribution: 16,
    accuracy: 87,
    trainingProgress: 58,
    isOnline: true,
    location: 'HZ'
  }
])

const activeNodesCount = computed(() => clients.value.filter(item => item.uploadCount > 0).length)
const inactiveNodesCount = computed(() => clients.value.filter(item => item.uploadCount === 0).length)
const activeRate = computed(() => Math.round((activeNodesCount.value / Math.max(clients.value.length, 1)) * 100))
const totalDataSize = computed(() => clients.value.reduce((sum, item) => sum + item.dataSize, 0))

const filteredModelHistory = computed(() => {
  if (timelineView.value === 'latest') return modelHistory.value.filter(item => item.isLatest)
  if (timelineView.value === 'significant') return modelHistory.value.filter(item => item.significant)
  return modelHistory.value
})

const filteredClients = computed(() => {
  const key = clientSearch.value.trim().toLowerCase()
  if (!key) return clients.value
  return clients.value.filter(item => item.name.toLowerCase().includes(key) || item.clientId.toLowerCase().includes(key))
})

const systemStats = computed(() => {
  const latest = modelHistory.value.find(item => item.isLatest) || modelHistory.value[modelHistory.value.length - 1]
  const accuracy = latest?.accuracy || 0
  return [
    { label: '活跃节点', value: String(activeNodesCount.value), trend: 8 },
    { label: '模型版本', value: String(modelHistory.value.length), trend: 12 },
    { label: '训练轮次', value: String(dataTransfers.value), trend: 6 },
    { label: '最新精度', value: `${accuracy.toFixed(1)}%`, trend: 3 }
  ]
})

let demoTimer: number | null = null
let refreshTimer: number | null = null

const getNodePosition = (index: number) => {
  const total = Math.max(clients.value.length, 1)
  const angle = (index / total) * Math.PI * 2 - Math.PI / 2
  const radius = isFullscreen.value ? 220 : 170
  return {
    x: radius * Math.cos(angle),
    y: radius * Math.sin(angle),
    angle
  }
}

const getNodeStyle = (index: number) => {
  const position = getNodePosition(index)
  return {
    left: `calc(50% + ${position.x}px)`,
    top: `calc(50% + ${position.y}px)`
  }
}

const getLineStyle = (index: number) => {
  const position = getNodePosition(index)
  const length = Math.sqrt(position.x * position.x + position.y * position.y)
  return {
    width: `${length}px`,
    left: '50%',
    top: '50%',
    transform: `rotate(${position.angle}rad)`
  }
}

const getClientIcon = (name: string) => {
  if (name.includes('北京')) return '京'
  if (name.includes('上海')) return '沪'
  if (name.includes('广州')) return '穗'
  if (name.includes('深圳')) return '深'
  if (name.includes('杭州')) return '杭'
  return '节'
}

const formatTime = (iso: string) => {
  if (!iso) return '从未上传'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

const zoomIn = () => {
  isFullscreen.value = true
}

const zoomOut = () => {
  isFullscreen.value = false
}

const resetView = () => {
  isFullscreen.value = false
  ElMessage.success('拓扑视图已重置')
}

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
}

const refreshNetwork = () => {
  dataTransfers.value += 1
  ElMessage.success('网络状态已刷新')
}

const compareVersions = () => {
  const [a, b] = selectedVersions.value
  if (!a || !b) return
  ElMessage.info(`已选择 ${a} 与 ${b}，可接入版本差异分析接口`)
}

const toggleVersionSelection = (version: ModelVersion) => {
  const idx = selectedVersions.value.indexOf(version.versionId)
  if (idx >= 0) {
    selectedVersions.value.splice(idx, 1)
    return
  }
  if (selectedVersions.value.length >= 2) {
    selectedVersions.value.shift()
  }
  selectedVersions.value.push(version.versionId)
}

const showVersionDetails = (version: ModelVersion) => {
  activeVersion.value = version
  versionDialogVisible.value = true
}

const toggleClientSelection = (client: ClientNode) => {
  const idx = selectedClients.value.indexOf(client.clientId)
  if (idx >= 0) {
    selectedClients.value.splice(idx, 1)
    return
  }
  selectedClients.value.push(client.clientId)
}

const showClientDetails = (client: ClientNode) => {
  activeClient.value = client
  clientDialogVisible.value = true
}

const sendMessageToClient = (client: ClientNode) => {
  ElMessage.success(`已向 ${client.name} 下发同步指令`)
}

const startDemo = () => {
  if (demoRunning.value) return
  demoRunning.value = true
  demoProgress.value = { clientConnect: 0, localTraining: 0, globalAggregation: 0 }
  ElMessage.success('联邦训练演示已开始')

  demoTimer = window.setInterval(() => {
    if (demoProgress.value.clientConnect < 100) {
      demoProgress.value.clientConnect += 10
      return
    }
    if (demoProgress.value.localTraining < 100) {
      demoProgress.value.localTraining += 10
      return
    }
    if (demoProgress.value.globalAggregation < 100) {
      demoProgress.value.globalAggregation += 10
      return
    }
    stopDemo()
    ElMessage.success('演示流程完成')
  }, 900)
}

const stopDemo = () => {
  demoRunning.value = false
  if (demoTimer !== null) {
    window.clearInterval(demoTimer)
    demoTimer = null
  }
}

const resetSystem = async () => {
  try {
    await ElMessageBox.confirm('确认重置联邦管理演示状态？', '重置确认', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    stopDemo()
    selectedVersions.value = []
    selectedClients.value = []
    isFullscreen.value = false
    dataTransfers.value = 18
    ElMessage.success('系统状态已重置')
  } catch {
    // ignore cancel
  }
}

const downloadJson = (filename: string, payload: unknown) => {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

const exportHistory = () => {
  downloadJson('federated-model-history.json', modelHistory.value)
  ElMessage.success('模型历史已导出')
}

const exportReport = () => {
  downloadJson('federated-report.json', {
    generatedAt: new Date().toISOString(),
    clients: clients.value,
    modelHistory: modelHistory.value,
    metrics: {
      activeNodes: activeNodesCount.value,
      inactiveNodes: inactiveNodesCount.value,
      activeRate: activeRate.value,
      totalDataSize: totalDataSize.value
    }
  })
  ElMessage.success('联邦报告已导出')
}

onMounted(() => {
  refreshTimer = window.setInterval(() => {
    if (!autoRefresh.value) return
    dataTransfers.value += 1
  }, 8000)
})

onUnmounted(() => {
  stopDemo()
  if (refreshTimer !== null) {
    window.clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
.federated-learning-view {
  height: auto;
  min-height: 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: var(--bg-app);
  overflow: visible;
}

.federated-learning-view > section {
  flex-shrink: 0;
}

.glass-panel {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
}

.page-header {
  padding: 16px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.header-content h1 {
  margin: 0;
  font-size: 24px;
}

.header-content p {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.overview-card {
  padding: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-meta .label {
  font-size: 12px;
  color: var(--text-secondary);
}

.stat-meta .value {
  font-size: 22px;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.stat-trend.up {
  color: #16a34a;
}

.stat-trend.down {
  color: #dc2626;
}

.main-content {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 12px;
  align-items: start;
  min-height: 0;
}

.network-section {
  padding: 14px;
  min-height: 640px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.section-header h2,
.section-header h3 {
  margin: 0;
}

.section-header p {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--text-secondary);
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.network-canvas-wrapper {
  margin-top: 12px;
}

.network-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.network-canvas {
  position: relative;
  height: 430px;
  border-radius: 12px;
  background: linear-gradient(160deg, #f8fafc, #eef2ff);
  border: 1px solid var(--border-light);
  overflow: hidden;
}

.network-canvas.fullscreen {
  height: 520px;
}

.hub-node {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 120px;
  height: 120px;
  border-radius: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #4f46e5, #6366f1);
  color: #fff;
  box-shadow: 0 16px 32px rgba(79, 70, 229, 0.3);
  z-index: 2;
}

.hub-title {
  font-size: 14px;
  font-weight: 700;
}

.hub-subtitle {
  margin-top: 4px;
  font-size: 11px;
  opacity: 0.85;
}

.line {
  position: absolute;
  height: 2px;
  transform-origin: left center;
  background: linear-gradient(90deg, rgba(99, 102, 241, 0.7), transparent);
  z-index: 1;
}

.line.active {
  background: linear-gradient(90deg, rgba(22, 163, 74, 0.8), transparent);
}

.client-node {
  position: absolute;
  transform: translate(-50%, -50%);
  width: 94px;
  min-height: 70px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  z-index: 3;
}

.client-node.active {
  border-color: rgba(22, 163, 74, 0.4);
}

.client-node.online {
  box-shadow: 0 8px 18px rgba(22, 163, 74, 0.15);
}

.node-badge {
  width: 26px;
  height: 26px;
  border-radius: 13px;
  background: var(--primary-fade);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: var(--primary-color);
}

.node-name {
  max-width: 80px;
  font-size: 11px;
  color: var(--text-regular);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.network-status {
  margin-top: 10px;
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-secondary);
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 4px;
}

.dot.active {
  background: #22c55e;
}

.dot.inactive {
  background: #94a3b8;
}

.dot.transfer {
  background: #3b82f6;
}

.details-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}

.detail-section {
  padding: 14px;
  min-height: 0;
}

.timeline-controls {
  margin-top: 12px;
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.timeline-list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  min-height: 0;
  overflow-y: auto;
}

.timeline-item {
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 10px;
  cursor: pointer;
  background: #fff;
}

.timeline-item.selected {
  border-color: rgba(79, 70, 229, 0.45);
  background: rgba(79, 70, 229, 0.06);
}

.item-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.item-row.muted {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.search-input {
  width: 180px;
}

.clients-overview {
  margin-top: 12px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--text-secondary);
}

.clients-list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 360px;
  min-height: 0;
  overflow-y: auto;
}

.client-card {
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 10px;
  background: #fff;
}

.client-card.active {
  border-color: rgba(22, 163, 74, 0.35);
}

.client-card.selected {
  border-color: rgba(79, 70, 229, 0.4);
  background: rgba(79, 70, 229, 0.05);
}

.metric {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}

.demo-panel {
  padding: 12px 14px;
}

.demo-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.demo-body {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.demo-item span {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.dialog-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.dialog-grid div {
  background: var(--bg-input);
  border-radius: 8px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dialog-grid span {
  font-size: 12px;
  color: var(--text-secondary);
}

@media (max-width: 1280px) {
  .overview-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .main-content {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .federated-learning-view {
    padding: 12px;
  }

  .page-header {
    flex-direction: column;
  }

  .header-actions {
    flex-wrap: wrap;
  }

  .overview-cards {
    grid-template-columns: 1fr;
  }

  .network-status {
    flex-direction: column;
    gap: 6px;
  }

  .dialog-grid {
    grid-template-columns: 1fr;
  }
}
</style>
