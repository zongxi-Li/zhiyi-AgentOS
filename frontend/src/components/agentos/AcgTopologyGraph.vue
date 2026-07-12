<!-- ACG 拓扑图 — 使用 vis-network 渲染 ACG 交互式拓扑，含步骤、Agent、记忆、证据、控制节点和图例 -->
<template>
  <section class="acg-topology ui-surface">
    <header class="panel-head">
      <div class="head-left">
        <el-icon class="head-icon"><Share /></el-icon>
        <h4>ACG 拓扑图</h4>
      </div>
      <div class="head-right">
        <span class="meta" v-if="hasData">{{ stats }}</span>
        <button v-if="hasData" class="action-btn" @click="fit" title="适配视图">
          <el-icon><FullScreen /></el-icon>
        </button>
      </div>
    </header>

    <div v-if="!hasData" class="empty">暂无 ACG 拓扑数据，请先运行一个 ACG 引擎工作流</div>
    <div v-else ref="graphRef" class="graph-canvas" />

    <div v-if="hasData" class="legend">
      <span class="legend-item"><i class="dot step"></i>步骤</span>
      <span class="legend-item"><i class="dot agent"></i>智能体</span>
      <span class="legend-item"><i class="dot memory"></i>记忆</span>
      <span class="legend-item"><i class="dot evidence"></i>证据</span>
      <span class="legend-item"><i class="dot control"></i>控制</span>
      <span class="legend-item"><i class="ring done"></i>已完成</span>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Share, FullScreen } from '@element-plus/icons-vue'
import { DataSet } from 'vis-data'
import { Network } from 'vis-network'
import type { AcgBlueprint, AcgNode, AcgEdge } from '@/services/api/agentos'

const props = defineProps<{
  blueprint: AcgBlueprint | null
  completedStepIds?: string[]
}>()

const graphRef = ref<HTMLElement | null>(null)
let network: Network | null = null

const hasData = computed(() => {
  return !!props.blueprint && Array.isArray(props.blueprint.nodes) && props.blueprint.nodes.length > 0
})

const stats = computed(() => {
  if (!props.blueprint) return ''
  return `${props.blueprint.nodes.length} 节点 / ${props.blueprint.edges.length} 边`
})

// 节点类型 → 配色（沿用项目色板）
const NODE_STYLE: Record<string, { background: string; border: string; shape: string }> = {
  step: { background: '#dbe7e3', border: '#3f6b63', shape: 'box' },
  agent: { background: '#cfe0f0', border: '#496b8f', shape: 'ellipse' },
  skill: { background: '#e6e0f0', border: '#6b5b95', shape: 'ellipse' },
  memory: { background: '#fcefd6', border: '#9a7432', shape: 'database' },
  evidence: { background: '#f6dede', border: '#b24a4a', shape: 'diamond' },
  control: { background: '#e2e8e0', border: '#727c76', shape: 'hexagon' }
}

// 边类型 → 样式
const EDGE_STYLE: Record<string, { color: string; dashes: boolean | number[] }> = {
  dependency: { color: '#3f6b63', dashes: false },
  communication: { color: '#496b8f', dashes: [4, 4] },
  control_flow: { color: '#9a7432', dashes: [2, 3] },
  write: { color: '#9a7432', dashes: [6, 3] },
  read: { color: '#9a7432', dashes: [6, 3] },
  support: { color: '#b24a4a', dashes: [2, 2] },
  execution: { color: '#727c76', dashes: false }
}

const buildNodeRows = (nodes: AcgNode[], completed: Set<string>) => {
  return nodes.map((node) => {
    const style = NODE_STYLE[node.nodeType] || NODE_STYLE.step
    const isDone = completed.has(node.nodeId)
    const label = node.name || node.nodeId
    const isStep = node.nodeType === 'step'
    return {
      id: node.nodeId,
      label,
      shape: style.shape,
      color: {
        background: style.background,
        border: isDone ? '#2f8f5b' : style.border,
        highlight: { background: style.background, border: '#2f8f5b' }
      },
      borderWidth: isDone ? 3 : 1.5,
      // Step 为主干节点（大、醒目）；Agent/Memory/Evidence 为认知卫星节点（小）
      size: isStep ? 26 : 16,
      font: { size: isStep ? 14 : 11, color: isStep ? '#1d2422' : '#5a635e' },
      mass: isStep ? 3 : 1,
      margin: isStep ? 10 : 6
    }
  })
}

