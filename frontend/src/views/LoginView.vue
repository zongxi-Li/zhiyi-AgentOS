<template>
  <div class="login-view">
    <div class="login-layout">
      <!-- 左侧：宣传卡片 -->
      <div class="promo-card">
        <div class="promo-content">
          <div class="logo-section">
            <div class="logo-icon">K</div>
            <div class="logo-text">Kinlin AI</div>
          </div>
          
          <div class="promo-title-wrapper">
            <h1 class="promo-title">
              智能数字人交互
            </h1>
            <p class="promo-subtitle">
              开启全新对话体验
            </p>
          </div>
          
          <div class="promo-image">
            <!-- 数字人形象占位 -->
            <div class="digital-human-placeholder">
              <el-icon :size="120"><User /></el-icon>
            </div>
          </div>
          
          <div class="promo-features">
            <div class="feature-item">
              <el-icon><Monitor /></el-icon>
              <span>多端同步</span>
            </div>
            <div class="feature-item">
              <el-icon><Connection /></el-icon>
              <span>实时交互</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 右侧：登录表单 -->
      <div class="login-form-card">
        <el-tabs v-model="activeTab" class="login-tabs">
          <el-tab-pane label="登录" name="login">
            <el-form
              ref="loginFormRef"
              :model="loginForm"
              :rules="loginRules"
              label-width="0"
              class="login-form"
            >
              <el-form-item prop="username">
                <el-input
                  v-model="loginForm.username"
                  placeholder="请输入用户名"
                  :prefix-icon="User"
                  size="large"
                />
              </el-form-item>
              
              <el-form-item prop="password">
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="请输入密码"
                  :prefix-icon="Lock"
                  size="large"
                  show-password
                  @keyup.enter="handleLogin"
                />
              </el-form-item>
              
              <el-form-item prop="remember">
                <el-checkbox v-model="loginForm.remember">
                  记住我
                </el-checkbox>
              </el-form-item>
              
              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  style="width: 100%"
                  @click="handleLogin"
                  :loading="loading"
                >
                  登录
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
          
          <el-tab-pane label="注册" name="register">
            <el-form
              ref="registerFormRef"
              :model="registerForm"
              :rules="registerRules"
              label-width="0"
              class="login-form"
            >
              <el-form-item prop="username">
                <el-input
                  v-model="registerForm.username"
                  placeholder="用户名"
                  :prefix-icon="User"
                  size="large"
                />
              </el-form-item>
              
              <el-form-item prop="email">
                <el-input
                  v-model="registerForm.email"
                  placeholder="邮箱"
                  :prefix-icon="Message"
                  size="large"
                />
              </el-form-item>
              
              <el-form-item prop="password">
                <el-input
                  v-model="registerForm.password"
                  type="password"
                  placeholder="密码"
                  :prefix-icon="Lock"
                  size="large"
                  show-password
                />
              </el-form-item>
              
              <el-form-item prop="confirmPassword">
                <el-input
                  v-model="registerForm.confirmPassword"
                  type="password"
                  placeholder="确认密码"
                  :prefix-icon="Lock"
                  size="large"
                  show-password
                  @keyup.enter="handleRegister"
                />
              </el-form-item>
              
              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  style="width: 100%"
                  @click="handleRegister"
                  :loading="loading"
                >
                  注册
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, Message, Monitor, Connection } from '@element-plus/icons-vue'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { authApi } from '@/services/api/auth'

const router = useRouter()

const activeTab = ref('login')
const loading = ref(false)
const loginFormRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()

const loginForm = reactive({
  username: '',
  password: '',
  remember: false
})

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名长度不能少于3位', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      const response = await authApi.login({
        username: loginForm.username,
        password: loginForm.password
      })
      
      // 如果请求成功（没有抛出异常），说明登录成功
      if (response.token) {
        localStorage.setItem('token', response.token)
        localStorage.setItem('userId', response.userId?.toString() || '')
        ElMessage.success(response.message || '登录成功')
        router.push('/chat')
      } else {
        ElMessage.error(response.message || '登录失败')
      }
    } catch (error: any) {
      // 错误已经在request.ts的拦截器中处理，这里只显示具体错误信息
      const errorMessage = error.response?.data?.message || error.message || '登录失败'
      ElMessage.error(errorMessage)
    } finally {
      loading.value = false
    }
  })
}

const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  await registerFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      const response = await authApi.register({
        username: registerForm.username,
        email: registerForm.email,
        password: registerForm.password
      })
      
      // 如果请求成功（没有抛出异常），说明注册成功
      if (response.token || response.message) {
        ElMessage.success(response.message || '注册成功，请登录')
        activeTab.value = 'login'
        loginForm.username = registerForm.username
      } else {
        ElMessage.error(response.message || '注册失败')
      }
    } catch (error: any) {
      // 错误已经在request.ts的拦截器中处理，这里只显示具体错误信息
      const errorMessage = error.response?.data?.message || error.message || '注册失败'
      ElMessage.error(errorMessage)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped lang="scss">
/* 登录页面 - 扁平化、艺术感设计 */
.login-view {
  width: 100vw;
  height: 100vh;
  background: var(--bg-color-page);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  position: relative;
}

/* 背景装饰 - 极简几何图形 */
.login-view::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 30%, var(--primary-fade) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(16, 185, 129, 0.05) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

.login-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  max-width: 1200px;
  width: 100%;
  gap: var(--spacing-2xl);
  align-items: center;
  position: relative;
  z-index: 1;
}

