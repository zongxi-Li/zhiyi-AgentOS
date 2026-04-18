<template>
  <div class="federated-learning-view">
    <div class="page-header">
      <div>
        <h1>Federated Learning</h1>
        <p>Model collaboration dashboard</p>
      </div>
      <div class="global-controls">
        <el-button type="primary" @click="startDemo" :disabled="demoRunning">
          <el-icon><VideoPlay /></el-icon>
          Start Demo
        </el-button>
        <el-button @click="resetSystem">
          <el-icon><Refresh /></el-icon>
          Reset
        </el-button>
        <el-button @click="exportReport">
          <el-icon><Document /></el-icon>
          Export Report
        </el-button>
      </div>
    </div>

    <div class="overview-cards">
      <div class="overview-card" v-for="stat in systemStats" :key="stat.label">
        <div class="stat-icon">{{ stat.icon }}</div>
        <div>
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
        <div class="stat-trend" :class="{ positive: stat.trend > 0, negative: stat.trend < 0 }">
          <el-icon v-if="stat.trend > 0"><Top /></el-icon>
          <el-icon v-else-if="stat.trend < 0"><Bottom /></el-icon>
          {{ Math.abs(stat.trend) }}%
        </div>
      </div>
    </div>

    <div class="main-content">
      <div class="network-section panel">
        <div class="section-header">
          <h2>Network Topology</h2>
          <div class="section-controls">
            <el-button size="small" @click="refreshNetwork">
              <el-icon><Refresh /></el-icon>
              Refresh
            </el-button>
            <el-switch v-model="autoRefresh" active-text="Auto" inactive-text="Manual" />
          </div>
        </div>

        <div class="network-toolbar">
          <el-button size="small" circle @click="zoomIn">
            <el-icon><ZoomIn /></el-icon>
          </el-button>
          <el-button size="small" circle @click="zoomOut">
            <el-icon><ZoomOut /></el-icon>
          </el-button>
          <el-button size="small" circle @click="resetView">
            <el-icon><Refresh /></el-icon>
          </el-button>
          <el-button size="small" circle @click="toggleFullscreen">
            <el-icon><FullScreen /></el-icon>
          </el-button>
        </div>

        <div ref="networkCanvas" class="network-canvas"></div>

        <div class="network-status">
          <div>Active: {{ activeNodesCount }}</div>
          <div>Inactive: {{ inactiveNodesCount }}</div>
          <div>Transfers: {{ dataTransfers }}</div>
        </div>
      </div>

      <div class="details-panel">
        <div class="panel detail-section">
          <div class="section-header">
            <h3>Model Versions</h3>
            <el-button size="small" @click="exportHistory">
              <el-icon><Download /></el-icon>
              Export
            </el-button>
          </div>

          <div class="timeline-controls">
            <el-radio-group v-model="timelineView" size="small">
              <el-radio-button label="all">All</el-radio-button>
              <el-radio-button label="latest">Latest</el-radio-button>
              <el-radio-button label="significant">Significant</el-radio-button>
            </el-radio-group>
            <el-button size="small" @click="compareVersions" :disabled="selectedVersions.length < 2">
              <el-icon><Document /></el-icon>
              Compare
            </el-button>
          </div>

          <el-timeline v-if="filteredModelHistory.length > 0">
            <el-timeline-item
              v-for="version in filteredModelHistory"
              :key="version.version_id"
              :timestamp="formatTime(version.created_at)"
              :type="version.isLatest ? 'primary' : version.significant ? 'warning' : 'info'"
            >
              <div
                class="version-card"
                :class="{ selected: selectedVersions.includes(version.version_id) }"
                @click="toggleVersionSelection(version)"
                @dblclick="showVersionDetails(version)"
              >
                <div class="version-header">
                  <strong>v{{ version.version }}</strong>
                  <el-tag size="small">{{ version.clients_count }} clients</el-tag>
                  <el-tag v-if="version.isLatest" type="success" size="small">Latest</el-tag>
                  <el-tag v-if="version.significant" type="warning" size="small">Key</el-tag>
                </div>
                <div class="version-metrics">
                  <span>Accuracy: {{ version.accuracy }}%</span>
                  <span>Loss: {{ version.loss }}</span>
                  <span>Duration: {{ version.training_duration || '-' }}</span>
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="No model history" />
        </div>

        <div class="panel detail-section">
          <div class="section-header">
            <h3>Clients</h3>
            <el-input
              v-model="clientSearch"
              placeholder="Search client"
              size="small"
              style="width: 220px"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>

          <div class="clients-overview">
            <span>Total: {{ clients.length }}</span>
            <span>Active Rate: {{ activeRate }}%</span>
            <span>Data: {{ totalDataSize }} MB</span>
          </div>

          <div
            v-for="client in filteredClients"
            :key="client.client_id"
            class="client-card"
            :class="{
              active: client.upload_count > 0,
              selected: selectedClients.includes(client.client_id),
              online: client.is_online
            }"
            @click="toggleClientSelection(client)"
            @dblclick="showClientDetails(client)"
          >
            <div class="client-header">
              <div class="client-name">{{ client.info?.name || client.client_id }}</div>
              <div class="client-actions">
                <el-tag :type="client.upload_count > 0 ? 'success' : 'info'" size="small">
                  {{ client.upload_count }} uploads
                </el-tag>
                <el-button size="small" circle @click.stop="sendMessageToClient(client)">
                  <el-icon><Message /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="client-metrics">
              <span>Last: {{ formatTime(client.last_upload) }}</span>
              <span>Data: {{ client.data_size || 0 }} MB</span>
              <span>Contribution: {{ client.contribution || 0 }}%</span>
            </div>
            <div class="client-metrics">
              <span>Accuracy: {{ client.accuracy || 0 }}%</span>
              <span>Progress: {{ client.training_progress || 0 }}%</span>
              <span v-if="client.is_online">Online</span>
              <span v-else>Offline</span>
            </div>
          </div>

          <el-empty v-if="filteredClients.length === 0" description="No matching clients" />
        </div>
      </div>
    </div>

    <div v-if="demoRunning" class="demo-controls panel">
      <div class="demo-header">
        <h3>Demo Progress</h3>
        <el-button size="small" @click="stopDemo">
          <el-icon><Close /></el-icon>
          Stop
        </el-button>
      </div>
      <div class="demo-content">
        <div class="demo-step">
          <span>1. Client Connect</span>
          <el-progress :percentage="demoProgress.clientConnect" />
        </div>
        <div class="demo-step">
          <span>2. Local Training</span>
          <el-progress :percentage="demoProgress.localTraining" />
        </div>
        <div class="demo-step">
          <span>3. Aggregation</span>
          <el-progress :percentage="demoProgress.globalAggregation" />
        </div>
      </div>
    </div>

    <el-dialog v-model="clientDialog.visible" title="Client Details" width="600px">
      <div v-if="clientDialog.data" class="client-detail-content">
        <p><strong>ID:</strong> {{ clientDialog.data.client_id }}</p>
        <p><strong>Name:</strong> {{ clientDialog.data.info?.name || '-' }}</p>
        <p><strong>Uploads:</strong> {{ clientDialog.data.upload_count }}</p>
        <p><strong>Last Upload:</strong> {{ formatTime(clientDialog.data.last_upload) }}</p>
        <p><strong>Data Size:</strong> {{ clientDialog.data.data_size || 0 }} MB</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Bottom,
  Close,
  Document,
  Download,
  FullScreen,
  Message,
  Refresh,
  Search,
  Top,
  VideoPlay,
  ZoomIn,
  ZoomOut
} from '@element-plus/icons-vue'

