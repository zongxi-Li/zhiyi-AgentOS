<template>
  <div class="digital-human-container" ref="containerRef">
    <canvas ref="canvasRef" class="digital-human-canvas"></canvas>
    <div v-if="loading" class="loading-overlay">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载数字人...</span>
    </div>
    <div v-if="error" class="error-overlay">
      <el-alert
        :title="error"
        type="error"
        :closable="false"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import * as THREE from 'three'

interface Props {
  roleId?: string
  isSpeaking?: boolean
  audioUrl?: string
}

const props = withDefaults(defineProps<Props>(), {
  isSpeaking: false
})

const containerRef = ref<HTMLElement>()
const canvasRef = ref<HTMLCanvasElement>()
const loading = ref(true)
const error = ref<string>('')

let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let renderer: THREE.WebGLRenderer | null = null
let animationId: number | null = null

onMounted(() => {
  initThreeJS()
})

onUnmounted(() => {
  cleanup()
})

watch(() => props.isSpeaking, (speaking) => {
  if (speaking) {
    startLipSync()
  } else {
    stopLipSync()
  }
})

const initThreeJS = () => {
  if (!canvasRef.value || !containerRef.value) return

  try {
    // 创建场景
    scene = new THREE.Scene()
    scene.background = new THREE.Color(0xf0f0f0)

    // 创建相机
    const width = containerRef.value.clientWidth
    const height = containerRef.value.clientHeight
    camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000)
    camera.position.z = 5

    // 创建渲染器
    renderer = new THREE.WebGLRenderer({
      canvas: canvasRef.value,
      antialias: true
    })
    renderer.setSize(width, height)
    renderer.setPixelRatio(window.devicePixelRatio)

    // 添加光源
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
    scene.add(ambientLight)

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
    directionalLight.position.set(5, 5, 5)
    scene.add(directionalLight)

    // 创建简单的几何体作为占位符（实际应该加载3D模型）
    const geometry = new THREE.BoxGeometry(1, 2, 0.5)
    const material = new THREE.MeshStandardMaterial({ color: 0x409eff })
    const cube = new THREE.Mesh(geometry, material)
    scene.add(cube)

    // 开始渲染循环
    animate()

    loading.value = false
  } catch (e: any) {
    error.value = '初始化数字人失败: ' + e.message
    loading.value = false
  }
}

const animate = () => {
  if (!scene || !camera || !renderer) return

  animationId = requestAnimationFrame(animate)
  renderer.render(scene, camera)
}

const startLipSync = () => {
  // TODO: 实现口型同步
  console.log('开始口型同步')
}

const stopLipSync = () => {
  // TODO: 停止口型同步
  console.log('停止口型同步')
}

const cleanup = () => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  if (renderer) {
    renderer.dispose()
  }
  scene = null
  camera = null
  renderer = null
}

// 响应窗口大小变化
const handleResize = () => {
  if (!containerRef.value || !camera || !renderer) return

  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight

  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.digital-human-container {
  width: 100%;
  height: 100%;
  position: relative;
  background: #f5f7fa;
  border-radius: 8px;
  overflow: hidden;
}

.digital-human-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.loading-overlay,
.error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  gap: 10px;
}

.is-loading {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>

