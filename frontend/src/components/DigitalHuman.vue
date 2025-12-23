<template>
  <div class="digital-human-container" ref="containerRef">
    <canvas ref="canvasRef" class="digital-human-canvas"></canvas>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-content">
        <div class="loading-spinner">
          <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        </div>
        <span class="loading-text">加载数字人...</span>
        <div class="loading-progress">
          <div class="progress-bar"></div>
        </div>
      </div>
    </div>
    
    <!-- 错误状态 -->
    <div v-if="error && !loading" class="error-overlay">
      <div class="error-content">
        <div class="error-icon">
          <el-icon :size="48"><WarningFilled /></el-icon>
        </div>
        <h3 class="error-title">加载失败</h3>
        <p class="error-message">{{ error }}</p>
        <el-button 
          type="primary" 
          size="small" 
          @click="handleRetry"
          :loading="retrying"
        >
          重试
        </el-button>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div v-if="!props.roleId && !loading && !error" class="empty-overlay">
      <div class="empty-content">
        <div class="empty-icon">
          <el-icon :size="64"><UserFilled /></el-icon>
        </div>
        <h3 class="empty-title">请选择角色</h3>
        <p class="empty-message">选择一个角色以加载数字人</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { Loading, WarningFilled, UserFilled } from '@element-plus/icons-vue'
import * as THREE from 'three'
import { digitalHumanApi } from '@/services/api/digitalHuman'
import { ElMessage } from 'element-plus'
import { kylinOSRenderer } from '@/utils/kylinOSRenderer'

interface Props {
  roleId?: string
  isSpeaking?: boolean
  audioUrl?: string
  style?: string
  transparent?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isSpeaking: false,
  style: 'realistic',
  transparent: false
})

const containerRef = ref<HTMLElement>()
const canvasRef = ref<HTMLCanvasElement>()
const loading = ref(true)
const error = ref<string>('')
const retrying = ref(false)

let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let renderer: THREE.WebGLRenderer | null = null
let animationId: number | null = null
let digitalHumanModel: THREE.Group | null = null
let lipSyncMixer: THREE.AnimationMixer | null = null
let lipSyncAction: THREE.AnimationAction | null = null
let isLipSyncing = false

onMounted(async () => {
  await initThreeJS()
  if (props.roleId) {
    await createDigitalHuman()
  }
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

watch(() => props.roleId, async (newRoleId) => {
  if (newRoleId) {
    await createDigitalHuman()
  }
})

watch(() => props.style, async (newStyle) => {
  if (props.roleId && newStyle) {
    try {
      const response = await digitalHumanApi.switchStyle(props.roleId, newStyle)
      if (response.success) {
        ElMessage.success('风格切换成功')
      }
    } catch (e: any) {
      ElMessage.error('风格切换失败: ' + e.message)
    }
  }
})

const initThreeJS = async () => {
  if (!canvasRef.value || !containerRef.value) return

  try {
    // 创建场景
    scene = new THREE.Scene()
    if (!props.transparent) {
      scene.background = new THREE.Color(0xf5f7fa)
    }

    // 创建相机
    const width = containerRef.value.clientWidth
    const height = containerRef.value.clientHeight
    camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000)
    camera.position.z = 5

    // 创建渲染器（适配银河麒麟系统）
    renderer = kylinOSRenderer.createRenderer(canvasRef.value)
    renderer.setSize(width, height)
    
    // 获取推荐的渲染设置
    const settings = kylinOSRenderer.getRecommendedSettings()
    renderer.setPixelRatio(settings.pixelRatio)

    // 添加光源
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7)
    scene.add(ambientLight)

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.9)
    directionalLight.position.set(5, 5, 5)
    scene.add(directionalLight)

    // 添加点光源增强效果
    const pointLight = new THREE.PointLight(0x409eff, 0.5, 10)
    pointLight.position.set(0, 2, 3)
    scene.add(pointLight)

    // 创建简单的几何体作为占位符（实际应该加载3D模型）
    const geometry = new THREE.BoxGeometry(1, 2, 0.5)
    const material = new THREE.MeshStandardMaterial({ 
      color: 0x409eff,
      metalness: 0.3,
      roughness: 0.4
    })
    const cube = new THREE.Mesh(geometry, material)
    cube.rotation.y = Math.PI / 4
    scene.add(cube)

    // 开始渲染循环
    animate()

    loading.value = false
  } catch (e: any) {
    error.value = '初始化数字人失败: ' + e.message
    loading.value = false
  }
}

/**
 * 创建数字人
 */