type TimelineView = 'all' | 'latest' | 'significant'

interface ModelVersion {
  version_id: string
  version: string
  created_at: string
  clients_count: number
  accuracy: number
  loss: number
  training_duration?: string
  accuracy_trend: number
  significant?: boolean
  isLatest: boolean
}

interface FederatedClient {
  client_id: string
  upload_count: number
  last_upload: string | null
  info?: {
    name?: string
  }
  data_size?: number
  contribution?: number
  accuracy?: number
  training_progress?: number
  is_online?: boolean
}

const demoRunning = ref(false)
const autoRefresh = ref(true)
const clientSearch = ref('')
const timelineView = ref<TimelineView>('all')
const selectedVersions = ref<string[]>([])
const selectedClients = ref<string[]>([])
const networkScale = ref(1)

const demoProgress = ref({
  clientConnect: 0,
  localTraining: 0,
  globalAggregation: 0
})

const clientDialog = ref<{ visible: boolean; data: FederatedClient | null }>({
  visible: false,
  data: null
})

let demoInterval: ReturnType<typeof setInterval> | null = null
let refreshInterval: ReturnType<typeof setInterval> | null = null

const systemStats = ref([
  { icon: 'N', label: 'Active Nodes', value: '0', trend: 0 },
  { icon: 'V', label: 'Model Versions', value: '0', trend: 0 },
  { icon: 'R', label: 'Training Rounds', value: '0', trend: 0 },
  { icon: 'A', label: 'Avg Accuracy', value: '0%', trend: 0 }
])