/* 左侧：宣传卡片 - 扁平化设计 */
.promo-card {
  background: var(--bg-color);
  border: 1px solid var(--border-color-base);
  border-radius: var(--border-radius-large);
  padding: var(--spacing-2xl);
  min-height: 600px;
  display: flex;
  align-items: center;
  position: relative;
  overflow: hidden;
}

/* 左侧卡片装饰 - 极简线条 */
.promo-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--primary-color) 0%, var(--success-color) 100%);
  opacity: 0.6;
}

.promo-content {
  width: 100%;
  position: relative;
  z-index: 1;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-2xl);
}

.logo-icon {
  width: 56px;
  height: 56px;
  background: var(--primary-fade);
  border: 1px solid var(--border-color-base);
  border-radius: var(--border-radius-base);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 700;
  color: var(--primary-color);
  font-family: var(--font-family-artistic);
  letter-spacing: -0.02em;
}

.logo-text {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-color-primary);
  font-family: var(--font-family-artistic);
  letter-spacing: -0.02em;
}

.promo-title-wrapper {
  margin-bottom: var(--spacing-2xl);
}

.promo-title {
  font-size: 40px;
  font-weight: 700;
  line-height: 1.3;
  margin-bottom: var(--spacing-md);
  color: var(--text-color-primary);
  letter-spacing: -0.02em;
  font-family: var(--font-family-base);
}

.promo-subtitle {
  font-size: var(--font-size-lg);
  font-weight: 400;
  line-height: 1.6;
  color: var(--text-color-secondary);
  letter-spacing: 0.01em;
}

.promo-image {
  margin: var(--spacing-2xl) 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

.digital-human-placeholder {
  width: 240px;
  height: 240px;
  background: var(--bg-color-secondary);
  border: 1px solid var(--border-color-base);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-color-secondary);
  transition: var(--transition-base);
}

.digital-human-placeholder:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.promo-features {
  display: flex;
  gap: var(--spacing-xl);
  margin-top: var(--spacing-2xl);
  flex-wrap: wrap;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  color: var(--text-color-secondary);
  font-size: var(--font-size-base);
  transition: var(--transition-base);
  
  .el-icon {
    font-size: 20px;
    transition: var(--transition-base);
  }
  
  span {
    font-weight: 500;
    letter-spacing: 0.01em;
  }
  
  &:hover {
    color: var(--primary-color);
    
    .el-icon {
      color: var(--primary-color);
    }
  }
}

/* 右侧：登录表单卡片 - 极简设计 */
.login-form-card {
  background: var(--bg-color);
  border: 1px solid var(--border-color-base);
  border-radius: var(--border-radius-large);
  padding: var(--spacing-2xl);
  min-height: 600px;
  box-shadow: var(--box-shadow-base);
}

.login-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: var(--spacing-2xl);
    border-bottom: 1px solid var(--border-color-light);
  }
  
  :deep(.el-tabs__nav-wrap::after) {
    display: none;
  }
  
  :deep(.el-tabs__item) {
    font-size: var(--font-size-lg);
    font-weight: 600;
    color: var(--text-color-secondary);
    padding: 0 var(--spacing-lg);
    margin-right: var(--spacing-xl);
    border-bottom: 2px solid transparent;
    transition: var(--transition-base);
    letter-spacing: 0.01em;
  }
  
  :deep(.el-tabs__item:hover) {
    color: var(--primary-color);
  }
  
  :deep(.el-tabs__item.is-active) {
    color: var(--primary-color);
    border-bottom-color: var(--primary-color);
  }
  
  :deep(.el-tabs__active-bar) {
    background-color: var(--primary-color);
    height: 2px;
  }
}

.login-form {
  .el-form-item {
    margin-bottom: var(--spacing-lg);
  }
  
  .el-form-item:last-child {
    margin-bottom: 0;
  }
  
  .el-input {
    height: 52px;
    font-size: var(--font-size-base);
  }
  
  .el-button {
    height: 52px;
    font-size: var(--font-size-md);
    font-weight: 600;
    letter-spacing: 0.02em;
    border-radius: var(--border-radius-base);
  }
  
  .el-checkbox {
    color: var(--text-color-regular);
    font-size: var(--font-size-base);
  }
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .login-layout {
    gap: var(--spacing-xl);
  }
  
  .promo-card,
  .login-form-card {
    padding: var(--spacing-xl);
    min-height: auto;
  }
  
  .promo-title {
    font-size: 32px;
  }
  
  .promo-subtitle {
    font-size: var(--font-size-base);
  }
  
  .digital-human-placeholder {
    width: 180px;
    height: 180px;
  }
}

@media (max-width: 768px) {
  .login-view {
    padding: var(--spacing-md);
  }
  
  .login-layout {
    grid-template-columns: 1fr;
    gap: var(--spacing-lg);
  }
  
  .promo-card {
    display: none;
  }
  
  .login-form-card {
    min-height: auto;
    padding: var(--spacing-lg);
  }
}
</style>
