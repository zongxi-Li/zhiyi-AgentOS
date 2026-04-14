<template>
  <div class="federated-learning-view">
    <div class="ambient-glow top-left"></div>
    <div class="ambient-glow bottom-right"></div>

    <div class="page-header glass-panel">
      <div>
        <h1>联邦管理</h1>
        <p>联邦训练节点协同状态、轮次演进与系统健康监控</p>
      </div>
      <div class="header-actions">
        <el-button :loading="refreshing" @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新状态
        </el-button>
        <el-button v-if="!demoRunning" type="primary" @click="startDemo">
          <el-icon><VideoPlay /></el-icon>
          启动演示
        </el-button>
        <el-button v-else type="danger" @click="stopDemo">
          <el-icon><CloseBold /></el-icon>
          停止演示
        </el-button>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card glass-panel">
        <div class="label">在线节点</div>
        <div class="value">{{ onlineClients }}/{{ clients.length }}</div>
      </div>
      <div class="stat-card glass-panel">
        <div class="label">当前轮次</div>
        <div class="value">Round {{ currentRound }}</div>
      </div>
      <div class="stat-card glass-panel">
        <div class="label">全局精度</div>
        <div class="value">{{ globalAccuracy }}%</div>
      </div>
      <div class="stat-card glass-panel">
        <div class="label">平均延迟</div>
        <div class="value">{{ avgLatency }}ms</div>
      </div>
    </div>

    <div class="content-grid">
      <section class="glass-panel section-card">
        <div class="section-title">
          <el-icon><Connection /></el-icon>
          <span>节点状态</span>
        </div>
        <el-table :data="clients" stripe height="360">
          <el-table-column prop="name" label="节点" min-width="140" />
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="getStatusTag(row.status)">{{ getStatusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="贡献度" min-width="130">
            <template #default="{ row }">
              <span>{{ row.contribution }}%</span>
            </template>
          </el-table-column>
          <el-table-column label="训练进度" min-width="180">
            <template #default="{ row }">
              <el-progress :percentage="row.progress" :stroke-width="8" :show-text="false" />
            </template>
          </el-table-column>
          <el-table-column label="精度" width="90">
            <template #default="{ row }">{{ row.accuracy.toFixed(1) }}%</template>
          </el-table-column>
          <el-table-column label="延迟" width="90">
            <template #default="{ row }">{{ row.latency }}ms</template>
          </el-table-column>
        </el-table>
      </section>

      <section class="glass-panel section-card">
        <div class="section-title">
          <el-icon><DataAnalysis /></el-icon>
          <span>轮次历史</span>
        </div>
        <el-timeline class="timeline">
          <el-timeline-item
            v-for="round in rounds"
            :key="round.id"
            :timestamp="formatTime(round.startedAt)"
            :type="round.delta >= 0 ? 'success' : 'warning'"
          >
            <div class="round-card">
              <div class="round-title">Round {{ round.id }}</div>
              <div class="round-metrics">
                <span>参与节点 {{ round.participants }}</span>
                <span>精度 {{ round.globalAccuracy }}%</span>
                <span>耗时 {{ round.duration }}</span>
                <span :class="round.delta >= 0 ? 'up' : 'down'">
                  {{ round.delta >= 0 ? '+' : '' }}{{ round.delta }}%
                </span>
              </div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </section>
    </div>

    <section class="glass-panel log-card">
      <div class="section-title">
        <el-icon><TrendCharts /></el-icon>
        <span>实时事件</span>
      </div>
      <div class="log-list">
        <div v-for="(item, index) in events" :key="index" class="log-item" :class="item.level">
          <span class="log-time">{{ item.time }}</span>
          <span class="log-text">{{ item.message }}</span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, VideoPlay, CloseBold, Connection, DataAnalysis, TrendCharts } from '@element-plus/icons-vue'

type ClientStatus = 'online' | 'training' | 'offline'
type LogLevel = 'info' | 'success' | 'warning'

interface FederatedClient {
  id: string
  name: string
  status: ClientStatus
  contribution: number
  progress: number
  accuracy: number
  latency: number
  lastSeen: string
}

interface RoundHistory {
  id: number
  startedAt: string
  participants: number
  globalAccuracy: number
  duration: string
  delta: number
}

interface LogEvent {
  time: string
  level: LogLevel
  message: string
}

const makeInitialClients = (): FederatedClient[] => [
  {
    id: 'edge-01',
    name: '华东节点 A',
    status: 'online',
    contribution: 23,
    progress: 82,
    accuracy: 91.4,
    latency: 42,
    lastSeen: new Date().toISOString()
  },
  {
    id: 'edge-02',
    name: '华南节点 B',
    status: 'training',
    contribution: 19,
    progress: 66,
    accuracy: 89.8,
    latency: 57,
    lastSeen: new Date().toISOString()
  },
  {
    id: 'edge-03',
    name: '西南节点 C',
    status: 'online',
    contribution: 27,
    progress: 91,
    accuracy: 92.7,
    latency: 39,
    lastSeen: new Date().toISOString()
  },
  {
    id: 'edge-04',
    name: '华北节点 D',
    status: 'offline',
    contribution: 0,
    progress: 0,
    accuracy: 0,
    latency: 0,
    lastSeen: new Date(Date.now() - 20 * 60 * 1000).toISOString()
  }
]

const makeInitialRounds = (): RoundHistory[] => [
  { id: 12, startedAt: new Date(Date.now() - 8 * 60 * 1000).toISOString(), participants: 3, globalAccuracy: 92.3, duration: '2m 10s', delta: 0.4 },
  { id: 11, startedAt: new Date(Date.now() - 18 * 60 * 1000).toISOString(), participants: 3, globalAccuracy: 91.9, duration: '2m 03s', delta: 0.6 },
  { id: 10, startedAt: new Date(Date.now() - 28 * 60 * 1000).toISOString(), participants: 2, globalAccuracy: 91.3, duration: '1m 58s', delta: 0.3 }
]

const makeInitialEvents = (): LogEvent[] => [
  { time: nowTime(), level: 'success', message: '全局模型 v1.2.0 已发布到聚合器。' },
  { time: nowTime(), level: 'info', message: '节点 华南节点 B 正在进行本地增量训练。' },
  { time: nowTime(), level: 'warning', message: '节点 华北节点 D 当前离线，已切换容错策略。' }
]

const clients = ref<FederatedClient[]>(makeInitialClients())
const rounds = ref<RoundHistory[]>(makeInitialRounds())
const events = ref<LogEvent[]>(makeInitialEvents())

const demoRunning = ref(false)
const refreshing = ref(false)
const currentRound = ref(12)

let demoTimer: ReturnType<typeof setInterval> | null = null

const onlineClients = computed(() => clients.value.filter((item) => item.status !== 'offline').length)
const globalAccuracy = computed(() => {
  const valid = clients.value.filter((item) => item.status !== 'offline')
  if (valid.length === 0) return '0.0'
  const avg = valid.reduce((sum, item) => sum + item.accuracy, 0) / valid.length
  return avg.toFixed(1)
})
const avgLatency = computed(() => {
  const valid = clients.value.filter((item) => item.status !== 'offline')
  if (valid.length === 0) return 0
  return Math.round(valid.reduce((sum, item) => sum + item.latency, 0) / valid.length)
})

function nowTime(): string {
  return new Date().toLocaleTimeString('zh-CN', { hour12: false })
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

function getStatusTag(status: ClientStatus): 'success' | 'warning' | 'info' {
  if (status === 'online') return 'success'
  if (status === 'training') return 'warning'
  return 'info'
}

function getStatusText(status: ClientStatus): string {
  if (status === 'online') return '在线'
  if (status === 'training') return '训练中'
  return '离线'
}

function pushEvent(message: string, level: LogLevel = 'info'): void {
  events.value.unshift({ time: nowTime(), level, message })
  if (events.value.length > 12) {
    events.value = events.value.slice(0, 12)
  }
}

function refreshData(): void {
  refreshing.value = true
  window.setTimeout(() => {
    clients.value = clients.value.map((item) => {
      if (item.status === 'offline') return item
      const progress = Math.min(100, item.progress + Math.floor(Math.random() * 5))
      const accuracy = Math.min(99.9, Math.max(80, item.accuracy + (Math.random() - 0.4) * 0.8))
      const latency = Math.max(20, Math.round(item.latency + (Math.random() - 0.5) * 8))
      return { ...item, progress, accuracy, latency, lastSeen: new Date().toISOString() }
    })
    refreshing.value = false
    pushEvent('已完成一次手动刷新。', 'success')
  }, 700)
}

function runOneRound(): void {
  currentRound.value += 1
  clients.value = clients.value.map((item) => {
    if (item.status === 'offline') return item
    return {
      ...item,
      status: Math.random() > 0.75 ? 'training' : 'online',
      progress: 35 + Math.floor(Math.random() * 65),
      accuracy: Math.min(99.9, Math.max(85, item.accuracy + (Math.random() - 0.35) * 1.2)),
      latency: Math.max(20, Math.round(item.latency + (Math.random() - 0.5) * 10)),
      lastSeen: new Date().toISOString()
    }
  })

  const accuracy = Number(globalAccuracy.value)
  const delta = Number((Math.random() * 1.2 - 0.2).toFixed(1))
  rounds.value.unshift({
    id: currentRound.value,
    startedAt: new Date().toISOString(),
    participants: onlineClients.value,
    globalAccuracy: Number((accuracy + delta).toFixed(1)),
    duration: `${1 + Math.floor(Math.random() * 2)}m ${10 + Math.floor(Math.random() * 40)}s`,
    delta
  })
  rounds.value = rounds.value.slice(0, 10)
  pushEvent(`Round ${currentRound.value} 聚合完成，精度变化 ${delta >= 0 ? '+' : ''}${delta}%`, delta >= 0 ? 'success' : 'warning')
}

function startDemo(): void {
  if (demoRunning.value) return
  demoRunning.value = true
  pushEvent('联邦训练演示已启动。', 'info')
  ElMessage.success('联邦训练演示已启动')
  demoTimer = setInterval(runOneRound, 3000)
}

function stopDemo(): void {
  if (!demoRunning.value) return
  demoRunning.value = false
  if (demoTimer) {
    clearInterval(demoTimer)
    demoTimer = null
  }
  pushEvent('联邦训练演示已停止。', 'warning')
}

onUnmounted(() => {
  if (demoTimer) {
    clearInterval(demoTimer)
  }
})
</script>

<style scoped>
.federated-learning-view {
  position: relative;
  min-height: 100%;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  color: var(--text-primary);
  overflow: auto;
}

.ambient-glow {
  position: absolute;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  filter: blur(70px);
  opacity: 0.2;
  pointer-events: none;
  z-index: 0;
}

.ambient-glow.top-left {
  top: -120px;
  left: -120px;
  background: #5b8ff9;
}

.ambient-glow.bottom-right {
  right: -120px;
  bottom: -140px;
  background: #36cfc9;
}

.glass-panel {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 14px;
  backdrop-filter: blur(10px);
  box-shadow: 0 10px 28px rgba(15, 35, 95, 0.06);
}

.page-header {
  padding: 16px 18px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  line-height: 1.2;
}

.page-header p {
  margin: 8px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.stats-grid {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.stat-card {
  padding: 14px 16px;
}

.stat-card .label {
  font-size: 13px;
  color: var(--text-secondary);
}

.stat-card .value {
  margin-top: 6px;
  font-size: 22px;
  font-weight: 700;
}

.content-grid {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 12px;
  grid-template-columns: 1.2fr 1fr;
}

.section-card {
  padding: 14px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  margin-bottom: 10px;
}

.timeline {
  max-height: 360px;
  overflow: auto;
  padding-right: 4px;
}

.round-card {
  background: rgba(91, 143, 249, 0.06);
  border-radius: 10px;
  padding: 10px 12px;
}

.round-title {
  font-weight: 600;
}

.round-metrics {
  margin-top: 6px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--text-secondary);
}

.up {
  color: #389e0d;
}

.down {
  color: #cf1322;
}

.log-card {
  position: relative;
  z-index: 1;
  padding: 14px;
}

.log-list {
  max-height: 220px;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.log-item {
  display: grid;
  grid-template-columns: 84px 1fr;
  gap: 8px;
  padding: 9px 10px;
  border-radius: 8px;
  font-size: 13px;
}

.log-item.info {
  background: rgba(91, 143, 249, 0.08);
}

.log-item.success {
  background: rgba(82, 196, 26, 0.1);
}

.log-item.warning {
  background: rgba(250, 173, 20, 0.12);
}

.log-time {
  color: var(--text-secondary);
}

@media (max-width: 1100px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .federated-learning-view {
    padding: 12px;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions {
    flex-wrap: wrap;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