const modelHistory = ref<ModelVersion[]>([
  {
    version_id: 'v1.0.0',
    version: '1.0.0',
    created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
    clients_count: 3,
    accuracy: 85.2,
    loss: 0.45,
    training_duration: '6m',
    accuracy_trend: 0,
    significant: false,
    isLatest: false
  },
  {
    version_id: 'v1.1.0',
    version: '1.1.0',
    created_at: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000).toISOString(),
    clients_count: 5,
    accuracy: 88.7,
    loss: 0.38,
    training_duration: '8m',
    accuracy_trend: 3.5,
    significant: true,
    isLatest: false
  },
  {
    version_id: 'v1.2.0',
    version: '1.2.0',
    created_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
    clients_count: 7,
    accuracy: 91.3,
    loss: 0.29,
    training_duration: '9m',
    accuracy_trend: 2.6,
    significant: false,
    isLatest: false
  },
  {
    version_id: 'v1.3.0',
    version: '1.3.0',
    created_at: new Date().toISOString(),
    clients_count: 8,
    accuracy: 92.5,
    loss: 0.25,
    training_duration: '10m',
    accuracy_trend: 1.2,
    significant: true,
    isLatest: true
  }
])

const clients = ref<FederatedClient[]>([
  {
    client_id: 'client_001',
    upload_count: 12,
    last_upload: new Date().toISOString(),
    info: { name: 'Beijing Node' },
    data_size: 245,
    contribution: 23,
    accuracy: 93,
    training_progress: 100,
    is_online: true
  },
  {
    client_id: 'client_002',
    upload_count: 8,
    last_upload: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    info: { name: 'Shanghai Node' },
    data_size: 187,
    contribution: 18,
    accuracy: 90,
    training_progress: 84,
    is_online: true
  },
  {
    client_id: 'client_003',
    upload_count: 0,
    last_upload: null,
    info: { name: 'Guangzhou Node' },
    data_size: 0,
    contribution: 0,
    accuracy: 0,
    training_progress: 0,
    is_online: false
  },
  {
    client_id: 'client_004',
    upload_count: 15,
    last_upload: new Date().toISOString(),
    info: { name: 'Shenzhen Node' },
    data_size: 312,
    contribution: 34,
    accuracy: 95,
    training_progress: 100,
    is_online: true
  },
  {
    client_id: 'client_005',
    upload_count: 6,
    last_upload: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    info: { name: 'Hangzhou Node' },
    data_size: 134,
    contribution: 12,
    accuracy: 88,
    training_progress: 66,
    is_online: true
  }
])

