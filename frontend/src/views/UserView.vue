<template>
  <div class="user-view">
    <el-card class="user-card">
      <template #header>
        <div class="card-header">
          <h3>用户中心</h3>
        </div>
      </template>
      
      <el-tabs v-model="activeTab">
        <el-tab-pane label="个人信息" name="profile">
          <el-form :model="userInfo" label-width="100px">
            <el-form-item label="用户名">
              <el-input v-model="userInfo.username" disabled />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="userInfo.email" />
            </el-form-item>
            <el-form-item label="头像">
              <el-upload
                class="avatar-uploader"
                action="/api/upload/avatar"
                :show-file-list="false"
              >
                <el-avatar :src="userInfo.avatar" :size="100">
                  <el-icon><User /></el-icon>
                </el-avatar>
              </el-upload>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="updateProfile">保存</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="账户设置" name="account">
          <el-form :model="accountForm" label-width="100px">
            <el-form-item label="当前密码">
              <el-input v-model="accountForm.currentPassword" type="password" />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input v-model="accountForm.newPassword" type="password" />
            </el-form-item>
            <el-form-item label="确认密码">
              <el-input v-model="accountForm.confirmPassword" type="password" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="changePassword">修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const activeTab = ref('profile')

const userInfo = ref({
  username: 'user',
  email: 'user@example.com',
  avatar: ''
})

const accountForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const updateProfile = () => {
  ElMessage.success('个人信息已更新')
}

const changePassword = () => {
  ElMessage.success('密码已修改')
}
</script>

<style scoped lang="scss">
.user-view {
  padding: var(--spacing-xl);
  max-width: 900px;
  margin: 0 auto;
  background: var(--bg-color-page);
  min-height: calc(100vh - 64px);
}

.user-card {
  min-height: 500px;
  border: 1px solid var(--border-color-base);
  box-shadow: var(--box-shadow-base);
}

.card-header {
  h3 {
    margin: 0;
    font-size: var(--font-size-xl);
    font-weight: 700;
    color: var(--text-color-primary);
    letter-spacing: -0.01em;
  }
}

.avatar-uploader {
  :deep(.el-upload) {
    cursor: pointer;
    transition: var(--transition-base);
    
    &:hover {
      opacity: 0.8;
    }
  }
}

:deep(.el-tabs__header) {
  border-bottom: 1px solid var(--border-color-light);
}

:deep(.el-tabs__item) {
  font-weight: 500;
  color: var(--text-color-secondary);
  
  &.is-active {
    color: var(--primary-color);
    font-weight: 600;
  }
}

:deep(.el-form-item__label) {
  color: var(--text-color-regular);
  font-weight: 500;
}
</style>


