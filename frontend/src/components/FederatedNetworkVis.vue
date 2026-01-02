<template>
  <div class="federated-network-vis" :class="theme" ref="container">
    <!-- 艺术背景层：动态噪声与流光 -->
    <div class="vis-bg">
      <div class="nebula"></div>
      <div class="noise-overlay"></div>
      <div class="scan-line"></div>
    </div>

    <div class="network-overlay">
      <!-- 核心节点：呼吸感的中心 -->
      <div class="global-node-art">
        <div class="core-glow"></div>
        <div class="core-ring"></div>
        <div class="node-icon-wrapper">
          <el-icon><Cpu /></el-icon>
        </div>
        <div class="hub-label">
          <span class="title">CENTRAL INTELLIGENCE</span>
          <span class="status">SYNCING NODES...</span>
        </div>
      </div>
      
      <!-- 边缘节点：环绕排布 -->
      <div class="local-nodes-container">
        <div 
          v-for="i in 8" 
          :key="i" 
          class="node-entry"
          :style="getEntryStyle(i)"
        >
          <div class="connection-path">
            <div class="data-particle" :style="`animation-delay: ${i * 0.4}s`"></div>
          </div>
          <div class="node-point">
            <div class="point-dot"></div>
            <div class="point-label">#{{ 1024 + i }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Cpu } from '@element-plus/icons-vue'

defineProps({
  theme: {
    type: String,
    default: 'dark'
  }
})

const getEntryStyle = (i: number) => {
  const angle = ((i - 1) / 8) * Math.PI * 2
  const radius = 180
  const x = Math.cos(angle) * radius
  const y = Math.sin(angle) * radius
  
  return {
    transform: `translate(${x}px, ${y}px)`,
    '--angle': `${angle}rad`,
    '--length': `${radius}px`
  }
}
</script>

<style scoped lang="scss">
.federated-network-vis {
  --hub-color: #6366f1;
  --particle-color: #818cf8;
  --bg-mix: #0f172a;
  
  &.light {
    --hub-color: #f59e0b;
    --particle-color: #fbbf24;
    --bg-mix: #ffffff;
  }

  position: relative;
  width: 100%;
  height: 550px;
  background: var(--bg-mix);
  border-radius: 40px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.8s ease;
}

/* 艺术背景层 */
.vis-bg {
  position: absolute;
  inset: 0;
  z-index: 1;

  .nebula {
    position: absolute;
    inset: -20%;
    background: radial-gradient(circle at 50% 50%, 
      rgba(99, 102, 241, 0.08) 0%, 
      rgba(16, 185, 129, 0.03) 30%, 
      transparent 70%);
    filter: blur(60px);
    animation: nebula-rotate 20s linear infinite;
  }

  .noise-overlay {
    position: absolute;
    inset: 0;
    opacity: 0.03;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
  }

  .scan-line {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent);
    animation: scan 4s linear infinite;
  }
}

.network-overlay {
  position: relative;
  z-index: 2;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 中心枢纽设计 */
.global-node-art {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  .core-glow {
    position: absolute;
    width: 140px;
    height: 140px;
    background: var(--hub-color);
    border-radius: 50%;
    opacity: 0.15;
    filter: blur(30px);
    animation: hub-pulse 3s ease-in-out infinite;
  }

  .core-ring {
    position: absolute;
    width: 110px;
    height: 110px;
    border: 1px solid var(--hub-color);
    border-opacity: 0.3;
    border-radius: 50%;
    animation: ring-rotate 10s linear infinite;
    &::after {
      content: '';
      position: absolute;
      top: -4px;
      left: 50%;
      width: 8px;
      height: 8px;
      background: var(--hub-color);
      border-radius: 50%;
    }
  }

  .node-icon-wrapper {
    width: 80px;
    height: 80px;
    background: var(--hub-color);
    border-radius: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 32px;
    color: white;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    z-index: 5;
  }

  .hub-label {
    margin-top: 24px;
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: 4px;

    .title {
      font-size: 12px;
      font-weight: 900;
      letter-spacing: 3px;
      color: var(--text-main);
      opacity: 0.8;
    }
    .status {
      font-size: 10px;
      font-weight: 700;
      color: var(--hub-color);
      opacity: 0.6;
    }
  }
}

/* 边缘节点与同步连线 */
.local-nodes-container {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.node-entry {
  position: absolute;
  width: 0;
  height: 0;
}

.connection-path {
  position: absolute;
  bottom: 0;
  left: 0;
  width: var(--length);
  height: 1px;
  background: linear-gradient(90deg, var(--hub-color), transparent);
  transform: rotate(var(--angle));
  transform-origin: 0 0;
  opacity: 0.2;

  .data-particle {
    position: absolute;
    width: 4px;
    height: 4px;
    background: #fff;
    border-radius: 50%;
    box-shadow: 0 0 10px #fff;
    animation: flow-particle 3s infinite cubic-bezier(0.4, 0, 0.2, 1);
  }
}

.node-point {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;

  .point-dot {
    width: 8px;
    height: 8px;
    background: #10b981;
    border-radius: 50%;
    box-shadow: 0 0 15px #10b981;
  }
  .point-label {
    font-size: 9px;
    font-weight: 800;
    color: var(--text-dim);
    font-family: 'JetBrains Mono', monospace;
  }
}

@keyframes hub-pulse {
  0%, 100% { transform: scale(1); opacity: 0.15; }
  50% { transform: scale(1.3); opacity: 0.25; }
}

@keyframes ring-rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes nebula-rotate {
  from { transform: rotate(0deg) scale(1); }
  50% { transform: rotate(180deg) scale(1.1); }
  to { transform: rotate(360deg) scale(1); }
}

@keyframes scan {
  from { transform: translateY(-100%); }
  to { transform: translateY(500px); }
}

@keyframes flow-particle {
  0% { left: 0; opacity: 0; transform: scale(0.5); }
  20% { opacity: 1; transform: scale(1); }
  80% { opacity: 1; transform: scale(1); }
  100% { left: 100%; opacity: 0; transform: scale(0.5); }
}
</style>