const safeClients = computed(() => (Array.isArray(clients.value) ? clients.value : []))
const safeModelHistory = computed(() => (Array.isArray(modelHistory.value) ? modelHistory.value : []))

const activeNodesCount = computed(() => safeClients.value.filter((client) => client.upload_count > 0).length)
const inactiveNodesCount = computed(() => safeClients.value.filter((client) => client.upload_count === 0).length)
const dataTransfers = computed(() => safeClients.value.reduce((sum, client) => sum + Math.max(0, client.upload_count || 0), 0))

const filteredModelHistory = computed<ModelVersion[]>(() => {
  const history = safeModelHistory.value
  if (timelineView.value === 'latest') return history.filter((version) => version.isLatest)
  if (timelineView.value === 'significant') return history.filter((version) => Boolean(version.significant))
  return history
})

const filteredClients = computed<FederatedClient[]>(() => {
  const keyword = clientSearch.value.trim().toLowerCase()
  if (!keyword) return safeClients.value
  return safeClients.value.filter((client) =>
    (client.info?.name || client.client_id).toLowerCase().includes(keyword)
  )
})

const activeRate = computed(() => {
  const total = safeClients.value.length
  if (!total) return 0
  return Math.round((activeNodesCount.value / total) * 100)
})

const totalDataSize = computed(() => safeClients.value.reduce((total, client) => total + (client.data_size || 0), 0))

const refreshSystemStats = () => {
  const latest = safeModelHistory.value.find((version) => version.isLatest)
  systemStats.value = [
    { icon: 'N', label: 'Active Nodes', value: String(activeNodesCount.value), trend: activeRate.value },
    { icon: 'V', label: 'Model Versions', value: String(safeModelHistory.value.length), trend: safeModelHistory.value.length > 1 ? 8 : 0 },
    { icon: 'R', label: 'Training Rounds', value: String(dataTransfers.value), trend: dataTransfers.value > 0 ? 6 : 0 },
    { icon: 'A', label: 'Avg Accuracy', value: `${latest?.accuracy ?? 0}%`, trend: latest?.accuracy_trend ?? 0 }
  ]
}

const ensureLatestVersionOnly = () => {
  let hasMarkedLatest = false
  modelHistory.value = safeModelHistory.value.map((version) => {
    if (!hasMarkedLatest && version.isLatest) {
      hasMarkedLatest = true
      return version
    }
    return { ...version, isLatest: false }
  })
}

const toggleVersionSelection = (version: ModelVersion) => {
  const idx = selectedVersions.value.indexOf(version.version_id)
  if (idx >= 0) {
    selectedVersions.value.splice(idx, 1)
    return
  }
  selectedVersions.value.push(version.version_id)
}

const toggleClientSelection = (client: FederatedClient) => {
  const idx = selectedClients.value.indexOf(client.client_id)
  if (idx >= 0) {
    selectedClients.value.splice(idx, 1)
    return
  }
  selectedClients.value.push(client.client_id)
}

const compareVersions = () => {
  if (selectedVersions.value.length < 2) {
    ElMessage.warning('Please select at least 2 versions to compare.')
    return
  }
  ElMessage.success(`Comparing: ${selectedVersions.value.join(' vs ')}`)
}

const startDemo = () => {
  if (demoRunning.value) return
  demoRunning.value = true
  demoProgress.value = { clientConnect: 0, localTraining: 0, globalAggregation: 0 }
  ElMessage.success('Federated learning demo started.')

  if (demoInterval) clearInterval(demoInterval)

  demoInterval = setInterval(() => {
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
    if (demoInterval) {
      clearInterval(demoInterval)
      demoInterval = null
    }
    ElMessage.success('Demo completed.')
  }, 1000)
}