const createDigitalHuman = async () => {
  if (!props.roleId) {
    error.value = '角色ID不能为空'
    return
  }

  try {
    loading.value = true
    error.value = ''
    
    const response = await digitalHumanApi.createDigitalHuman({
      roleId: props.roleId,
      style: props.style
    })

    if (response && response.success) {
      // 使用返回的数据加载3D模型
      const modelData = response.data
      if (modelData?.modelUrl) {
        await load3DModel(modelData.modelUrl)
      } else if (modelData?.modelPath) {
        await load3DModel(modelData.modelPath)
      } else {
        // 如果没有模型URL，使用默认占位符
        createPlaceholderModel()
      }
      ElMessage.success('数字人创建成功')
      loading.value = false
    } else {
      const errorMsg = response?.message || response?.error || '创建数字人失败'
      error.value = errorMsg
      ElMessage.error(errorMsg)
      loading.value = false
    }
  } catch (e: any) {
    // 处理各种错误情况
    let errorMsg = '创建数字人失败'
    
    if (e.response && e.response.data) {
      // 后端返回的错误响应
      const errorData = e.response.data
      errorMsg = errorData.message || errorData.error || errorData.msg || errorMsg
    } else if (e.message) {
      errorMsg = e.message
    } else if (typeof e === 'string') {
      errorMsg = e
    }
    
    error.value = errorMsg
    
    // 更友好的错误提示
    if (e.response?.status === 500) {
      ElMessage.error({
        message: errorMsg || '创建数字人失败: 服务器内部错误，请检查Python服务是否运行',
        duration: 5000
      })
      // 触发全局错误提示
      const errorEvent = new CustomEvent('global-error', {
        detail: { message: errorMsg || '服务器内部错误', duration: 5000 }
      })
      window.dispatchEvent(errorEvent)
    } else if (e.response?.status === 404) {
      ElMessage.warning('数字人服务未找到，请检查后端服务是否正常运行')
    } else {
      ElMessage.error(error.value)
    }
  } finally {
    loading.value = false
  }
}

const animate = () => {
  if (!scene || !camera || !renderer) return

  animationId = requestAnimationFrame(animate)
  renderer.render(scene, camera)
}

/**
 * 加载3D模型
 */
const load3DModel = async (modelUrl: string) => {
  if (!scene) return
  
  try {
    // 清除旧模型
    if (digitalHumanModel) {
      scene.remove(digitalHumanModel)
      digitalHumanModel = null
    }
    
    // 这里应该使用GLTFLoader加载模型
    // 由于需要额外安装@react-three/gltfjsx或three/examples/jsm/loaders/GLTFLoader
    // 暂时使用占位符，实际项目中应该加载真实的3D模型
    createPlaceholderModel()
    
    // 实际实现示例（需要安装three/examples/jsm/loaders/GLTFLoader）:
    // import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'
    // const loader = new GLTFLoader()
    // const gltf = await loader.loadAsync(modelUrl)
    // digitalHumanModel = gltf.scene
    // scene.add(digitalHumanModel)
    // 
    // // 设置动画混合器
    // if (gltf.animations && gltf.animations.length > 0) {
    //   lipSyncMixer = new THREE.AnimationMixer(digitalHumanModel)
    // }
  } catch (e: any) {
    console.error('加载3D模型失败:', e)
    createPlaceholderModel()
  }
}

/**
 * 创建占位符模型
 */
const createPlaceholderModel = () => {
  if (!scene) return
  
  // 清除旧模型
  if (digitalHumanModel) {
    scene.remove(digitalHumanModel)
  }
  
  // 创建更美观的占位符（人形轮廓）
  const group = new THREE.Group()
  
  // 头部
  const headGeometry = new THREE.SphereGeometry(0.3, 32, 32)
  const headMaterial = new THREE.MeshStandardMaterial({ 
    color: 0xffdbac,
    metalness: 0.1,
    roughness: 0.7
  })
  const head = new THREE.Mesh(headGeometry, headMaterial)
  head.position.y = 1.2
  group.add(head)
  
  // 身体
  const bodyGeometry = new THREE.CylinderGeometry(0.25, 0.3, 0.8, 32)
  const bodyMaterial = new THREE.MeshStandardMaterial({ 
    color: 0x409eff,
    metalness: 0.2,
    roughness: 0.6
  })
  const body = new THREE.Mesh(bodyGeometry, bodyMaterial)
  body.position.y = 0.4
  group.add(body)
  
  // 添加旋转动画
  const animateRotation = () => {
    if (group && !isLipSyncing) {
      group.rotation.y += 0.005
    }
  }
  
  // 在animate函数中调用
  const originalAnimate = animate
  animate = () => {
    originalAnimate()
    animateRotation()
  }
  
  digitalHumanModel = group
  scene.add(digitalHumanModel)
}