const buildEdgeRows = (edges: AcgEdge[]) => {
  return edges.map((edge, index) => {
    const style = EDGE_STYLE[edge.edgeType] || EDGE_STYLE.dependency
    const isDep = edge.edgeType === 'dependency'
    return {
      id: edge.edgeId || `e-${index}`,
      from: edge.sourceId,
      to: edge.targetId,
      arrows: 'to',
      color: { color: style.color, highlight: '#2f8f5b' },
      dashes: style.dashes,
      smooth: { enabled: true, type: 'continuous' },
      // 依赖主干边更粗更短（强弹簧），认知关联边更细
      width: isDep ? 2.5 : 1,
      length: isDep ? 130 : 70
    }
  })
}

const options = {
  autoResize: true,
  layout: { improvedLayout: true },
  physics: {
    enabled: true,
    solver: 'forceAtlas2Based',
    forceAtlas2Based: {
      gravitationalConstant: -45,
      centralGravity: 0.012,
      springLength: 120,
      springConstant: 0.18,
      damping: 0.42,
      avoidOverlap: 0.6
    },
    maxVelocity: 28,
    minVelocity: 0.45,
    timestep: 0.5,
    adaptiveTimestep: true,
    stabilization: { enabled: true, iterations: 220, fit: true }
  },
  interaction: { hover: true, dragNodes: true, zoomView: true, navigationButtons: false }
}

const render = async () => {
  await nextTick()
  if (!graphRef.value || !hasData.value || !props.blueprint) return
  const completed = new Set(props.completedStepIds || [])
  if (network) {
    network.destroy()
    network = null
  }
  const data = {
    nodes: new DataSet(buildNodeRows(props.blueprint.nodes, completed)),
    edges: new DataSet(buildEdgeRows(props.blueprint.edges))
  }
  network = new Network(graphRef.value, data as any, options as any)

  // 布局展开成形后，完全冻结 physics —— 节点定住不再漂移抖动。
  // physics 关闭后 dragNodes 仍有效：拖动只移动被拖的单个节点，
  // 其余节点保持不动，不会触发整图重新布局/旋转。
  network.once('stabilizationIterationsDone', () => {
    network?.setOptions({ physics: { enabled: false } } as any)
    network?.fit({ animation: { duration: 350, easingFunction: 'easeInOutQuad' } })
  })
}

const fit = () => network?.fit({ animation: true })

watch(() => [props.blueprint, props.completedStepIds], () => render(), { deep: true })
onMounted(render)
onBeforeUnmount(() => {
  network?.destroy()
  network = null
})
</script>

<style scoped>
.acg-topology {
  display: flex;
  flex-direction: column;
}
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
}
.head-left { display: flex; align-items: center; gap: 6px; }
.head-icon { font-size: 15px; color: var(--primary-color); }
.panel-head h4 { margin: 0; font-size: 14px; font-weight: 700; color: var(--text-primary); }
.head-right { display: flex; align-items: center; gap: 8px; }
.meta { font-size: 11px; color: var(--text-secondary); font-weight: 600; }
.action-btn {
  width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;
  border: none; background: var(--primary-fade); color: var(--primary-color);
  border-radius: 6px; cursor: pointer; transition: all .2s ease;
}
.action-btn:hover { background: var(--primary-color); color: #fff; }
.empty { padding: 32px 12px; text-align: center; color: var(--text-secondary); font-size: 13px; }
.graph-canvas { width: 100%; height: 420px; min-height: 320px; }
.legend {
  display: flex; flex-wrap: wrap; gap: 12px; padding-top: var(--space-sm);
  border-top: 1px solid var(--border-light); margin-top: var(--space-sm);
}
.legend-item { display: flex; align-items: center; gap: 4px; font-size: 11px; color: var(--text-secondary); }
.dot { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
.dot.step { background: #dbe7e3; border: 1.5px solid #3f6b63; }
.dot.agent { background: #cfe0f0; border: 1.5px solid #496b8f; border-radius: 50%; }
.dot.memory { background: #fcefd6; border: 1.5px solid #9a7432; }
.dot.evidence { background: #f6dede; border: 1.5px solid #b24a4a; transform: rotate(45deg); }
.dot.control { background: #e2e8e0; border: 1.5px solid #727c76; }
.ring { width: 10px; height: 10px; border-radius: 50%; display: inline-block; border: 3px solid #2f8f5b; }
</style>