const stopDemo = () => {
  demoRunning.value = false
  demoProgress.value = { clientConnect: 0, localTraining: 0, globalAggregation: 0 }
  if (demoInterval) {
    clearInterval(demoInterval)
    demoInterval = null
  }
  ElMessage.info('Demo stopped.')
}

const resetSystem = async () => {
  try {
    await ElMessageBox.confirm('Reset all local demo status and selections?', 'Confirm Reset', {
      confirmButtonText: 'Reset',
      cancelButtonText: 'Cancel',
      type: 'warning'
    })
    stopDemo()
    selectedClients.value = []
    selectedVersions.value = []
    timelineView.value = 'all'
    networkScale.value = 1
    refreshSystemStats()
    renderNetwork()
    ElMessage.success('System reset complete.')
  } catch {
    // user cancelled
  }
}

const refreshNetwork = () => {
  renderNetwork()
  ElMessage.info('Network refreshed.')
}

const exportHistory = () => {
  ElMessage.success(`Exported ${safeModelHistory.value.length} model version records.`)
}

const exportReport = () => {
  ElMessage.success('Federated learning report exported.')
}

const showVersionDetails = (version: ModelVersion) => {
  ElMessage.info(`Version ${version.version}: accuracy ${version.accuracy}%, loss ${version.loss}`)
}

const showClientDetails = (client: FederatedClient) => {
  clientDialog.value.data = client
  clientDialog.value.visible = true
}

const sendMessageToClient = (client: FederatedClient) => {
  ElMessage.success(`Message sent to ${client.info?.name || client.client_id}.`)
}

const formatTime = (time?: string | null) => {
  if (!time) return 'Never uploaded'
  const date = new Date(time)
  if (Number.isNaN(date.getTime())) return 'Invalid time'
  return date.toLocaleString('zh-CN')
}

const networkCanvas = ref<HTMLElement | null>(null)

const applyNetworkScale = () => {
  if (!networkCanvas.value) return
  networkCanvas.value.style.transform = `scale(${networkScale.value})`
  networkCanvas.value.style.transformOrigin = 'center center'
}

const renderNetwork = () => {
  if (!networkCanvas.value) return

  const canvas = networkCanvas.value
  const clientList = safeClients.value
  const total = clientList.length

  canvas.innerHTML = ''
  applyNetworkScale()

  const centerNode = document.createElement('div')
  centerNode.className = 'network-node center-node'
  centerNode.innerHTML = `
    <div class="node-content">
      <span class="node-icon">S</span>
      <span class="node-label">Server</span>
    </div>
  `
  canvas.appendChild(centerNode)

  if (!total) return

  clientList.forEach((client, index) => {
    const angle = (index / total) * 2 * Math.PI
    const radius = 180
    const isActive = client.upload_count > 0

    const clientNode = document.createElement('div')
    clientNode.className = `network-node client-node ${isActive ? 'active' : ''}`
    clientNode.style.left = `calc(50% + ${radius * Math.cos(angle)}px)`
    clientNode.style.top = `calc(50% + ${radius * Math.sin(angle)}px)`
    clientNode.innerHTML = `
      <div class="node-content">
        <span class="node-icon">C</span>
        <span class="node-label">${client.info?.name || client.client_id}</span>
      </div>
      ${isActive ? '<div class="node-status active"></div>' : '<div class="node-status"></div>'}
    `

    const line = document.createElement('div')
    line.className = `network-line ${isActive ? 'active' : ''}`
    line.style.width = `${radius}px`
    line.style.left = '50%'
    line.style.top = '50%'
    line.style.transform = `rotate(${angle}rad)`

    canvas.appendChild(line)
    canvas.appendChild(clientNode)
  })
}

const zoomIn = () => {
  networkScale.value = Math.min(2, networkScale.value + 0.1)
  applyNetworkScale()
}

const zoomOut = () => {
  networkScale.value = Math.max(0.5, networkScale.value - 0.1)
  applyNetworkScale()
}

const resetView = () => {
  networkScale.value = 1
  applyNetworkScale()
}