const startLipSync = async () => {
  if (!props.roleId || !props.audioUrl) return
  
  isLipSyncing = true

  try {
    // 获取音频文件
    const audioResponse = await fetch(props.audioUrl)
    const audioBlob = await audioResponse.blob()
    const audioFile = new File([audioBlob], 'audio.wav', { type: 'audio/wav' })

    // 调用后端API更新动画
    const response = await digitalHumanApi.updateAnimation(
      props.roleId,
      '', // text可以从props获取
      audioFile
    )

    if (response.success) {
      // 使用返回的动画数据更新3D模型
      const animationData = response.data
      if (animationData?.animationUrl && lipSyncMixer) {
        // 加载动画并播放
        // 实际实现需要加载动画文件
        console.log('口型同步开始，动画URL:', animationData.animationUrl)
        
        // 简单的口型同步效果：缩放头部
        if (digitalHumanModel) {
          const head = digitalHumanModel.children.find(child => child.position.y > 1)
          if (head) {
            const scaleAnimation = () => {
              if (isLipSyncing && head) {
                const scale = 1 + Math.sin(Date.now() * 0.01) * 0.1
                head.scale.set(scale, scale, scale)
              }
            }
            const interval = setInterval(() => {
              if (!isLipSyncing) {
                clearInterval(interval)
                if (head) head.scale.set(1, 1, 1)
              } else {
                scaleAnimation()
              }
            }, 50)
          }
        }
      } else {
        console.log('口型同步开始（无动画数据）')
      }
    }
  } catch (e: any) {
    console.error('口型同步失败:', e)
    isLipSyncing = false
  }
}

const stopLipSync = () => {
  isLipSyncing = false
  
  // 停止动画
  if (lipSyncAction) {
    lipSyncAction.stop()
    lipSyncAction = null
  }
  
  // 重置模型状态
  if (digitalHumanModel) {
    const head = digitalHumanModel.children.find(child => child.position.y > 1)
    if (head) {
      head.scale.set(1, 1, 1)
    }
  }
  
  console.log('停止口型同步')
}

const cleanup = () => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  if (renderer) {
    renderer.dispose()
  }
  if (lipSyncMixer) {
    lipSyncMixer.stopAllAction()
    lipSyncMixer = null
  }
  if (digitalHumanModel && scene) {
    scene.remove(digitalHumanModel)
    digitalHumanModel = null
  }
  scene = null
  camera = null
  renderer = null
  isLipSyncing = false
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

const handleRetry = async () => {
  if (!props.roleId) {
    ElMessage.warning('请先选择角色')
    return
  }
  
  retrying.value = true
  error.value = ''
  await createDigitalHuman()
  retrying.value = false
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped lang="scss">
.digital-human-container {
  width: 100%;
  height: 100%;
  position: relative;
  /* background removed to support transparency */
  border-radius: var(--border-radius-large);
  overflow: hidden;
  /* border removed to support transparency */
}

.digital-human-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.loading-overlay,
.error-overlay,
.empty-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.2); /* Semi-transparent default */
  backdrop-filter: blur(8px);
  z-index: 10;
}

.loading-content, .error-content, .empty-content {
  background: rgba(255, 255, 255, 0.8);
  padding: 24px;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  text-align: center;
}

/* Dark mode / transparent mode adaptation could be added here if needed */

.loading-spinner {
  position: relative;
  
  .is-loading {
    animation: rotate 1s linear infinite;
    color: #409eff;
  }
}

.loading-text {
  font-size: 16px;
  font-weight: 500;
  color: #606266;
}

.loading-progress {
  width: 200px;
  height: 4px;
  background: #e4e7ed;
  border-radius: 2px;
  overflow: hidden;
  position: relative;
}

.progress-bar {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 30%;
  background: var(--primary-color);
  border-radius: 2px;
  animation: progress 1.5s ease-in-out infinite;
}

@keyframes progress {
  0% {
    left: -30%;
  }
  100% {
    left: 100%;
  }
}

.error-content,
.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  text-align: center;
  padding: 32px;
  max-width: 300px;
}

.error-icon,
.empty-icon {
  color: #f56c6c;
  opacity: 0.8;
}

.empty-icon {
  color: #909399;
}

.error-title,
.empty-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.error-message,
.empty-message {
  margin: 0;
  font-size: 14px;
  color: #909399;
  line-height: 1.6;
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