const toggleFullscreen = async () => {
  const target = networkCanvas.value?.parentElement
  if (!target) return
  try {
    if (document.fullscreenElement) {
      await document.exitFullscreen()
    } else {
      await target.requestFullscreen()
    }
  } catch {
    ElMessage.warning('Fullscreen is not available in this browser context.')
  }
}

onMounted(() => {
  ensureLatestVersionOnly()
  refreshSystemStats()
  renderNetwork()
  refreshInterval = setInterval(() => {
    if (!autoRefresh.value) return
    refreshSystemStats()
    renderNetwork()
  }, 5000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
  if (demoInterval) {
    clearInterval(demoInterval)
    demoInterval = null
  }
})
</script>

<style scoped>
.federated-learning-view {
  min-height: 100vh;
  padding: 20px;
  background: linear-gradient(135deg, #243b55 0%, #141e30 100%);
  color: #fff;
}

.page-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
}

.page-header p {
  margin: 6px 0 0;
  opacity: 0.85;
}

.global-controls {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.overview-card {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 10px;
  padding: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.stat-icon {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
}

.stat-label {
  font-size: 12px;
  opacity: 0.85;
}

.stat-trend {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-trend.positive {
  color: #6ddf6d;
}

.stat-trend.negative {
  color: #ff7a7a;
}

.main-content {
  display: grid;
  grid-template-columns: 1fr 420px;
  gap: 16px;
}

.panel {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 10px;
  padding: 14px;
}

.network-section {
  min-height: 540px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  gap: 10px;
}

.section-header h2,
.section-header h3 {
  margin: 0;
}

.section-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.network-toolbar {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-bottom: 10px;
}

.network-canvas {
  position: relative;
  width: 100%;
  height: 380px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
}

.network-node {
  position: absolute;
  width: 92px;
  height: 92px;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.center-node {
  left: 50%;
  top: 50%;
  background: #ff5f6d;
}

.client-node {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.client-node.active {
  border-color: #78d078;
}

.node-content {
  font-size: 12px;
  line-height: 1.3;
}

.node-icon {
  display: block;
  font-weight: 700;
  margin-bottom: 2px;
}

.node-status {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #999;
}

.node-status.active {
  background: #6ddf6d;
}

.network-line {
  position: absolute;
  height: 2px;
  background: rgba(255, 255, 255, 0.2);
  transform-origin: left center;
}

.network-line.active {
  background: rgba(109, 223, 109, 0.8);
}

.network-status {
  margin-top: 10px;
  display: flex;
  gap: 14px;
  font-size: 13px;
}

.details-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-section {
  max-height: 360px;
  overflow: auto;
}

.timeline-controls {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
  align-items: center;
}

.version-card {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 10px;
  cursor: pointer;
}

.version-card.selected {
  border-color: #6ddf6d;
}

.version-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.version-metrics {
  display: flex;
  gap: 10px;
  font-size: 12px;
  opacity: 0.9;
  flex-wrap: wrap;
}

.clients-overview {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
  font-size: 12px;
  opacity: 0.9;
}

.client-card {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 10px;
  cursor: pointer;
}

.client-card.selected {
  border-color: #6ddf6d;
}

.client-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.client-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.client-name {
  font-weight: 700;
}

.client-metrics {
  display: flex;
  gap: 10px;
  font-size: 12px;
  opacity: 0.9;
  margin-top: 4px;
  flex-wrap: wrap;
}

.demo-controls {
  position: fixed;
  right: 20px;
  bottom: 20px;
  width: 360px;
}

.demo-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.demo-header h3 {
  margin: 0;
}

.demo-step {
  margin-bottom: 10px;
}

.demo-step:last-child {
  margin-bottom: 0;
}

.client-detail-content p {
  margin: 0 0 8px;
}

@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }

  .demo-controls {
    width: calc(100% - 40px);
    left: 20px;
    right: 20px;
  }
}
</style>
